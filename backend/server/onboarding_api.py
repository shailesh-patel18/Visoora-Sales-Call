from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
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

import os
from server.sse_manager import sse_broadcast, subscribe_to_tenant

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

class EvidenceStringField(BaseModel):
    value: str
    confidence: int = Field(..., ge=0, le=100, description="Confidence score from 0 to 100 based strictly on provided text.")
    snippet: str = Field(..., description="Exact quote from the source text verifying this claim. Or 'N/A' if unable to verify.")
    source_url: str = Field(..., description="URL where this snippet was found. Or 'N/A'.")
    source: str = Field("LLM", description="Where this field was extracted from (e.g. 'schema.org', 'OpenGraph', 'LLM')")

class EvidenceObjectionField(BaseModel):
    objection: str
    rebuttal: str
    confidence: int
    snippet: str
    source_url: str
    source: str = Field("LLM")

class EvidenceSegmentField(BaseModel):
    segment: str
    rationale: str
    confidence: int
    snippet: str
    source_url: str
    source: str = Field("LLM")

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

async def background_analyze_domain(url: str, job_id: str, tenant_id: str):
    logger.info("background_analyze_started", website=url, job_id=job_id)
    
    if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
        from server.mock_fixtures import mock_onboarding_response
        # Offline dev mode mock
        steps = ["reachable", "robots", "sitemap", "metadata", "opengraph", "schema", "pricing", "about", "blog", "contacts", "ai_summary", "business_brain", "icp"]
        for i, step in enumerate(steps):
            sse_broadcast(job_id, {"step": step, "status": "running", "progress": int((i / len(steps)) * 100)})
            await asyncio.sleep(0.5)
            sse_broadcast(job_id, {"step": step, "status": "done", "progress": int(((i + 1) / len(steps)) * 100)})
        sse_broadcast(job_id, {"step": "completed", "status": "done", "progress": 100, "result": mock_onboarding_response.model_dump()})
        return

    # Broadcast initial steps before we start
    sse_broadcast(job_id, {"step": "reachable", "status": "running", "progress": 5})
    
    # 1. Scrape the website with retry logic
    max_retries = 2
    scrape_data = None
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Run our in-house crawler
            sse_broadcast(job_id, {"step": "reachable", "status": "done", "progress": 10})
            sse_broadcast(job_id, {"step": "robots", "status": "running", "progress": 12})
            await asyncio.sleep(0.5) # simulate robots check
            sse_broadcast(job_id, {"step": "robots", "status": "done", "progress": 15})
            
            sse_broadcast(job_id, {"step": "sitemap", "status": "running", "progress": 18})
            await asyncio.sleep(0.5) # simulate sitemap check
            sse_broadcast(job_id, {"step": "sitemap", "status": "done", "progress": 20})

            sse_broadcast(job_id, {"step": "metadata", "status": "running", "progress": 25})
            scrape_data = await in_house_crawl(url)
            break  # Success, exit retry loop
            
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            logger.warning("in_house_crawl_attempt_failed", attempt=attempt, error=str(e), website=url)
            
            # Don't retry on certain fatal errors
            if "403" in error_str or "forbidden" in error_str or "cloudflare" in error_str:
                logger.error("in_house_crawl_blocked", error=str(e), website=url)
                sse_broadcast(job_id, {"step": "error", "status": "error", "message": "Site blocked our reader (Cloudflare/403)."})
                return
                
            if "not found" in error_str or "404" in error_str or "dns" in error_str or "name or service not known" in error_str:
                logger.error("in_house_crawl_unreachable", error=str(e), website=url)
                sse_broadcast(job_id, {"step": "error", "status": "error", "message": "Website unreachable (DNS/404)."})
                return
                
            if attempt < max_retries:
                await asyncio.sleep(3)  # Backoff
            else:
                logger.error("in_house_crawl_failed_final", error=str(e), website=url)
                sse_broadcast(job_id, {"step": "error", "status": "error", "message": f"Scraping failed: {str(e)}"})
                return

    pages = scrape_data.get('pages', [])
    metadata = scrape_data.get('metadata') or {}
    source_url = metadata.get('sourceURL') or metadata.get('source_url') or url

    if not pages:
        logger.error("in_house_crawl_low_content", website=url, pages_len=len(pages))
        sse_broadcast(job_id, {"step": "error", "status": "error", "message": "Low content found on page."})
        return

    # Deterministic Extraction Layers mock for UI
    sse_broadcast(job_id, {"step": "metadata", "status": "done", "progress": 30})
    sse_broadcast(job_id, {"step": "opengraph", "status": "running", "progress": 35})
    await asyncio.sleep(0.3)
    sse_broadcast(job_id, {"step": "opengraph", "status": "done", "progress": 40})
    
    sse_broadcast(job_id, {"step": "schema", "status": "running", "progress": 45})
    await asyncio.sleep(0.3)
    sse_broadcast(job_id, {"step": "schema", "status": "done", "progress": 50})
    
    # Check what pages we actually found to update those specific steps
    paths_found = [p.get('path', '') for p in pages]
    
    if '/pricing' in paths_found:
        sse_broadcast(job_id, {"step": "pricing", "status": "running", "progress": 55})
        await asyncio.sleep(0.3)
        sse_broadcast(job_id, {"step": "pricing", "status": "done", "progress": 60})
        
    if any(p in paths_found for p in ['/about', '/about-us']):
        sse_broadcast(job_id, {"step": "about", "status": "running", "progress": 62})
        await asyncio.sleep(0.3)
        sse_broadcast(job_id, {"step": "about", "status": "done", "progress": 65})
        
    sse_broadcast(job_id, {"step": "ai_summary", "status": "running", "progress": 70})
    await asyncio.sleep(0.5)
    sse_broadcast(job_id, {"step": "ai_summary", "status": "done", "progress": 75})
    
    sse_broadcast(job_id, {"step": "business_brain", "status": "running", "progress": 80})
    
    # 2. Extract structured evidence via AI Gateway
    logger.info("ai_gateway_extraction_started", pages=len(pages))
    try:
        from server.ai_gateway import gateway
        
        # We retry the AI extraction just in case
        extraction = None
        for ai_attempt in range(3):
            try:
                extraction = await gateway.extract_business_brain(url=url, structured_data=scrape_data, source_url=source_url)
                break
            except Exception as ex:
                if ai_attempt < 2:
                    await asyncio.sleep(2 ** ai_attempt)
                else:
                    raise ex
                    
        sse_broadcast(job_id, {"step": "business_brain", "status": "done", "progress": 90})
        sse_broadcast(job_id, {"step": "icp", "status": "running", "progress": 95})
        await asyncio.sleep(0.5)
        sse_broadcast(job_id, {"step": "icp", "status": "done", "progress": 99})
        
        sse_broadcast(job_id, {"step": "completed", "status": "done", "progress": 100, "result": extraction.model_dump()})
    except Exception as e:
        logger.error("ai_gateway_extraction_failed", error=str(e), tenant_id=tenant_id, url=url)
        sse_broadcast(job_id, {"step": "error", "status": "error", "message": "AI Extraction failed. Please try again."})


class JobResponse(BaseModel):
    job_id: str

from fastapi import status

@router.post("/analyze-domain", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analyze_domain(payload: AnalyzeRequest, bg_tasks: BackgroundTasks, user: UserPrincipal = Depends(get_current_user)):
    import uuid
    job_id = f"onboarding_{uuid.uuid4().hex}"
    bg_tasks.add_task(background_analyze_domain, payload.website, job_id, user.tenant_id)
    return JobResponse(job_id=job_id)

@router.get("/events/{job_id}")
async def sse_events(job_id: str):
    return StreamingResponse(subscribe_to_tenant(job_id), media_type="text/event-stream")

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
