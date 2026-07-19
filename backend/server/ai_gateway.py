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
            "You are an expert business analyst. Extract detailed business insights from this website based on the schema.\n"
            "1. You must never invent information.\n"
            "2. If you cannot find strong evidence in the text, set the value to 'Unable to verify', confidence to 0, and snippet to 'N/A'.\n"
            f"3. Set source_url to {source_url} for all valid snippets.\n"
        )
        
        try:
            from server.onboarding_api import AnalyzeDomainResponse
            schema = AnalyzeDomainResponse.model_json_schema()
            data = await self._firecrawl_extract(source_url, prompt, schema)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="firecrawl", model="extract", latency_ms=latency)
            
            return AnalyzeDomainResponse(**data)
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
            "You are an ICP extraction engine. Based on this company's website, extract Ideal Customer Profile (ICP) segments.\n"
            "1. You must never invent information.\n"
            "2. Every ICP MUST be backed by a direct quote (snippet) proving this ICP is viable.\n"
            f"3. Ensure the source_url is {source_url}.\n"
        )
        
        try:
            schema = ICPGenerationResponse.model_json_schema()
            data = await self._firecrawl_extract(source_url, prompt, schema)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="firecrawl", model="extract", latency_ms=latency)
            
            return ICPGenerationResponse(**data)
            
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
            f"{prompt}"
        )
        
        try:
            schema = response_model.model_json_schema()
            res_data = await self._firecrawl_extract(source_url, full_prompt, schema)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="firecrawl", model="extract", latency_ms=latency)
            
            return response_model(**res_data)
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
        
        prompt_version = "v2.1_firecrawl"
        model_name = "firecrawl_extract"
        
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
            schema = GroundedEmailDraft.model_json_schema()
            # Pass a dummy url to Firecrawl so it works
            data = await self._firecrawl_extract("https://example.com", system_prompt, schema)
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="firecrawl", model="extract", latency_ms=latency)
            
            return GroundedEmailDraft(**data), {"prompt_version": prompt_version, "model": model_name, "temperature": 0.4}
        except Exception as e:
            logger.error("ai_gateway_email_draft_failed", error=str(e))
            raise

gateway = AIGateway()
