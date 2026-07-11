import json
import os
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CallStateContext(BaseModel):
    current_state: str = "INITIATION"
    state_history: List[str] = Field(default_factory=list)
    lead_metadata: Dict[str, str] = Field(default_factory=dict)
    objection_count: int = 0
    objection_history: List[str] = Field(default_factory=list)
    prospect_name: str = "Valued Customer"
    company_name: str = "Global Corp"
    is_terminal: bool = False
    rag_context: Optional[str] = None  # Pre-call memory brief from MemoryManager
    conversation_plan: Optional[Dict] = None # Phase 4 dynamic plan injection

def get_tenant_config(tenant_id: str) -> dict:
    from server.storage_manager import supabase_admin_client as supabase_client
    
    # 1. Resolve UUID
    try:
        uuid_str = str(uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)) if tenant_id != "default_shared_tenant" else "1a646c07-6c22-50d4-a745-98db0e071728"
    except Exception:
        uuid_str = tenant_id

    # 2. Try Supabase
    if supabase_client:
        try:
            res = supabase_client.table("agent_configs").select("*").eq("tenant_id", uuid_str).execute()
            if res.data:
                row = res.data[0]
                persona_json = row.get("persona", "{}")
                try:
                    persona_data = json.loads(persona_json)
                except Exception:
                    persona_data = {}
                return {
                    "company_description": row.get("company_description") or "",
                    "value_proposition": row.get("value_proposition") or "",
                    "icp_industries": row.get("icp_industries") or [],
                    "icp_company_sizes": row.get("icp_company_sizes") or [],
                    "icp_regions": row.get("icp_regions") or [],
                    "decision_maker_titles": row.get("decision_maker_titles") or [],
                    "avoid_list": row.get("avoid_list") or [],
                    "competitors": row.get("competitors") or [],
                    "objections_list": row.get("objections_list") or [],
                    "brand_voice_tone": row.get("brand_voice_tone") or "",
                    **persona_data
                }
        except Exception as e:
            print(f"[States Config] Supabase query failed: {e}")

    # 3. Fallback to local file
    PROGRESS_FILE = "recordings/local_onboarding_progress.json"
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                registry = json.load(f)
            if tenant_id in registry:
                progress_data = registry[tenant_id]
                s1 = progress_data.get("step1") or {}
                s3 = progress_data.get("step3") or {}
                s5 = progress_data.get("step5") or {}
                return {
                    "company_name": s1.get("companyName") or "",
                    "website": s1.get("website") or "",
                    "industry": s1.get("industry") or "",
                    "team_size": s1.get("teamSize") or "",
                    "annual_revenue": s1.get("annualRevenue") or "",
                    "target_region": s1.get("targetRegion") or "",
                    "agent_name": s3.get("agentName") or "Alex",
                    "company_description": s3.get("companyDescription") or "",
                    "value_proposition": s3.get("valueProposition") or "",
                    "voice": s3.get("voice") or "rachel",
                    "tone": s3.get("tone") or "consultative",
                    "timezone": s3.get("timezone") or "America/New_York",
                    "calling_hours_start": s3.get("callingHoursStart") or "08:00",
                    "calling_hours_end": s3.get("callingHoursEnd") or "17:00",
                    "product_name": s3.get("productName") or "",
                    "product_price": s3.get("productPrice") or "",
                    "product_features": s3.get("productFeatures") or "",
                    "target_audience": s3.get("targetAudience") or "",
                    "kb_description": s3.get("kbDescription") or "",
                    "kb_faqs": s3.get("kbFaqs") or [],
                    "objections_list": s3.get("objectionsList") or [],
                    "icp_industries": s3.get("icpIndustries") or [],
                    "icp_company_sizes": s3.get("icpCompanySizes") or [],
                    "icp_regions": s3.get("icpRegions") or [],
                    "decision_maker_titles": s3.get("decisionMakerTitles") or [],
                    "avoid_list": s3.get("avoidList") or [],
                    "competitors": s3.get("competitors") or [],
                    "brand_voice_tone": s3.get("brandVoiceTone") or "",
                    "campaign_goal": s5.get("campaignGoal") or "",
                    "playbook_greeting": s5.get("playbookGreeting") or "",
                    "playbook_booking_link": s5.get("playbookBookingLink") or "",
                }
        except Exception as e:
            print(f"[States Config] Local config load failed: {e}")

    return {}

