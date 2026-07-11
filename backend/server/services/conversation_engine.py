import structlog
import uuid
import datetime
from typing import Dict, Any, Optional
from server.storage_manager import supabase_admin_client as supabase_client
from server.services.mission_engine import emit_mission_event

logger = structlog.get_logger("conversation_engine")

class ConversationEngine:
    """
    Abstracts communication providers (Twilio, Retell, WebRTC).
    Receives a conversation plan and orchestrates the live call.
    """
    
    @staticmethod
    async def execute_conversation(task_id: str, prospect_metadata: Dict[str, str], conversation_plan: Dict[str, Any], user: Any) -> Dict[str, Any]:
        """
        Routes the conversation execution to the appropriate provider (e.g., Twilio).
        """
        logger.info("execute_conversation_start", task_id=task_id, prospect=prospect_metadata.get("phone"))
        
        # In the future, evaluate tenant preferences to select provider
        provider = "twilio"
        
        # Sprint 3: Compliance & Retry Policy Foundations
        from compliance.gate import verify_compliance_gate
        compliance_check = await verify_compliance_gate(prospect_metadata.get("phone"), user.tenant_id, None)
        if not compliance_check.get("allowed", True):
            logger.warn("compliance_gate_failed", task_id=task_id, reason=compliance_check.get("reason"))
            return {"success": False, "error": "Compliance check failed."}
            
        # Stub: Load Tenant Retry Policy (e.g. Leave Voicemail -> Email -> 3 Days)
        retry_policy = {
            "voicemail": ["leave_ai_voicemail", "send_followup_email", "retry_3_days"],
            "no_answer": ["retry_tomorrow_morning"],
            "busy": ["retry_2_hours"]
        }
        
        if provider == "twilio":
            return await ConversationEngine._trigger_twilio(task_id, prospect_metadata, conversation_plan, user, retry_policy)
        else:
            raise NotImplementedError(f"Provider {provider} not supported.")
            
    @staticmethod
    async def _trigger_twilio(task_id: str, prospect_metadata: Dict[str, str], conversation_plan: Dict[str, Any], user: Any, retry_policy: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Triggers a Twilio outbound call, passing the task_id and conversation_plan.
        """
        from server.twilio_handler import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, _public_base_url_from_request
        import httpx
        from urllib.parse import urlencode
        from utils.retry import retry_async

        prospect_phone = prospect_metadata.get("phone")
        if not prospect_phone:
            return {"success": False, "error": "Phone number is required."}

        tenant_id = user.tenant_id
        call_id = f"stm_{str(uuid.uuid4())[:8]}"
        
        # We store the conversation plan in Supabase linked to the call_id so the webhook can retrieve it,
        # or pass a reference. Since webhook URLs have length limits, we store it in a temporary lookup table or cache.
        if supabase_client:
            supabase_client.table("call_contexts").insert({
                "call_id": call_id,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "conversation_plan": conversation_plan,
                "created_at": datetime.datetime.utcnow().isoformat()
            }).execute()

        log_data = {"tenant_id": tenant_id, "call_id": call_id, "task_id": task_id}
        logger.info("trigger_outbound_twilio", **log_data)
        
        # Emit Mission Event
        mission_id = prospect_metadata.get("mission_id")
        if mission_id:
            emit_mission_event(mission_id, "call_dialing", task_id, {"call_id": call_id, "provider": "twilio"})

        if TWILIO_ACCOUNT_SID == "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" or TWILIO_AUTH_TOKEN == "your_twilio_auth_token_here":
            logger.warn("trigger_outbound_call_mock", event_message="Mocking outbound call trigger (Twilio credentials not configured).")
            return {"success": True, "call_sid": f"CAmocked_{call_id}", "call_id": call_id}

        api_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        public_base_url = _public_base_url_from_request()
        query_params = {
            "phone": prospect_phone,
            "name": prospect_metadata.get("name", "Prospect"),
            "company": prospect_metadata.get("company", "Acme"),
            "tenant_id": tenant_id,
            "call_id": call_id,
            "task_id": task_id
        }
        webhook_url = f"{public_base_url}/incoming-call?{urlencode(query_params)}"
        
        status_query = urlencode({"task_id": task_id, "mission_id": prospect_metadata.get("mission_id", "")})
        status_callback_url = f"{public_base_url}/api/twilio-status-callback?{status_query}"
        
        data = {
            "To": prospect_phone,
            "From": TWILIO_PHONE_NUMBER,
            "Url": webhook_url,
            "StatusCallback": status_callback_url,
            "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
            "StatusCallbackMethod": "POST"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await retry_async(
                    lambda: client.post(api_url, data=data, auth=auth),
                    attempts=3,
                    retry_if=lambda res: res.status_code in {429, 500, 502, 503, 504},
                )
                res_json = response.json()
                if response.status_code == 201:
                    return {"success": True, "call_sid": res_json.get("sid"), "call_id": call_id}
                else:
                    return {"success": False, "error": res_json.get("message")}
            except Exception as e:
                return {"success": False, "error": str(e)}
