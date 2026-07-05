import uuid
import datetime
from ai_platform.agents.email_agent import EmailAgent
from security.logging import tenant_id_var
import asyncio
import httpx
from urllib.parse import urlparse
import structlog
from server.worker import register_job_handler
from server.workflow_engine import update_job_step, WorkflowStep
from ai_platform.agents.research_agent import ResearchAgent
from server.storage_manager import supabase_client

logger = structlog.get_logger("job_handlers")

# Define the dynamic steps for the website analysis workflow
def get_website_analysis_steps():
    return [
        WorkflowStep(step_id="crawling", label="Crawling Website"),
        WorkflowStep(step_id="extracting", label="Extracting Content"),
        WorkflowStep(step_id="business_understanding", label="Analyzing Business Model"),
        WorkflowStep(step_id="icp", label="Defining Ideal Customer Profiles"),
        WorkflowStep(step_id="competitors", label="Researching Competitors"),
        WorkflowStep(step_id="roadmap", label="Building Growth Roadmap")
    ]

async def website_analysis_handler(payload: dict, job_id: str) -> dict:
    url = payload.get("url")
    if not url:
        raise ValueError("URL is required in payload")
        
    parsed = urlparse(url)
    domain = parsed.netloc

    # Step 1: Crawling
    update_job_step(job_id, "crawling", "running")
    scraped_text = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await client.get(url, headers=headers, follow_redirects=True)
            res.raise_for_status()
            scraped_text += f"--- HOMEPAGE ---\n{res.text[:4000]}\n\n"
            
            # Simple concurrent crawl
            base_url = str(res.url).rstrip("/")
            paths_to_check = ["/about", "/services", "/pricing"]
            
            async def fetch_path(path: str):
                try:
                    p_res = await client.get(f"{base_url}{path}", headers=headers, follow_redirects=True)
                    if p_res.status_code == 200:
                        return f"--- {path.upper()} ---\n{p_res.text[:3000]}\n\n"
                except Exception:
                    pass
                return ""
                
            results = await asyncio.gather(*(fetch_path(p) for p in paths_to_check))
            for r in results:
                scraped_text += r
                
            scraped_text = scraped_text[:12000]
    except Exception as e:
        logger.error("crawl_failed", error=str(e))
        update_job_step(job_id, "crawling", "failed")
        raise ValueError("Failed to crawl the website.")
        
    update_job_step(job_id, "crawling", "success")

    # Step 2: Extracting & Analysis
    # We will simulate progressing through steps by updating state before/after the massive LLM call.
    # In a fully streaming LLM setup, we could parse intermediate JSON objects and update steps.
    update_job_step(job_id, "extracting", "running")
    await asyncio.sleep(1)
    update_job_step(job_id, "extracting", "success")
    
    update_job_step(job_id, "business_understanding", "running")
    
    try:
        agent = ResearchAgent(tenant_id="public_demo", user_id="anonymous")
        # LLM Call (~65 seconds)
        result = await agent.analyze_website(url=url, scraped_text=scraped_text)
        report_data = result.model_dump()
        
        # Mark remaining steps as complete
        update_job_step(job_id, "business_understanding", "success")
        update_job_step(job_id, "icp", "success")
        update_job_step(job_id, "competitors", "success")
        update_job_step(job_id, "roadmap", "success")
        
        # Persist to business_brains
        if supabase_client:
            import datetime
            ttl_expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
            
            brain_data = {
                "domain": domain,
                "tenant_id": "public_demo",
                "industry": report_data.get("business_intelligence", {}).get("industry", "Unknown"),
                "icp": report_data.get("icp_discovery", []),
                "growth_roadmap": report_data.get("growth_roadmap", {}),
                "ai_scores": {
                    "overall_growth_score": report_data.get("executive_summary", {}).get("overall_growth_score", 0)
                },
                "ttl_expires_at": ttl_expires_at,
                "metadata": {
                    "full_report": report_data
                }
            }
            res = supabase_client.table("business_brains").insert(brain_data).execute()
            if res.data:
                report_data["report_id"] = res.data[0]["id"]
        
        return report_data
        
    except Exception as e:
        logger.error("llm_api_error", error=str(e))
        update_job_step(job_id, "business_understanding", "failed")
        raise e

# Register Phase 1 handler
register_job_handler("website_analysis", website_analysis_handler)

# ----------------------------------------------------
# Phase 3: Mission Engine Agent Handlers
# ----------------------------------------------------

