from typing import Dict, Any, List, Optional
from sales_employee.services import knowledge_service, EmailDraft

class AIEmailGenerator:
    def generate_followup(
        self,
        tenant_id: str,
        agent_id: str,
        lead: Dict[str, Any],
        history: List[Dict[str, Any]],
        original_subject: Optional[str] = None
    ) -> EmailDraft:
        """
        Generates a context-aware follow-up email, ensuring no repetition and proper threading.
        """
        # Fetch persona/RAG knowledge
        context = knowledge_service.build_persona_context(tenant_id, agent_id, lead.get("company_name", ""))
        persona = context.get("persona_config", {})
        brief = lead.get("research_brief") or {}
        hooks = brief.get("personalization_hooks") or [lead.get("company_name", "")]
        tone = persona.get("tone", "consultative")
        value_prop = persona.get("value_proposition") or persona.get("business_description") or "simplify follow-up workflows"
        agent_name = persona.get("agent_name", "Alex")
        
        # Analyze history
        outbound_emails = [h for h in history if h.get("channel") == "email" and h.get("direction") == "outbound"]
        prior_calls = [h for h in history if h.get("channel") == "call"]
        
        subject = original_subject or f"Idea for {lead.get('company_name')}"
        if outbound_emails and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
            
        opener = f"Hi {lead.get('name')},"
        
        # Decide content dynamically based on history to avoid duplication
        if not outbound_emails:
            # First outreach email
            if prior_calls:
                reference = "I tried calling you earlier today and wanted to drop a quick note here."
            else:
                reference = f"I was reading about {hooks[0]} and thought this might be relevant to your team."
                
            body = (
                f"{opener}\n\n"
                f"{reference} We help companies like yours with a {tone} approach focused on {value_prop}.\n\n"
                f"Specifically, we noticed potential areas of improvement around {', '.join(str(h) for h in hooks if h)[:160]}.\n\n"
                "Would it make sense to connect for a brief chat this week?\n\n"
                f"Best,\n{agent_name}"
            )
        elif len(outbound_emails) == 1:
            # First follow-up
            if prior_calls and prior_calls[-1].get("status") in ("no-answer", "voicemail"):
                reference = "I tried giving you a quick ring yesterday but missed you. I wanted to see if my previous email had made its way to your inbox."
            else:
                reference = "I wanted to follow up on my previous note regarding our outreach strategies."
                
            body = (
                f"{opener}\n\n"
                f"{reference}\n\n"
                f"I know you're busy, but I wanted to mention that we also specialize in resolving {brief.get('likely_pain_points', ['manual prospecting'])[0]}.\n\n"
                "Do you have 5 minutes for a quick intro call next Tuesday?\n\n"
                f"Best,\n{agent_name}"
            )
        else:
            # Subsequent follow-ups
            body = (
                f"{opener}\n\n"
                "I wanted to check back one last time to see if improving your pipeline flow was still a priority this quarter.\n\n"
                "If not, no worries at all. Feel free to reach out whenever the timing is better.\n\n"
                f"Thanks again,\n{agent_name}"
            )
            
        return EmailDraft(
            subject=subject,
            body=body,
            personalization_notes=[str(h) for h in hooks if h]
        )

ai_email_generator = AIEmailGenerator()
