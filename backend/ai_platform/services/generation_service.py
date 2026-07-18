import json
import asyncio
import structlog
from typing import Dict, Any, List, Optional
from ai_platform.providers.llm_provider import get_llm_provider, GenerationConfig
from server.ai_gateway import gateway

logger = structlog.get_logger("visoora_generation_service")

class ContextBuilder:
    @staticmethod
    def build_prompt_context(business_brain: dict, knowledge: dict) -> dict:
        context = {
            "business_facts": {
                "company_description": business_brain.get("company_description"),
                "value_proposition": business_brain.get("value_proposition"),
            },
            "prospect_facts": {}
        }
        
        # Only include high-confidence, verified facts
        for category, fields in knowledge.items():
            if isinstance(fields, list):
                valid_fields = [f for f in fields if f.get("verified") and str(f.get("value")).lower() != "unknown"]
                if valid_fields:
                    context["prospect_facts"][category] = valid_fields
        return context

class EmailValidator:
    @staticmethod
    def validate_draft(draft, prompt_context: dict):
        """
        Ensures all citations in the draft actually exist in the prompt context.
        Strips invalid citations.
        """
        valid_citations = []
        # flatten all snippets from prompt_context
        context_snippets = []
        for cat, fields in prompt_context.get("prospect_facts", {}).items():
            for f in fields:
                snippet = f.get("snippet", "").lower()
                if snippet and snippet != "n/a":
                    context_snippets.append(snippet)
                
        for cit in draft.citations:
            cit_snip = cit.snippet.lower()
            if any(cit_snip in cs or cs in cit_snip for cs in context_snippets):
                valid_citations.append(cit)
            else:
                logger.warn("hallucinated_citation_removed", snippet=cit.snippet)
                
        draft.citations = valid_citations
        return draft

class GenerationService:
    def __init__(self, provider_name: str = "claude"):
        self.provider = get_llm_provider(provider_name)

    async def draft_prospecting_email(self, business_brain, target_company, knowledge_data, hint=None):
        prompt_context = ContextBuilder.build_prompt_context(business_brain, knowledge_data)
        
        draft, meta = await gateway.draft_email(
            prompt_context=prompt_context,
            target_company=target_company,
            hint=hint
        )
        
        validated_draft = EmailValidator.validate_draft(draft, prompt_context)
        
        logger.info("email_drafted_via_gateway", company=target_company.get('company'))
        return {
            "draft": validated_draft.model_dump(),
            "meta": meta
        }

    async def generate_email_alternatives(self, target_company, citations):
        tone_configs = [
            {"label": "Professional", "icon": "briefcase", "tone_desc": "Formal, data-driven, no contractions, sign off with full name and title."},
            {"label": "Friendly", "icon": "smile", "tone_desc": "Warm, conversational, like a peer. Use first names. Light humor ok."},
            {"label": "Very Short", "icon": "zap", "tone_desc": "Max 3 sentences total. No pleasantries. Straight to the point."},
        ]
        
        prompt_context = {
            "prospect_facts": {
                "Verified Citations from Original Draft": citations
            }
        }
        
        async def generate_one(t):
            try:
                draft, _ = await gateway.draft_email(
                    prompt_context=prompt_context,
                    target_company=target_company,
                    hint=f"Use this tone: {t['tone_desc']}"
                )
                return {"label": t["label"], "icon": t["icon"], "email_subject": draft.subject, "email_body": draft.body}
            except Exception as e:
                logger.error("alternative_failed", tone=t["label"], error=str(e))
                return {"label": t["label"], "icon": t["icon"], "email_subject": "", "email_body": ""}
                
        results = await asyncio.gather(*[generate_one(t) for t in tone_configs])
        return list(results)

    async def analyze_website(self, url, html_content):
        system_prompt = 'Analyze website content. Output JSON: {"companyDescription":"...","valueProposition":"...","icpIndustries":["..."]}'
        user_prompt = f"URL: {url}\n\nContent:\n{html_content[:3000]}"
        config = GenerationConfig(temperature=0.3, max_tokens=500)
        return await self.provider.generate_json(system_prompt, user_prompt, config)

generation_service = GenerationService()