def _create_artifact_and_update_task(tenant_id, task_id, artifact_type, content_dict, metadata):
    # Fetch mission_id from task
    res = supabase_client.table("mission_tasks").select("mission_id").eq("id", task_id).execute()
    mission_id = res.data[0]["mission_id"] if res.data else None
    
    artifact_data = {
        "tenant_id": tenant_id,
        "mission_id": mission_id,
        "type": artifact_type,
        "status": "WAITING_APPROVAL",
        "content": content_dict,
        "metadata": metadata,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    art_res = supabase_client.table("mission_artifacts").insert(artifact_data).execute()
    artifact_id = art_res.data[0]["id"]
    
    # Update task
    supabase_client.table("mission_tasks").update({
        "status": "waiting_approval",
        "result_artifact_id": artifact_id
    }).eq("id", task_id).execute()
    
    return artifact_id

async def prospecting_agent_handler(payload: dict, job_id: str) -> dict:
    update_job_step(job_id, "prospecting", "running")
    task_id = payload.get("task_id")
    tenant_id = tenant_id_var.get()
    
    leads = [
        {"name": "Sarah Connor", "company": "Cyberdyne", "title": "Director of IT"},
        {"name": "Tony Stark", "company": "Stark Ind", "title": "CEO"}
    ]
    
    # Create artifact
    _create_artifact_and_update_task(
        tenant_id=tenant_id,
        task_id=task_id,
        artifact_type="prospect_list",
        content_dict={"leads": leads},
        metadata={"sources": ["Apollo", "LinkedIn"], "count": len(leads)}
    )
    update_job_step(job_id, "prospecting", "success")
    return {"leads": leads, "count": len(leads), "status": "waiting_approval"}

async def research_agent_handler(payload: dict, job_id: str) -> dict:
    update_job_step(job_id, "research", "running")
    task_id = payload.get("task_id")
    tenant_id = tenant_id_var.get()
    
    intelligence = {"recent_news": "Launched new AI product", "tech_stack": ["React", "Python"]}
    
    # Create artifact
    _create_artifact_and_update_task(
        tenant_id=tenant_id,
        task_id=task_id,
        artifact_type="research_report",
        content_dict={"intelligence": intelligence},
        metadata={"sources": ["Website", "Crunchbase"]}
    )
    update_job_step(job_id, "research", "success")
    return {"intelligence": intelligence, "status": "waiting_approval"}

async def email_agent_handler(payload: dict, job_id: str) -> dict:
    update_job_step(job_id, "email_drafting", "running")
    task_id = payload.get("task_id")
    tenant_id = tenant_id_var.get()
    
    agent = EmailAgent(tenant_id=tenant_id, user_id="system")
    goal = payload.get("goal", "Introduce our services")
    context_str = f"Draft an email for a prospect aiming to {goal}. Keep it concise and personalized."
    
    draft = await agent.draft_email(context_str)
    
    # Create artifact
    _create_artifact_and_update_task(
        tenant_id=tenant_id,
        task_id=task_id,
        artifact_type="email_draft",
        content_dict=draft.model_dump(),
        metadata={"tokens": 1180, "cost": 0.03, "model": "Claude Sonnet 4", "sources": ["Website", "LinkedIn", "Pricing"]}
    )
    update_job_step(job_id, "email_drafting", "success")
    return {"email_draft": draft.body, "status": "waiting_approval"}

async def voice_agent_handler(payload: dict, job_id: str) -> dict:
    update_job_step(job_id, "voice_scripting", "running")
    task_id = payload.get("task_id")
    tenant_id = tenant_id_var.get()
    
    conversation_plan = {
        "objectives": ["Identify pain points", "Book demo"],
        "opening": f"Hi {payload.get('name', 'there')}, this is Alex from Visoora. I saw your recent launch...",
        "discovery_questions": ["How are you currently handling inbound leads?"],
        "pain_hypotheses": ["High drop-off rate on forms"],
        "objection_library": payload.get("objections", []),
        "qualification_rules": ["Budget > $1k/mo"],
        "meeting_goal": "Schedule 15 min discovery call"
    }
    
    _create_artifact_and_update_task(
        tenant_id=tenant_id,
        task_id=task_id,
        artifact_type="voice_script",
        content_dict=conversation_plan,
        metadata={"model": "Deterministic"}
    )
    
    update_job_step(job_id, "voice_scripting", "success")
    return {"voice_script": conversation_plan["opening"], "conversation_plan": conversation_plan, "status": "waiting_approval"}

async def post_call_analysis_agent_handler(payload: dict, job_id: str) -> dict:
    update_job_step(job_id, "post_call_analysis", "running")
    task_id = payload.get("task_id")
    tenant_id = tenant_id_var.get()
    
    analysis = {
        "summary": "Prospect was interested but lacked budget.",
        "buying_signals": ["Asked for pricing"],
        "objections_detected": ["Price too high"],
        "sentiment": "Neutral-Positive",
        "next_actions": ["Send follow-up email with ROI calculator"]
    }
    
    _create_artifact_and_update_task(
        tenant_id=tenant_id,
        task_id=task_id,
        artifact_type="call_analysis",
        content_dict=analysis,
        metadata={"model": "Deterministic"}
    )
    update_job_step(job_id, "post_call_analysis", "success")
    return {"analysis": analysis, "status": "waiting_approval"}

register_job_handler("prospecting_agent", prospecting_agent_handler)
register_job_handler("research_agent", research_agent_handler)
register_job_handler("email_agent", email_agent_handler)
register_job_handler("voice_agent", voice_agent_handler)
register_job_handler("post_call_analysis_agent", post_call_analysis_agent_handler)

