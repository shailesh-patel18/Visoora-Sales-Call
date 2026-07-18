from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from security.rbac import get_current_user, UserPrincipal
from security.config import settings
import structlog
import asyncio
import httpx
import re
from bs4 import BeautifulSoup

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
            "description": "Every AI-generated insight must be backed by evidence from the source website and include a confidence score. If you cannot find strong evidence in the text, set the value to 'Unable to verify', confidence to 0, and snippet to 'N/A'."
        }

async def in_house_crawl(base_url: str) -> dict:
    """An in-house crawler that checks the homepage and common subpages, returning structured JSON."""
    from urllib.parse import urlparse
    import json
    parsed = urlparse(base_url)
    if not parsed.scheme:
        base_url = "https://" + base_url
    
    # Normalize base URL
    base_url = base_url.rstrip("/")
    paths_to_check = ["/", "/about", "/about-us", "/pricing", "/services", "/product"]
    
    structured_data = {
        "metadata": {"sourceURL": base_url},
        "pages": []
    }
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async def fetch_path(path: str) -> dict:
            try:
                res = await client.get(f"{base_url}{path}", headers=headers)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # 1. Metadata
                    title = soup.title.string if soup.title else ""
                    meta_desc = ""
                    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                    if desc_tag:
                        meta_desc = desc_tag.get("content", "")
                        
                    # 2. Schema.org
                    schemas = []
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            schemas.append(json.loads(script.string))
                        except:
                            pass
                            
                    # 3. Headers
                    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
                    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
                    
                    # 4. Clean text fallback
                    for el in soup(["nav", "header", "footer", "script", "style", "noscript", "iframe", "svg"]):
                        el.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    
                    if len(text) > 50 or title or meta_desc:
                        return {
                            "path": path,
                            "title": title,
                            "description": meta_desc,
                            "schemas": schemas,
                            "h1s": h1s,
                            "h2s": h2s,
                            "text_sample": text[:2000]
                        }
            except Exception as e:
                pass
            return None

        results = await asyncio.gather(*(fetch_path(p) for p in paths_to_check))
        for r in results:
            if r:
                structured_data["pages"].append(r)
            
    if not structured_data["pages"]:
        raise ValueError("not found")
        
    return structured_data

@router.post("/analyze-domain", response_model=AnalyzeDomainResponse)
async def analyze_domain(payload: AnalyzeRequest, user: UserPrincipal = Depends(get_current_user)):
    url = payload.website
    logger.info("analyze_domain_started", website=url, tenant_id=user.tenant_id)

    # 1. Scrape the website with retry logic
    max_retries = 1
    scrape_data = None
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Run our in-house crawler
            scrape_data = await in_house_crawl(url)
            break  # Success, exit retry loop
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            logger.warning("in_house_crawl_attempt_failed", attempt=attempt, error=str(e), website=url)
            
            # Don't retry on certain fatal errors
            if "403" in error_str or "forbidden" in error_str or "cloudflare" in error_str:
                logger.error("in_house_crawl_blocked", error=str(e), website=url)
                raise HTTPException(status_code=400, detail={"error_type": "blocked", "message": "This site blocked our reader. Try adding /about or /pricing as a fallback URL, or use the manual fallback."})
                
            if "not found" in error_str or "404" in error_str or "dns" in error_str or "name or service not known" in error_str:
                logger.error("in_house_crawl_unreachable", error=str(e), website=url)
                raise HTTPException(status_code=400, detail={"error_type": "network", "message": "We couldn't reach this website. Please check the URL and try again."})
                
            if attempt < max_retries:
                await asyncio.sleep(3)  # Backoff
            else:
                logger.error("in_house_crawl_failed_final", error=str(e), website=url)
                # If it's a timeout
                if "timeout" in error_str:
                    raise HTTPException(status_code=400, detail={"error_type": "timeout", "message": "The website took too long to respond. It might be too large or slow."})
                raise HTTPException(status_code=400, detail={"error_type": "unknown_scrape_error", "message": f"Failed to scrape website: {str(e)}"})

    pages = scrape_data.get('pages', [])
    metadata = scrape_data.get('metadata') or {}
    source_url = metadata.get('sourceURL') or metadata.get('source_url') or url

    if not pages:
        logger.error("in_house_crawl_low_content", website=url, pages_len=len(pages))
        raise HTTPException(status_code=400, detail={"error_type": "low_content", "message": "We read the site but couldn't find enough information to build a profile. Please use the manual fallback to add a quick description instead."})

    # 2. Extract structured evidence via AI Gateway
    logger.info("ai_gateway_extraction_started", pages=len(pages))
    try:
        from server.ai_gateway import gateway
        extraction = await gateway.extract_business_brain(url=url, structured_data=scrape_data, source_url=source_url)
        return extraction
    except Exception as e:
        logger.error("ai_gateway_extraction_failed", error=str(e), tenant_id=user.tenant_id, url=url)
        raise HTTPException(status_code=500, detail={"error_type": "llm_failure", "message": "Failed to extract intelligence from website via AI Gateway."})

@router.post("/complete")
async def complete_onboarding(payload: dict, user: UserPrincipal = Depends(get_current_user)):
    from server.storage_manager import storage, supabase_admin_client
    import uuid
    import datetime
    
    logger.info("onboarding_complete_requested", tenant_id=user.tenant_id)
    
    # Store Agent Config
    storage.upsert_agent_config(user.tenant_id, payload)
    
    # Enqueue ICP generation job
    if supabase_admin_client:
        try:
            job_data = {
                "id": str(uuid.uuid4()),
                "tenant_id": user.tenant_id,
                "workflow_type": "icp_generation",
                "status": "queued",
                "payload": {"agent_config": payload},
                "created_at": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
            supabase_admin_client.table("workflow_jobs").insert(job_data).execute()
            logger.info("enqueued_icp_generation", tenant_id=user.tenant_id, job_id=job_data["id"])
        except Exception as e:
            logger.error("failed_to_enqueue_icp_job", error=str(e), tenant_id=user.tenant_id)
    
    return {"status": "success"}
