import os
import json
import hashlib
import structlog
import datetime
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from urllib.parse import urlparse
import instructor
from openai import AsyncOpenAI
from security.config import settings
from ai_platform.providers.openrouter import OpenRouterProvider
from ai_platform.providers.openai_provider import OpenAIProvider

logger = structlog.get_logger("ai_gateway")

class EvidenceField(BaseModel):
    field: str = Field(..., description="The name of the field (e.g., 'Company Name', 'Industry').")
    value: str = Field(..., description="The extracted value. Use 'Unknown' if not found.")
    source_url: str = Field(..., description="The URL where this was found.")
    snippet: str = Field(..., description="The exact quote from the text. Use 'N/A' if Unknown.")
    confidence: int = Field(..., description="Confidence score from 0 to 100. 0 if Unknown.")
    verified: bool = Field(default=False)

class IdentityExtraction(BaseModel):
    fields: list[EvidenceField]

class ProductsExtraction(BaseModel):
    fields: list[EvidenceField]

class SocialProofExtraction(BaseModel):
    fields: list[EvidenceField]

class EmailCitation(BaseModel):
    field: str = Field(..., description="The name of the field from the Prompt Context.")
    snippet: str = Field(..., description="The exact quote from the Prompt Context.")
    source_url: str = Field(..., description="The URL where this was found.")

class GroundedEmailDraft(BaseModel):
    subject: str = Field(..., description="Punchy subject line, max 8 words, no ALL CAPS.")
    body: str = Field(..., description="The email body.")
    citations: list[EmailCitation] = Field(..., description="The exact citations from the Prompt Context used to personalize the email.")

class ICP(BaseModel):
    segment: str = Field(description="The target customer segment (e.g. SaaS Founders, Healthcare IT)")
    rationale: str = Field(description="Why this segment is a good fit based on the website")
    confidence: int = Field(description="0-100 confidence score")
    snippet: str = Field(description="Direct quote from the website proving this")
    source_url: str = Field(description="The source URL")

class ICPGenerationResponse(BaseModel):
    icps: List[ICP]


