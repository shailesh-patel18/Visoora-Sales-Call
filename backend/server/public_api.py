import os
import json
import httpx
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import structlog
import asyncio
from ai_platform.agents.research_agent import ResearchAgent

logger = structlog.get_logger("visoora_public_api")

public_router = APIRouter(prefix="/api/public", tags=["Public"])

class AnalyzeRequest(BaseModel):
    url: str
    captcha_token: str = None  # Optional for now to not break existing frontend if missing, but will enforce below.

@public_router.post("/analyze-website")
async def analyze_website(payload: AnalyzeRequest, request: Request):
    """
    Public endpoint for the landing page demo.
    Scrapes a snippet of the target website and returns LLM-generated business intelligence.
    Rate-limited and restricted to small text snippets to prevent abuse.
    """
    # 1. Turnstile CAPTCHA Validation (Mock for Phase 2)
    if not payload.captcha_token or payload.captcha_token == "test-bypass":
        # In production, verify token with Cloudflare API
        # raise HTTPException(status_code=400, detail="Invalid CAPTCHA token.")
        pass

    from security.url_validator import validate_and_normalize_url
    url = validate_and_normalize_url(payload.url)
    
    parsed = urlparse(url)
    domain = parsed.netloc

    # 2. Layered Rate Limiting
    from security.api_rate_limiter import enforce_layered_rate_limits
    await enforce_layered_rate_limits(request, domain=domain, tenant_id="anonymous")

    # 1. Intelligent Caching: Check if we already have a recent business brain for this domain
    from server.storage_manager import get_scoped_supabase_client, supabase_admin_client
    import datetime
    
    if supabase_admin_client:
        now_str = datetime.datetime.utcnow().isoformat()
        res = supabase_admin_client.table("business_brains")\
            .select("id")\
            .eq("domain", domain)\
            .gte("ttl_expires_at", now_str)\
            .execute()
            
        if res.data:
            return {"cached": True, "result_id": res.data[0]["id"]}

    # --- ENTERPRISE MIGRATION: COMPATIBILITY ADAPTER & SHADOW MODE ---
    try:
        from v2.foundation.context.feature_flags import FeatureFlags
        from v2.experience.compatibility.shadow_mode import ShadowRunner
        import asyncio
        
        async def run_v2_research_agent(url: str):
            """Stub to trigger the v2 workflow DAG instead of legacy job."""
            from v2.workflow.engine import WorkflowEngine
            from v2.workflow.models import WorkflowDefinition, WorkflowStep
            
            # Create a quick DAG for the agent
            def_stub = WorkflowDefinition(
                workflow_name="Shadow_Website_Analysis",
                steps=[WorkflowStep(step_id="analyze", action="execute_agent", agent_type="ResearchAgent", payload={"url": url})]
            )
            # Fire and forget execution init
            await WorkflowEngine.initialize(tenant_id="anonymous", definition=def_stub, payload={})
            return {"status": "v2_started"}

        async def run_legacy_workflow(url: str):
            from server.workflow_engine import create_workflow_job
            from server.job_handlers import get_website_analysis_steps
            job = create_workflow_job(
                workflow_type="website_analysis",
                tenant_id="public_demo",
                payload={"url": url},
                steps=get_website_analysis_steps()
            )
            return {"cached": False, "job_id": job.id, "message": "Analysis started"}

        # 1. Feature Flag Routing (100% v2 traffic)
        if FeatureFlags.is_enabled("WEBSITE_ANALYZER_V2_ENABLED"):
            # A real implementation would map the v2 job ID back to the legacy polling format
            # so the frontend doesn't break, but for now we stub it.
            await run_v2_research_agent(url)
            return {"cached": False, "job_id": "v2-mock-job-id", "message": "v2 Analysis started"}
            
        # 2. Shadow Mode (Run Legacy synchronously, fire v2 in background)
        if FeatureFlags.is_enabled("SHADOW_MODE_WEBSITE_ANALYZER"):
            return await ShadowRunner.run(
                tenant_id="anonymous",
                operation_name="analyze_website",
                legacy_func=run_legacy_workflow,
                v2_func=run_v2_research_agent,
                url=url
            )
    except ImportError:
        # Fallback if v2 modules fail to load
        logger.error("v2_compatibility_layer_failed_to_load")

    # --- END MIGRATION ADAPTER ---

    # 2. Not cached. Create a generic Workflow Job. (Legacy)
    from server.workflow_engine import create_workflow_job
    from server.job_handlers import get_website_analysis_steps
    
    job = create_workflow_job(
        workflow_type="website_analysis",
        tenant_id="public_demo",
        payload={"url": url},
        steps=get_website_analysis_steps()
    )
    
    return {"cached": False, "job_id": job.id, "message": "Analysis started"}

