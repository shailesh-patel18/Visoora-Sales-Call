from typing import Dict, Any, List, Optional
import structlog
from sales_employee.services import StrategyDecision, store, require_tenant_id, utc_now, history_service

logger = structlog.get_logger("visoora_followup_engine")

class AIFollowupEngine:
    def decide_next_action(
        self,
        lead: Dict[str, Any],
        history: List[Dict[str, Any]],
        agent_config: Dict[str, Any]
    ) -> StrategyDecision:
        """
        Observe: Analyze lead history, replies, call outcomes, and events.
        Reason & Decide: Return next step strategy details.
        """
        # 1. Unsubscribed / Stopped guard
        follow_up_status = lead.get("follow_up_status", "").lower()
        lead_status = lead.get("status", "").lower()
        if follow_up_status == "stopped" or lead_status == "unsubscribed" or follow_up_status == "unsubscribed":
            return StrategyDecision(
                action="wait",
                wait_hours=99999,
                reason="Prospect has unsubscribed; automated outreach is permanently disabled.",
                should_send=False
            )

        # 2. Stop-on-company-reply check
        company_name = lead.get("company_name", "")
        tenant_id = lead.get("tenant_id", "acme_tenant")
        if company_name:
            try:
                all_leads = store.list("leads", tenant_id)
            except Exception:
                all_leads = []
            company_leads = [l for l in all_leads if l.get("company_name", "").lower() == company_name.lower() and l.get("id") != lead.get("id")]
            for cl in company_leads:
                try:
                    cl_history = history_service.list_for_lead(tenant_id, cl["id"])
                except Exception:
                    cl_history = []
                replied = any(h.get("channel") == "email" and h.get("direction") == "inbound" for h in cl_history)
                if replied:
                    return StrategyDecision(
                        action="wait",
                        wait_hours=99999,
                        reason="Outreach stopped because another contact from the same company has replied.",
                        should_send=False
                    )

        # 3. Bounced Emails check
        bounced = any(h.get("status") == "bounced" for h in history)
        if bounced:
            return StrategyDecision(
                action="stop_lost",
                reason="Outbound email bounced; terminating automated follow-up.",
                should_send=False
            )
            
        # 4. Inbound Replies check
        replies = [h for h in history if h.get("channel") == "email" and h.get("direction") == "inbound"]
        if replies:
            # Check for booking sentiment/status
            meeting_booked = any(
                "meeting" in str(r.get("metadata", {})).lower() or 
                r.get("status") == "meeting_booked" 
                for r in replies
            )
            if meeting_booked:
                return StrategyDecision(
                    action="book_meeting",
                    reason="Lead booked a meeting; transitioning plan to completed.",
                    should_send=False
                )
            return StrategyDecision(
                action="escalate_to_human",
                reason="Lead replied to our outbound outreach; human routing required.",
                should_send=False
            )
            
        # 5. Call Outcome check (e.g. if demo was booked)
        calls = [h for h in history if h.get("channel") == "call"]
        if any(c.get("status") == "completed" and "demo_booked" in str(c.get("outcome", "")) for c in calls):
            return StrategyDecision(
                action="book_meeting",
                reason="Demo was booked during previous call outreach; terminating pipeline.",
                should_send=False
            )

        # 6. Human Approval / Lead Review check
        if lead.get("needs_review"):
            return StrategyDecision(
                action="escalate_to_human",
                reason="Lead research details require manual operator verification before sending.",
                should_send=False
            )
            
        # 7. Outbound Threshold limit check
        outbound_touches = [h for h in history if h.get("direction") == "outbound" and h.get("channel") in {"call", "email"}]
        if len(outbound_touches) >= 5:
            return StrategyDecision(
                action="stop_no_response",
                reason=f"Reached outbound limit of {len(outbound_touches)} touches without contact response.",
                should_send=False
            )
            
        # 8. State & Sequence checks
        last_touch = history[-1] if history else None
        if not last_touch:
            return StrategyDecision(
                action="send_email",
                reason="No prior outreach attempts found; initiating outreach sequence with custom research email.",
                should_send=True
            )
            
        # Previous action was email send
        if last_touch.get("channel") == "email" and last_touch.get("status") in {"sent", "delivered", "opened"}:
            opened = any(h.get("status") == "opened" for h in history)
            if opened:
                # High intent: attempt call
                return StrategyDecision(
                    action="call",
                    reason="Email opened by prospect. Proceeding with outbound voice call attempt.",
                    should_send=False
                )
            else:
                # Wait period
                return StrategyDecision(
                    action="wait",
                    wait_hours=72,
                    reason="Previous email delivered but not yet opened; waiting 72 hours for engagement.",
                    should_send=False
                )
                
        # Previous action was a call attempt that didn't connect
        if last_touch.get("channel") == "call" and last_touch.get("status") in {"no-answer", "voicemail"}:
            return StrategyDecision(
                action="send_email",
                reason="Prior outbound call attempt was unanswered; sending a thread-connected email referencing the attempt.",
                should_send=True
            )
            
        return StrategyDecision(
            action="wait",
            wait_hours=24,
            reason="Outreach sequence active; checking for updates in 24 hours.",
            should_send=False
        )

    def log_reasoning(self, tenant_id: str, lead_id: str, input_context: Dict[str, Any], decision: StrategyDecision) -> Dict[str, Any]:
        """Logs explainable reasoning logs into the database reasoning_logs table."""
        require_tenant_id(tenant_id)
        log_entry = {
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "input_context": input_context,
            "decision": decision.model_dump(),
            "created_at": utc_now()
        }
        return store.insert("reasoning_logs", log_entry)

ai_followup_engine = AIFollowupEngine()
