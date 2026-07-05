import json
import asyncio
import structlog
from typing import Dict, Any, List, Optional
from ai_platform.providers.llm_provider import get_llm_provider, GenerationConfig

logger = structlog.get_logger("visoora_generation_service")

class GenerationService:
    def __init__(self, provider_name: str = "claude"):
        self.provider = get_llm_provider(provider_name)

    async def draft_prospecting_email(self, business_brain, target_company, research_data, hint=None):
        hint_instruction = f"\n\nReviewer instruction: {hint}" if hint else ""
        system_prompt = '''You are an elite B2B SDR. Write a short cold outreach email (under 100 words).
Output JSON with exactly these keys:
- "email_subject": Punchy subject, max 8 words, no ALL CAPS
- "email_body": Email body with \n for line breaks. Sign off with first name only.
- "pain_points_addressed": Array of 1-3 likely pains
- "reason_selected": 1 sentence on why good fit
- "expected_reply_rate": string like "14%"
- "expected_meeting_prob": string like "5%"
- "personalization_score": int 0-100
- "business_brain_match": int 0-100
- "spam_risk": "Low", "Medium", or "High"'''
        user_prompt = f"""Business Brain:
{business_brain.get('company_description')}
Value Prop: {business_brain.get('value_proposition')}
Tone: {business_brain.get('brand_voice_tone')}

Prospect: {target_company.get('first_name')} {target_company.get('last_name')}, {target_company.get('title')} at {target_company.get('company')}

Research: {research_data}{hint_instruction}"""
        config = GenerationConfig(temperature=0.7, max_tokens=700)
        result = await self.provider.generate_json(system_prompt, user_prompt, config)
        logger.info("email_drafted", company=target_company.get('company'))
        return result

    async def generate_email_alternatives(self, business_brain, target_company, research_data):
        tone_configs = [
            {"label": "Professional", "icon": "briefcase", "tone_desc": "Formal, data-driven, no contractions, sign off with full name and title."},
            {"label": "Friendly", "icon": "smile", "tone_desc": "Warm, conversational, like a peer. Use first names. Light humor ok."},
            {"label": "Very Short", "icon": "zap", "tone_desc": "Max 3 sentences total. No pleasantries. Straight to the point."},
        ]
        async def generate_one(t):
            system_prompt = f"You are a B2B SDR. Write a cold email in this tone: {t['tone_desc']}.\nOutput JSON: {{\"email_subject\": \"...\", \"email_body\": \"...\"}}"
            user_prompt = f"Company: {business_brain.get('company_description')}\nValue: {business_brain.get('value_proposition')}\nProspect: {target_company.get('first_name')} {target_company.get('last_name')}, {target_company.get('title')} at {target_company.get('company')}\nResearch: {research_data}"
            try:
                config = GenerationConfig(temperature=0.75, max_tokens=400)
                result = await self.provider.generate_json(system_prompt, user_prompt, config)
                return {"label": t["label"], "icon": t["icon"], "email_subject": result.get("email_subject",""), "email_body": result.get("email_body","")}
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
