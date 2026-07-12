from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from security.rbac import get_current_user, UserPrincipal
from security.config import settings
import structlog
import asyncio

try:
    from firecrawl import FirecrawlApp
except ImportError:
    FirecrawlApp = None

from openai import AsyncOpenAI
import instructor

logger = structlog.get_logger("onboarding_api")

def resolve_tenant_uuid(tenant_id: str) -> str:
    # Basic mock for now to satisfy imports
    import uuid
    # Try to return a valid uuid
    try:
        uuid.UUID(tenant_id)
        return tenant_id
    except ValueError:
        return "00000000-0000-0000-0000-000000000000"

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Firecrawl & OpenAI Setup (lazy — safe for CI/test environments without keys)
firecrawl_app = None
if FirecrawlApp and getattr(settings, 'firecrawl_api_key', None):
    try:
        firecrawl_app = FirecrawlApp(api_key=settings.firecrawl_api_key)
    except Exception as e:
        logger.error("firecrawl_init_failed", error=str(e))

aclient = None
_openai_key = getattr(settings, 'openai_api_key', None)
if _openai_key:
    try:
        aclient = instructor.from_openai(AsyncOpenAI(api_key=_openai_key))
    except Exception as e:
        logger.error("instructor_init_failed", error=str(e))

class AnalyzeRequest(BaseModel):
    website: str

# Zero Hallucination Evidence Models
class EvidenceStringField(BaseModel):
    value: str
    confidence: int = Field(..., ge=0, le=100, description="Confidence score from 0 to 100 based strictly on provided text.")
    snippet: str = Field(..., description="Exact quote from the source text verifying this claim. Or 'N/A' if unable to verify.")
    source_url: str = Field(..., description="URL where this snippet was found. Or 'N/A'.")

class EvidenceObjectionField(BaseModel):
    objection: str
    rebuttal: str
    confidence: int
    snippet: str
    source_url: str

class EvidenceSegmentField(BaseModel):
    segment: str
    rationale: str
    confidence: int
    snippet: str
    source_url: str

class AnalyzeDomainResponse(BaseModel):
    company_name: EvidenceStringField
    company_description: EvidenceStringField
    value_proposition: EvidenceStringField
    estimated_industries: List[EvidenceStringField]
    estimated_regions: List[EvidenceStringField]
    estimated_decision_makers: List[EvidenceStringField]
    potential_competitors: List[EvidenceStringField]
    potential_objections: List[EvidenceObjectionField]
    suggested_segments: List[EvidenceSegmentField]
    brand_voice_tone: EvidenceStringField

    class Config:
        json_schema_extra = {
            "description": "Extract ONLY what is explicitly stated in the provided text. Never guess, infer, or hallucinate. If you cannot find strong evidence in the text, set the value to 'Unable to verify', confidence to 0, and snippet to 'N/A'."
        }

@router.post("/analyze-domain", response_model=AnalyzeDomainResponse)
async def analyze_domain(payload: AnalyzeRequest, user: UserPrincipal = Depends(get_current_user)):
    url = payload.website
    logger.info("analyze_domain_started", website=url, tenant_id=user.tenant_id)

    if not firecrawl_app:
        raise HTTPException(status_code=500, detail="Firecrawl API key is missing or invalid.")

    # 1. Scrape the website
    try:
        # Run synchronous firecrawl in a thread pool to avoid blocking async loop
        scrape_result = await asyncio.to_thread(
            firecrawl_app.scrape_url,
            url
        )
        
        # Support both older firecrawl dict returns and newer v1.0.0+ Pydantic Document returns
        if hasattr(scrape_result, 'model_dump'):
            scrape_data = scrape_result.model_dump()
        elif hasattr(scrape_result, 'dict'):
            scrape_data = scrape_result.dict()
        else:
            scrape_data = scrape_result
            
        markdown_content = scrape_data.get('markdown', '')
        metadata = scrape_data.get('metadata') or {}
        source_url = metadata.get('sourceURL') or metadata.get('source_url') or url
    except Exception as e:
        logger.error("firecrawl_scrape_failed", error=str(e), website=url)
        raise HTTPException(status_code=400, detail=f"Failed to scrape website: {str(e)}")

    if not markdown_content:
        raise HTTPException(status_code=400, detail="Could not extract any content from the website.")

    # 2. Extract structured evidence using LLM
    logger.info("llm_extraction_started", markdown_length=len(markdown_content))
    try:
        extraction = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            response_model=AnalyzeDomainResponse,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a strictly objective data extractor. Your ONLY job is to extract business details from the provided website text.\n\n"
                        "CORE PRINCIPLE: ZERO HALLUCINATION.\n"
                        "1. You must NEVER guess, infer, or hallucinate.\n"
                        "2. Every extracted field MUST be backed by a direct quote (`snippet`) from the text.\n"
                        "3. If the information is missing from the text, you MUST set the value to 'Unable to verify', `confidence` to 0, and `snippet` to 'N/A'.\n"
                        "4. Confidence should be 95-100 for explicitly stated facts, 60-94 for weakly stated facts, and 0 for missing facts.\n"
                        f"5. Set `source_url` to {source_url} for all valid snippets."
                    )
                },
                {"role": "user", "content": f"Website Content:\n\n{markdown_content[:20000]}"}
            ]
        )
        return extraction
    except Exception as e:
        logger.error("llm_extraction_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to extract intelligence from website.")

@router.post("/complete")
async def complete_onboarding(payload: dict, user: UserPrincipal = Depends(get_current_user)):
    from server.storage_manager import storage
    logger.info("onboarding_complete_requested", tenant_id=user.tenant_id)
    
    # Store Agent Config
    storage.upsert_agent_config(user.tenant_id, payload)
    
    return {"status": "success"}
