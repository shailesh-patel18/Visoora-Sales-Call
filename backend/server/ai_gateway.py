import os
import json
import hashlib
import structlog
import datetime
import asyncio
from typing import Optional, Dict, Any
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

class AIGateway:
    """
    Centralized AI Gateway handling caching, mock responses, multi-provider routing, and cost logging.
    """
    def __init__(self):
        self.mock_level = os.getenv("MOCK_LEVEL", "LIVE").upper()
        # Initialize providers lazily
        self._openai_client = None
        self._locks = {}  # Deduplication locks mapping url_hash -> asyncio.Lock

    def _normalize_url(self, url: str) -> str:
        """Strips scheme, www, and trailing slashes for consistent caching."""
        parsed = urlparse(url if "://" in url else f"https://{url}")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        normalized = f"{netloc}{path}"
        return normalized

    def _hash_url(self, normalized_url: str) -> str:
        return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()

    async def _check_cache(self, url_hash: str) -> Optional[Dict]:
        """Queries Supabase for a cached extraction, honoring TTL."""
        try:
            from server.storage_manager import supabase_admin_client
            if not supabase_admin_client:
                return None
                
            response = supabase_admin_client.table("ai_cache").select("*").eq("url_hash", url_hash).order("created_at", desc=True).limit(1).execute()
            if response.data and len(response.data) > 0:
                record = response.data[0]
                expires_at_str = record.get("expires_at")
                if expires_at_str:
                    # Parse ISO format datetime
                    expires_at = datetime.datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
                        logger.info("ai_gateway_cache_expired", url_hash=url_hash)
                        return None

                logger.info("ai_gateway_cache_hit", url_hash=url_hash)
                return record["response_json"]
        except Exception as e:
            logger.warning("ai_gateway_cache_error", error=str(e))
        return None

    async def _write_cache(self, url_hash: str, original_url: str, response_json: Dict):
        """Writes successful extraction to Supabase as a new version."""
        try:
            from server.storage_manager import supabase_admin_client
            if not supabase_admin_client:
                return
            
            # Default TTL for Business Brain is 7 days
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            
            data = {
                "url_hash": url_hash,
                "original_url": original_url,
                "response_json": response_json,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat()
            }
            # Insert instead of upsert for Evidence Versioning
            supabase_admin_client.table("ai_cache").insert(data).execute()
            logger.info("ai_gateway_cache_write", url_hash=url_hash, expires_at=expires_at.isoformat())
        except Exception as e:
            logger.warning("ai_gateway_cache_write_error", error=str(e))

    def _get_static_mock(self, url: str) -> Any:
        """Returns a completely static mock object mapping the AnalyzeDomainResponse structure."""
        from server.onboarding_api import AnalyzeDomainResponse, EvidenceStringField
        
        mock_str = lambda val: EvidenceStringField(value=val, confidence=100, snippet="Mock snippet", source_url=url)
        return AnalyzeDomainResponse(
            company_name=mock_str("Mock Startup Inc"),
            company_description=mock_str("We build cost-aware AI platforms for bootstrapped founders."),
            value_proposition=mock_str("Save $1000s on AI API costs with intelligent gateways."),
            estimated_industries=[mock_str("B2B SaaS"), mock_str("AI Tooling")],
            estimated_regions=[mock_str("Global")],
            estimated_decision_makers=[mock_str("CTOs"), mock_str("Founders")],
            potential_competitors=[mock_str("Acme Corp")],
            potential_objections=[{
                "objection": "It's too hard to setup.",
                "rebuttal": "We provide a 1-click gateway.",
                "confidence": 95,
                "snippet": "1-click deployment",
                "source_url": url
            }],
            suggested_segments=[{
                "segment": "Bootstrapped Founders",
                "rationale": "They need to save money.",
                "confidence": 98,
                "snippet": "Bootstrap friendly",
                "source_url": url
            }],
            brand_voice_tone=mock_str("Professional yet scrappy")
        )

    def _log_cost(self, provider: str, model: str, latency_ms: float, tokens_in: int = 0, tokens_out: int = 0):
        logger.info("ai_gateway_cost_log", 
                    provider=provider, 
                    model=model, 
                    latency_ms=latency_ms, 
                    tokens_in=tokens_in, 
                    tokens_out=tokens_out)

    async def extract_business_brain(self, url: str, structured_data: dict, source_url: str, force_refresh: bool = False) -> Any:
        """
        Main entry point for extracting a Business Brain.
        Handles Mocking, Caching, and Provider Routing.
        """
        from server.onboarding_api import AnalyzeDomainResponse

        # 1. Mock Mode Check
        if self.mock_level == "STATIC":
            logger.info("ai_gateway_mock_static_triggered", url=url)
            return self._get_static_mock(url)

        # 2. Cache Check & Deduplication Lock
        norm_url = self._normalize_url(url)
        url_hash = self._hash_url(norm_url)
        
        if url_hash not in self._locks:
            self._locks[url_hash] = asyncio.Lock()
            
        async with self._locks[url_hash]:
            if not force_refresh:
                cached_data = await self._check_cache(url_hash)
                if cached_data:
                    return AnalyzeDomainResponse(**cached_data)
            
        # 3. Provider Router
        import time
        start_time = time.time()
        
        _openai_key = os.getenv('OPENAI_API_KEY')
        if not _openai_key:
            raise ValueError("OPENAI_API_KEY is not set. Cannot run LIVE extraction.")
            
        aclient = instructor.from_openai(AsyncOpenAI(api_key=_openai_key))
        
        try:
            extraction = await aclient.chat.completions.create(
                model="gpt-4o-mini",
                response_model=AnalyzeDomainResponse,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are a strictly objective reasoning engine. Your ONLY job is to extract business details from the provided structured website data.\n\n"
                            "CORE PRINCIPLE: EVIDENCE BACKED.\n"
                            "1. You must never invent information. Base your answers strictly on the provided structured data (metadata, headers, text).\n"
                            "2. Every extracted field MUST be backed by a direct quote (`snippet`) from the text or metadata.\n"
                            "3. If the information is missing from the data, you MUST set the value to 'Unable to verify', `confidence` to 0, and `snippet` to 'N/A'.\n"
                            "4. Confidence should be 95-100 for explicitly stated facts, 60-94 for weakly stated facts, and 0 for missing facts.\n"
                            f"5. Set `source_url` to {source_url} for all valid snippets."
                        )
                    },
                    {"role": "user", "content": f"Structured Website Data:\n\n{json.dumps(structured_data, indent=2)[:20000]}"}
                ]
            )
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="openai", model="gpt-4o-mini", latency_ms=latency)
            
            # 4. Write to Cache
            await self._write_cache(url_hash, url, extraction.model_dump())
            
            return extraction
            
        except Exception as e:
            logger.error("ai_gateway_extraction_failed", error=str(e), url=url)
            raise

    async def generate_icps_from_brain(self, business_brain_data: dict) -> Any:
        """
        Takes verified facts from a Business Brain and extracts/reasons ICPs from them.
        Enforces that ICPs must be backed by evidence in the provided data.
        """
        from pydantic import BaseModel, Field
        from typing import List
        
        class EvidenceICPField(BaseModel):
            segment: str = Field(..., description="The name of the Ideal Customer Profile segment.")
            rationale: str = Field(..., description="Why this segment is a good fit.")
            confidence: int = Field(..., description="Confidence score from 0 to 100.")
            snippet: str = Field(..., description="Exact quote from the Business Brain proving this ICP.")
            source_url: str = Field(..., description="URL where this evidence was found.")

        class ICPGenerationResponse(BaseModel):
            icps: List[EvidenceICPField]
            
        import time
        start_time = time.time()
        
        _openai_key = os.getenv('OPENAI_API_KEY')
        if not _openai_key:
            if self.mock_level == "STATIC":
                # Static fallback for frontend devs
                return ICPGenerationResponse(icps=[
                    EvidenceICPField(
                        segment="Bootstrapped Founders",
                        rationale="They need to save money.",
                        confidence=98,
                        snippet="Bootstrap friendly",
                        source_url="https://mock.com"
                    )
                ])
            raise ValueError("OPENAI_API_KEY is not set. Cannot run LIVE extraction.")
            
        aclient = instructor.from_openai(AsyncOpenAI(api_key=_openai_key))
        
        try:
            extraction = await aclient.chat.completions.create(
                model="gpt-4o-mini",
                response_model=ICPGenerationResponse,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are an ICP extraction engine. Base your ICP definitions ONLY on the provided verified Business Brain facts.\n"
                            "1. You must never invent information. Base your answers strictly on the provided Business Brain data.\n"
                            "2. Every ICP MUST be backed by a direct quote (`snippet`) from the Business Brain proving this ICP is viable.\n"
                        )
                    },
                    {"role": "user", "content": f"Business Brain Data:\n\n{json.dumps(business_brain_data, indent=2)[:20000]}"}
                ]
            )
            
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="openai", model="gpt-4o-mini", latency_ms=latency)
            
            return extraction
            
        except Exception as e:
            logger.error("ai_gateway_icp_generation_failed", error=str(e))
            raise

    async def _run_extraction(self, prompt: str, data: dict, response_model: Any, source_url: str) -> Any:
        import time
        start_time = time.time()
        _openai_key = os.getenv('OPENAI_API_KEY')
        if not _openai_key:
            raise ValueError("OPENAI_API_KEY is not set.")
            
        aclient = instructor.from_openai(AsyncOpenAI(api_key=_openai_key))
        
        try:
            extraction = await aclient.chat.completions.create(
                model="gpt-4o-mini",
                response_model=response_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict, objective extraction engine.\n"
                            "CORE PRINCIPLE: EVIDENCE BACKED.\n"
                            "1. You must never invent information or provide estimates.\n"
                            "2. Every extracted field MUST be backed by a direct quote (`snippet`) from the provided data.\n"
                            "3. If information is missing, set value to 'Unknown', confidence to 0, and snippet to 'N/A'.\n"
                            f"4. Set source_url to {source_url} for all valid snippets.\n\n"
                            f"{prompt}"
                        )
                    },
                    {"role": "user", "content": f"Structured Data:\n\n{json.dumps(data, indent=2)[:15000]}"}
                ]
            )
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="openai", model="gpt-4o-mini", latency_ms=latency)
            return extraction
        except Exception as e:
            logger.error("ai_gateway_knowledge_extraction_failed", error=str(e))
            raise

    async def extract_identity(self, structured_data: dict, source_url: str) -> IdentityExtraction:
        prompt = "Extract fields: 'Company Name', 'Industry', 'Locations'. Return a list of EvidenceFields."
        if self.mock_level == "STATIC":
            return IdentityExtraction(fields=[EvidenceField(field="Company Name", value="Mock", source_url=source_url, snippet="mock", confidence=100)])
        return await self._run_extraction(prompt, structured_data, IdentityExtraction, source_url)

    async def extract_products(self, structured_data: dict, source_url: str) -> ProductsExtraction:
        prompt = "Extract fields: 'Product Categories', 'Pricing Mentioned'. Return a list of EvidenceFields."
        if self.mock_level == "STATIC":
            return ProductsExtraction(fields=[EvidenceField(field="Product Categories", value="Mock", source_url=source_url, snippet="mock", confidence=100)])
        return await self._run_extraction(prompt, structured_data, ProductsExtraction, source_url)

    async def extract_social_proof(self, structured_data: dict, source_url: str) -> SocialProofExtraction:
        prompt = "Extract fields: 'Case Studies', 'Customers Mentioned'. Return a list of EvidenceFields."
        if self.mock_level == "STATIC":
            return SocialProofExtraction(fields=[EvidenceField(field="Case Studies", value="Mock", source_url=source_url, snippet="mock", confidence=100)])
        return await self._run_extraction(prompt, structured_data, SocialProofExtraction, source_url)

    async def draft_email(self, prompt_context: dict, target_company: dict, hint: str = None) -> tuple[GroundedEmailDraft, dict]:
        """
        Drafts a grounded email using only the provided prompt_context.
        Returns the draft and metadata about the generation (prompt_version, model).
        """
        import time
        start_time = time.time()
        _openai_key = os.getenv('OPENAI_API_KEY')
        
        prompt_version = "v2.1"
        model_name = "gpt-4o"
        temperature = 0.4
        
        if not _openai_key:
            if self.mock_level == "STATIC":
                mock_draft = GroundedEmailDraft(
                    subject="Quick question", 
                    body="Mock email body.", 
                    citations=[EmailCitation(field="Mock", snippet="Mock snippet", source_url="https://mock.com")]
                )
                return mock_draft, {"prompt_version": prompt_version, "model": model_name, "temperature": temperature}
            raise ValueError("OPENAI_API_KEY is not set.")
            
        aclient = instructor.from_openai(AsyncOpenAI(api_key=_openai_key))
        
        hint_instruction = f"\n\nReviewer instruction: {hint}" if hint else ""
        system_prompt = (
            "You are an elite B2B SDR. Write a short cold outreach email (under 100 words).\n"
            "CORE PRINCIPLE: EVIDENCE BACKED.\n"
            "1. You MUST use the provided Prompt Context snippets to personalize the email.\n"
            "2. If a fact is not in the Prompt Context, do NOT mention it. Refuse to guess.\n"
            "3. You must list the exact `citations` (Field, Snippet, URL) you used to prove your personalization."
        )
        
        user_prompt = (
            f"Prospect: {target_company.get('first_name')} {target_company.get('last_name')}, {target_company.get('title')} at {target_company.get('company')}\n\n"
            f"Prompt Context (Verified Evidence):\n{json.dumps(prompt_context, indent=2)}\n"
            f"{hint_instruction}"
        )
        
        try:
            draft = await aclient.chat.completions.create(
                model=model_name,
                temperature=temperature,
                response_model=GroundedEmailDraft,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            latency = (time.time() - start_time) * 1000
            self._log_cost(provider="openai", model=model_name, latency_ms=latency)
            return draft, {"prompt_version": prompt_version, "model": model_name, "temperature": temperature}
        except Exception as e:
            logger.error("ai_gateway_email_draft_failed", error=str(e))
            raise

gateway = AIGateway()