class StateMachineController:
    # State transitions map specifying allowed target states for every source state
    TRANSITIONS: Dict[str, List[str]] = {
        "INITIATION": ["DISCOVERY", "PITCH", "OBJECTION", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "DISCOVERY": ["PITCH", "OBJECTION", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "PITCH": ["QUALIFICATION", "OBJECTION", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "QUALIFICATION": ["BOOKING", "OBJECTION", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "BOOKING": ["SUCCESS_COMPLETE", "OBJECTION", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "OBJECTION": ["DISCOVERY", "PITCH", "QUALIFICATION", "BOOKING", "TRANSFER_TO_HUMAN", "END_CALL_DISCONNECT"],
        "TRANSFER_TO_HUMAN": [],
        "END_CALL_DISCONNECT": [],
        "SUCCESS_COMPLETE": []
    }

    def __init__(self, initial_metadata: dict, tenant_id: str = "default_shared_tenant"):
        # Extract prospect details robustly
        prospect_name = initial_metadata.get("name") or initial_metadata.get("prospect_name") or "Valued Customer"
        company_name = initial_metadata.get("company") or initial_metadata.get("company_name") or "Global Corp"
        
        self.tenant_id = tenant_id
        self.config = get_tenant_config(tenant_id)
        agent_id = initial_metadata.get("agent_id")
        if agent_id:
            try:
                from sales_employee.services import knowledge_service

                shared_context = knowledge_service.build_persona_context(
                    tenant_id,
                    agent_id,
                    f"{prospect_name} {company_name}",
                )
                self.config.update(shared_context.get("persona_config") or {})
                self.config["sales_employee_knowledge_context"] = shared_context.get("knowledge_context", "")
            except Exception as exc:
                print(f"[States Config] Sales employee context load failed: {exc}")
        
        # Inject Phase 4 Conversation Plan
        conversation_plan = initial_metadata.get("conversation_plan")
        if conversation_plan:
            self.config["conversation_plan"] = conversation_plan
            # Override playbook details with dynamic plan
            if "opening" in conversation_plan:
                self.config["playbook_greeting"] = conversation_plan["opening"]
        
        self.context = CallStateContext(
            lead_metadata=initial_metadata,
            prospect_name=prospect_name,
            company_name=company_name,
            conversation_plan=conversation_plan
        )
        
    def validate_and_transition(self, next_state: str) -> bool:
        """
        Evaluates current state against allowable transitions. 
        Appends to history, handles objection counters, updates is_terminal flag, and logs output.
        """
        current = self.context.current_state
        
        # If already in a terminal state, no further transitions are allowed
        if current in ["END_CALL_DISCONNECT", "SUCCESS_COMPLETE", "TRANSFER_TO_HUMAN"]:
            return False

        # Validate transition target
        allowed_transitions = self.TRANSITIONS.get(current, [])
        if next_state not in allowed_transitions:
            return False

        # Perform transition
        self.context.state_history.append(current)
        self.context.current_state = next_state

        # Update objection counts if transition to OBJECTION
        if next_state == "OBJECTION":
            self.context.objection_count += 1

        # Check for terminal status
        if next_state in ["END_CALL_DISCONNECT", "SUCCESS_COMPLETE", "TRANSFER_TO_HUMAN"]:
            self.context.is_terminal = True

        return True

    def inject_rag_context(self, brief: str):
        """
        Injects the pre-call memory brief produced by MemoryManager.load_pre_call_context()
        into the FSM context, so it gets woven into the next prompt compilation.
        Should be called once during call setup, before the first AI turn.
        """
        if brief:
            self.context.rag_context = brief

    def compile_expert_system_prompt(self) -> str:
        """
        Compiles and returns the full dynamic Expert System Prompt featuring live token injections.
        """
        history_str = ", ".join(f"'{obj}'" for obj in self.context.objection_history) if self.context.objection_history else "None"
        
        agent_name = self.config.get("agent_name") or "Alex"
        agent_company = self.config.get("company_name") or "Visoora"
        tone = self.config.get("tone") or "consultative"
        
        prompt = f"""You are {agent_name}, a senior sales consultant at {agent_company}. You are on a live telephone call. You are human — never reveal or imply you are an AI under any circumstances.
Your tone is {tone}.

BUSINESS & PRODUCT CONTEXT:"""
        
        if self.config.get("company_description"):
            prompt += f"\n- Company Description: {self.config.get('company_description')}"
        if self.config.get("value_proposition"):
            prompt += f"\n- Value Proposition: {self.config.get('value_proposition')}"
        if self.config.get("product_name"):
            prompt += f"\n- Product: {self.config.get('product_name')} (Pricing: {self.config.get('product_price')})"
            prompt += f"\n- Product Features: {self.config.get('product_features')}"
            prompt += f"\n- Target Audience: {self.config.get('target_audience')}"
            
        if self.config.get("kb_faqs"):
            prompt += "\n\nKNOWLEDGE BASE FAQs (Use these facts to answer questions):"
            for faq in self.config["kb_faqs"]:
                q = faq.get("question", faq.get("q", ""))
                a = faq.get("answer", faq.get("a", ""))
                if q and a:
                    prompt += f"\nQ: {q}\nA: {a}"
                    
        if self.config.get("objections_list"):
            prompt += "\n\nOBJECTION HANDLING PLAYBOOK (Use these specific rebuttals if the prospect raises these objections):"
            for obj_item in self.config["objections_list"]:
                obj_trigger = obj_item.get("objection", obj_item.get("trigger", ""))
                rebuttal = obj_item.get("rebuttal", "")
                if obj_trigger and rebuttal:
                    prompt += f"\n- If prospect objects '{obj_trigger}', respond with: '{rebuttal}'"

        campaign_goal = self.config.get("campaign_goal") or "Book Demo Meeting"
        playbook_booking_link = self.config.get("playbook_booking_link") or ""
        playbook_greeting = self.config.get("playbook_greeting") or ""

        prompt += f"""

CAMPAIGN GOAL: {campaign_goal}
"""
        if playbook_booking_link:
            prompt += f"Use this booking link when scheduling: {playbook_booking_link}\n"

        prompt += f"""
VOICE RULES (critical — TTS reads this aloud):
- Never use markdown, asterisks, bullet points, headers, or numbered lists. Plain speech only.
- Maximum two sentences per turn. Short sentences. Vary length naturally.
- Begin each turn with a brief acknowledgment filler: "Right.", "Got it.", "Sure.", "Absolutely.", "Of course." — vary them, never repeat the same one twice in a row.
- Use natural contractions: "I'll", "we've", "that's", "you're". Never formal constructs.
- Insert occasional brief pauses through comma placement. Never rush.

PERSONA BY CALL STATE:"""

        if playbook_greeting:
            prompt += f"\n- INITIATION: Open the call exactly with this playbook script: \"{playbook_greeting}\" (Wait for prospect response)."
        else:
            prompt += f"\n- INITIATION: Warm, unhurried, slightly casual. You are calling on behalf of someone they may have engaged with before."

        prompt += f"""
- DISCOVERY: Curious, conversational. Ask open-ended questions about their current tools, workflow pain points, and challenges. Do not pitch features yet.
- PITCH: Confident and focused. One crisp value statement linked to their needs, then ask a qualifying question. Never list features.
- OBJECTION: Slow down. Empathetic, never defensive. Validate their concern in your own words before pivoting. If this prospect has raised {self.context.objection_count} objections already, acknowledge the pattern: "I hear you — sounds like you've got a few concerns, let's go through them."
- QUALIFICATION: Curious, conversational. Ask one question at a time to confirm budget scope, timeline, and decision-making roles. Never interrogate.
- BOOKING: Helpful and concrete. Offer two specific time slots. Make it easy to say yes.
- COMPLETE: Warm closing. Repeat the confirmed time once. Short, genuine goodbye.

HUMAN FALLIBILITY (makes you sound real):
- Occasionally use: "Let me think about that for a second.", "That's a fair question.", "Actually — good point."
- If you don't know something: "I'll have to check that and get back to you."
- Never be perfectly smooth. A tiny moment of natural hesitation reads as human.

HARD RULES:
- Never argue. Never pressure. Never repeat the same pitch twice verbatim.
- If prospect says "not interested" twice: acknowledge graciously and close the call.
- If silence exceeds 4 seconds: re-engage with "Are you still there?" once. If no response, close politely.
- Never say: "As an AI", "I'm a bot", "I'm calling from an automated system", "I was programmed to".
- Current call state: {self.context.current_state}. Objections raised so far: [{history_str}]. Prospect name: {self.context.prospect_name}. Company name: {self.context.company_name}."""
        
        # ── RAG: Inject prior-call memory brief ──
        if self.context.rag_context:
            prompt += f"""

[PRIOR CALL HISTORY — Use this to personalize the conversation. Do not repeat it verbatim. Reference it naturally when relevant]:
{self.context.rag_context}"""

        if self.config.get("sales_employee_knowledge_context"):
            prompt += f"""

[AGENT SALES BRAIN — Shared knowledge for calls and emails. Use these facts naturally when relevant]:
{self.config.get("sales_employee_knowledge_context")}"""
        
        return prompt


    def generate_state_prompt_modifier(self) -> str:
        """
        Returns hard, explicit text directives based on the active state 
        to be appended directly into the agent prompt layer.
        """
        state = self.context.current_state
        
        directives = {
            "INITIATION": (
                "CRITICAL: Warm, unhurried, slightly casual. Verify you're speaking to the correct "
                "owner or decision maker. You're calling on behalf of someone they may have engaged with before. "
                "Do not start pitching or sharing product details yet."
            ),
            "DISCOVERY": (
                "CRITICAL: Warm and curious. Ask open-ended questions to discover their current pain points, "
                "objectives, and daily tools. Keep it conversational. Do not rush to pitch yet."
            ),
            "PITCH": (
                "CRITICAL: Confident and focused. Deliver one crisp value statement specifically answering their "
                "stated pain points, then ask a qualifying question. Never list features."
            ),
            "OBJECTION": (
                f"CRITICAL: Slow down. Empathetic, never defensive. Validate their concern in your own words "
                f"before pivoting. Objection count: {self.context.objection_count}. "
                + (
                    "Since the prospect has raised multiple objections, acknowledge the pattern: "
                    "'I hear you — sounds like you've got a few concerns, let's go through them.' "
                    if self.context.objection_count >= 2 else ""
                )
                + "Pivot smoothly back to the active conversational phase (Discovery, Pitch, Qualification, or Booking)."
            ),
            "QUALIFICATION": (
                "CRITICAL: Curious, conversational. Ask direct qualifying questions to confirm budget "
                "footprints, need, and authority. Ask one question at a time. Never interrogate."
            ),
            "BOOKING": (
                "CRITICAL: Helpful and concrete. Secure a firm date and time for a follow-up demonstration. "
                "Trigger the calendar availability checking tool immediately. Offer two specific time slots "
                "and make it easy to say yes."
            ),
            "END_CALL_DISCONNECT": (
                "CRITICAL: Politeness is key. Graciously wrap up the conversation, say goodbye, and terminate the session."
            ),
            "SUCCESS_COMPLETE": (
                "CRITICAL: Warm closing. Booking confirmed successfully. Repeat the confirmed time once, "
                "review next steps with a short, genuine goodbye, and conclude the conversation."
            ),
            "TRANSFER_TO_HUMAN": (
                "CRITICAL: You are handing this call to a human specialist. Say exactly: "
                "'Let me connect you with one of our team members who can help you best. Please hold for just a moment.' "
                "Then stop speaking. Do not continue the conversation."
            )
        }
        
        return directives.get(state, "CRITICAL: Maintain professional conversational flow.")