class AIGateway:
    def __init__(self):
        self.mock_level = os.getenv("MOCK_AI", "NONE").upper()
        
        provider_name = settings.llm_provider.lower()
        
        if provider_name == "openrouter":
            self.provider_cls = OpenRouterProvider
        elif provider_name == "openai":
            self.provider_cls = OpenAIProvider
        else:
            self.provider_cls = OpenRouterProvider
            
    def _get_provider(self, task_type: str):
        if task_type == "extraction":
            return self.provider_cls(model_name=settings.model_extraction)
        elif task_type == "reasoning":
            return self.provider_cls(model_name=settings.model_reasoning)
        elif task_type == "email":
            return self.provider_cls(model_name=settings.model_email)
        return self.provider_cls()
        
    def _log_cost(self, provider: str, model: str, latency_ms: float, tokens_in: int = 0, tokens_out: int = 0):
        logger.info(
            "ai_api_cost",
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out
        )

    async def _firecrawl_extract(self, url: str, prompt: str, schema: dict) -> dict:
        import httpx
        import os
        import json
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            raise ValueError("FIRECRAWL_API_KEY is not set.")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "url": url,
                    "formats": ["extract"],
                    "extract": {
                        "prompt": prompt,
                        "schema": schema
                    }
                }
            )
            if res.status_code != 200:
                raise Exception(f"Firecrawl API failed: {res.text}")
            
            data = res.json().get('data', {}).get('extract', {})
            return data

    async def extract_business_brain(self, url: str, structured_data: dict, source_url: str, force_refresh: bool = False) -> Any:
        import time
        start_time = time.time()
        
        prompt = (
            "You are an expert business analyst. Extract detailed business insights based on the provided website data.\n"
            "1. You must never invent information. Base everything ONLY on the provided JSON data.\n"
            "2. If you cannot find strong evidence in the text, set the value to 'Unable to verify', confidence to 0, and snippet to 'N/A'.\n"
            f"3. Set source_url to {source_url} for all valid snippets.\n\n"
            f"Website Data:\n{json.dumps(structured_data, indent=2)}"
        )
        
        try:
            from server.onboarding_api import AnalyzeDomainResponse
            provider = self._get_provider("extraction")
            data = await provider.generate_structured(prompt, AnalyzeDomainResponse)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider=provider.name, model=provider.model_name, latency_ms=latency)
            
            return data
        except Exception as e:
            logger.error("ai_gateway_extraction_failed", error=str(e), url=url)
            raise

    async def generate_icps_from_brain(self, business_brain_data: dict) -> Any:
        import time
        import json
        start_time = time.time()
        
        source_url = business_brain_data.get("metadata", {}).get("sourceURL") or business_brain_data.get("url")
        if not source_url:
            source_url = "https://example.com"
            
        prompt = (
            "You are an ICP extraction engine. Based on this company's data, extract Ideal Customer Profile (ICP) segments.\n"
            "1. You must never invent information.\n"
            "2. Every ICP MUST be backed by a direct quote (snippet) proving this ICP is viable.\n"
            f"3. Ensure the source_url is {source_url}.\n\n"
            f"Company Data:\n{json.dumps(business_brain_data, indent=2)}"
        )
        
        try:
            from server.onboarding_api import ICPGenerationResponse
            provider = self._get_provider("reasoning")
            data = await provider.generate_structured(prompt, ICPGenerationResponse)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider=provider.name, model=provider.model_name, latency_ms=latency)
            
            return data
            
        except Exception as e:
            logger.error("ai_gateway_icp_generation_failed", error=str(e))
            raise

    async def _run_extraction(self, prompt: str, data: dict, response_model: Any, source_url: str) -> Any:
        import time
        start_time = time.time()
        
        full_prompt = (
            "You are a strict, objective extraction engine.\n"
            "CORE PRINCIPLE: EVIDENCE BACKED.\n"
            "1. You must never invent information.\n"
            "2. Every extracted field MUST be backed by a direct quote (snippet).\n"
            f"3. Set source_url to {source_url}.\n\n"
            f"{prompt}\n\n"
            f"Data Context:\n{json.dumps(data, indent=2)}"
        )
        
        try:
            provider = self._get_provider("extraction")
            res_data = await provider.generate_structured(full_prompt, response_model)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider=provider.name, model=provider.model_name, latency_ms=latency)
            
            return res_data
        except Exception as e:
            logger.error("ai_gateway_knowledge_extraction_failed", error=str(e))
            raise

    async def extract_identity(self, structured_data: dict, source_url: str) -> Any:
        from server.onboarding_api import IdentityExtraction, EvidenceField
        prompt = "Extract fields: 'Company Name', 'Industry', 'Locations'."
        return await self._run_extraction(prompt, structured_data, IdentityExtraction, source_url)

    async def extract_products(self, structured_data: dict, source_url: str) -> Any:
        from server.onboarding_api import ProductsExtraction, EvidenceField
        prompt = "Extract fields: 'Product Categories', 'Pricing Mentioned'."
        return await self._run_extraction(prompt, structured_data, ProductsExtraction, source_url)

    async def extract_social_proof(self, structured_data: dict, source_url: str) -> Any:
        from server.onboarding_api import SocialProofExtraction, EvidenceField
        prompt = "Extract fields: 'Case Studies', 'Customers Mentioned'."
        return await self._run_extraction(prompt, structured_data, SocialProofExtraction, source_url)

    async def draft_email(self, prompt_context: dict, target_company: dict, hint: str = None) -> tuple[Any, dict]:
        import time
        import json
        start_time = time.time()
        
        prompt_version = "v2.2_openrouter"
        
        hint_instruction = f"\n\nReviewer instruction: {hint}" if hint else ""
        system_prompt = (
            "You are an elite B2B SDR. Write a short cold outreach email (under 100 words).\n"
            "1. You MUST use the provided Prompt Context snippets to personalize the email.\n"
            "2. List exact citations (Field, Snippet, URL) you used.\n"
            f"Prospect: {target_company.get('first_name')} {target_company.get('last_name')}, {target_company.get('title')} at {target_company.get('company')}\n"
            f"Prompt Context:\n{json.dumps(prompt_context, indent=2)}\n{hint_instruction}"
        )
        
        try:
            from server.onboarding_api import GroundedEmailDraft
            provider = self._get_provider("email")
            data = await provider.generate_structured(system_prompt, GroundedEmailDraft)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider=provider.name, model=provider.model_name, latency_ms=latency)
            
            return data, {"prompt_version": prompt_version, "model": provider.model_name, "temperature": 0.4}
        except Exception as e:
            logger.error("ai_gateway_email_draft_failed", error=str(e))
            raise

gateway = AIGateway()