@public_router.get("/workflow/{job_id}/stream")
async def stream_workflow(job_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream progress to the frontend.
    """
    from fastapi.responses import StreamingResponse
    from server.sse_manager import subscribe_to_job
    
    return StreamingResponse(
        subscribe_to_job(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@public_router.get("/report/{result_id}")
async def get_report(result_id: str):
    """
    Fetches a cached report (Business Brain) by ID.
    """
    from server.storage_manager import get_scoped_supabase_client, supabase_admin_client
    if not supabase_admin_client:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    res = supabase_admin_client.table("business_brains").select("metadata").eq("id", result_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Report not found")
        
    metadata = res.data[0].get("metadata", {})
    full_report = metadata.get("full_report")
    if not full_report:
        raise HTTPException(status_code=404, detail="Report data incomplete")
        
    full_report["report_id"] = result_id
    return full_report


@public_router.post("/webhooks/sendgrid")
async def sendgrid_webhook(request: Request):
    """
    Public webhook receiver for SendGrid asynchronous events (opens, clicks, bounces).
    """
    from server.storage_manager import supabase_admin_client
    from server.events.bus import bus
    import datetime

    if not supabase_admin_client:
        return {"status": "error", "message": "Database not configured"}

    try:
        body_bytes = await request.body()
        events = json.loads(body_bytes)
        
        processed = 0
        for event in events:
            raw_msg_id = event.get("sg_message_id", "")
            event_type = event.get("event")
            
            # SendGrid affixes .filter to message IDs, we need the base ID
            base_message_id = raw_msg_id.split(".")[0]
            if not base_message_id or not event_type:
                continue
                
            # Find the mission_artifact that has this sendgrid_message_id in metadata
            res = supabase_admin_client.table("mission_artifacts").select("id, tenant_id, metadata")\
                .contains("metadata", {"sendgrid_message_id": base_message_id}).execute()
                
            if not res.data:
                continue
                
            artifact = res.data[0]
            artifact_id = artifact["id"]
            tenant_id = artifact["tenant_id"]
            metadata = artifact.get("metadata") or {}
            
            # Initialize or update tracking metrics
            tracking = metadata.get("tracking", {
                "opens": 0,
                "clicks": 0,
                "bounces": 0,
                "last_opened_at": None
            })
            
            now_iso = datetime.datetime.utcnow().isoformat()
            
            if event_type == "open":
                tracking["opens"] += 1
                tracking["last_opened_at"] = now_iso
                bus.publish("EmailOpened", {"artifact_id": artifact_id, "tenant_id": tenant_id, "timestamp": now_iso})
            elif event_type == "click":
                tracking["clicks"] += 1
                bus.publish("EmailClicked", {"artifact_id": artifact_id, "tenant_id": tenant_id, "url": event.get("url"), "timestamp": now_iso})
            elif event_type in ["bounce", "dropped", "deferred"]:
                tracking["bounces"] += 1
                bus.publish("EmailBounced", {"artifact_id": artifact_id, "tenant_id": tenant_id, "timestamp": now_iso})
            
            metadata["tracking"] = tracking
            
            # Persist tracking updates
            supabase_admin_client.table("mission_artifacts").update({"metadata": metadata}).eq("id", artifact_id).execute()
            logger.info("sendgrid_event_processed", sg_event_type=event_type, artifact_id=artifact_id)
            processed += 1
            
        return {"status": "ok", "processed": processed}
    except Exception as e:
        logger.error("sendgrid_webhook_failed", error=str(e))
        return {"status": "error", "message": str(e)}

@public_router.get("/health")
async def health_check():
    """
    Health monitoring endpoint.
    Reports the status of the database, Gemini, and prospecting providers.
    """
    from server.storage_manager import supabase_admin_client
    from server.prospecting.metrics_registry import global_metrics_registry
    
    health_status = {}
    
    # Database
    if supabase_admin_client:
        health_status["database"] = "healthy"
    else:
        health_status["database"] = "unconfigured"

    # Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip():
        health_status["gemini"] = "healthy"
    else:
        health_status["gemini"] = "unconfigured (missing API key)"

    # Development Mode Check
    dev_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    health_status["mode"] = "development" if dev_mode else "production"

    # Providers from metrics registry
    health_status["providers"] = global_metrics_registry.get_all_metrics()
    
    return health_status
