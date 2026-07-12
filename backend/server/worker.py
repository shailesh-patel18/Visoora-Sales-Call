import os
import json
import datetime
import asyncio
import structlog
from typing import Dict, Any, Callable, Optional, List
from server.storage_manager import supabase_admin_client

logger = structlog.get_logger("visoora_worker")

# Shared registry for job execution functions
JOB_HANDLERS: Dict[str, Callable[[dict], Any]] = {}
worker_lock = asyncio.Lock()

def register_job_handler(job_type: str, handler: Callable[[dict], Any]):
    JOB_HANDLERS[job_type] = handler
    logger.info("job_handler_registered", job_type=job_type)

async def dummy_handler(payload: dict) -> dict:
    duration = payload.get("duration", 5)
    await asyncio.sleep(duration)
    return {"message": "Dummy job completed successfully!", "duration": duration}

register_job_handler("dummy", dummy_handler)

# Import actual job handlers to register them
try:
    import server.lead_scorer
    import server.company_research
    import server.email_generator
    import server.email_dispatcher
except ImportError as imp_err:
    logger.warn("worker_handlers_lazy_import_warning", error=str(imp_err))

async def process_next_job():
    """
    Looks for the oldest 'queued' background job, claims it atomically,
    executes its registered handler, and updates its status.
    """
    if supabase_admin_client:
        try:
            # 1. Fetch oldest queued job
            res = supabase_admin_client.table("workflow_jobs")\
                .select("*")\
                .eq("status", "queued")\
                .order("created_at", desc=False)\
                .limit(1)\
                .execute()
            
            if not res.data:
                return False
            
            job = res.data[0]
            job_id = job["id"]
            workflow_type = job["workflow_type"]
            payload = job["payload"] or {}
            tenant_id = job["tenant_id"]

            # TENANT ISOLATION GUARD: Reject jobs without a valid tenant context
            if not tenant_id or tenant_id == "":
                logger.error("job_rejected_no_tenant", job_id=job_id, workflow_type=workflow_type)
                supabase_admin_client.table("workflow_jobs")\
                    .update({"status": "failed", "error": "Missing tenant_id — rejected for safety"})\
                    .eq("id", job_id).execute()
                return False

            # Inject tenant_id into payload so handlers always have it
            payload["tenant_id"] = tenant_id

            # 2. Claim job atomically using optimistic lock
            claim_res = supabase_admin_client.table("workflow_jobs")\
                .update({
                    "status": "running",
                    "updated_at": datetime.datetime.utcnow().isoformat()
                })\
                .eq("id", job_id)\
                .eq("status", "queued")\
                .execute()
            
            if not claim_res.data:
                # Job was claimed by another worker
                return False
            
            logger.info("job_claimed_db", job_id=job_id, workflow_type=workflow_type, tenant_id=tenant_id)
            
            # Emit workflow started event
            from server.workflow_engine import emit_workflow_event
            emit_workflow_event(job_id, event_type="workflow_started")
            
            # 3. Run handler
            handler = JOB_HANDLERS.get(workflow_type)
            if not handler:
                raise ValueError(f"No job handler registered for type: '{workflow_type}'")
            
            # Setup logging variables
            from security.logging import correlation_id_var, tenant_id_var
            tenant_id_var.set(tenant_id)
            correlation_id_var.set(job_id)

            try:
                # Execute task (which can be async or sync)
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(payload, job_id=job_id)
                else:
                    result = handler(payload, job_id=job_id)
                
                # Mark as success
                supabase_admin_client.table("workflow_jobs")\
                    .update({
                        "status": "success",
                        "result_id": result.get("id") if result and isinstance(result, dict) else None,
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    })\
                    .eq("id", job_id)\
                    .execute()
                    
                emit_workflow_event(job_id, event_type="workflow_completed", payload={"result": result})
                logger.info("job_success_db", job_id=job_id, workflow_type=workflow_type)
            except Exception as handler_err:
                logger.error("job_handler_error_db", job_id=job_id, workflow_type=workflow_type, error=str(handler_err))
                emit_workflow_event(job_id, event_type="workflow_failed", payload={"error": str(handler_err)})
                supabase_admin_client.table("workflow_jobs")\
                    .update({
                        "status": "failed",
                        "error": str(handler_err),
                        "updated_at": datetime.datetime.utcnow().isoformat()
                    })\
                    .eq("id", job_id)\
                    .execute()
            return True
        except Exception as e:
            logger.error("db_worker_iteration_failed", error=str(e))
            return False
    return False

def recover_stuck_jobs():
    """Finds jobs stuck in 'running' state for > 5 minutes and resets them."""
    if not supabase_admin_client:
        return
    try:
        five_mins_ago = (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)).isoformat()
        res = supabase_admin_client.table("workflow_jobs")\
            .update({"status": "queued", "error": "Reset after being stuck in running state"})\
            .eq("status", "running")\
            .lt("updated_at", five_mins_ago)\
            .execute()
        if res.data:
            logger.info("recovered_stuck_jobs", count=len(res.data))
    except Exception as e:
        logger.error("failed_recovering_stuck_jobs", error=str(e))

async def run_worker_loop():
    """Runs a continuous background execution loop with exponential backoff (1.0s to 15.0s)."""
    logger.info("worker_loop_start", message="Visoora background job worker started.")
    poll_interval = 1.0
    last_recovery_time = datetime.datetime.utcnow()

    while True:
        try:
            # 1. Recover stuck jobs periodically (every ~1 minute)
            now = datetime.datetime.utcnow()
            if (now - last_recovery_time).total_seconds() > 60:
                recover_stuck_jobs()
                last_recovery_time = now

            # 2. Process next workflow job
            job_processed = await process_next_job()
            
            # 3. Spawn tasks whose dependencies are met
            from server.services.mission_engine import spawn_ready_tasks
            tasks_spawned = spawn_ready_tasks()
            
            # 4. Exponential backoff
            if job_processed or tasks_spawned:
                poll_interval = 1.0
            else:
                poll_interval = min(poll_interval * 1.5, 15.0)
                
        except Exception as e:
            logger.error("worker_loop_error", error=str(e))
            poll_interval = min(poll_interval * 2.0, 15.0)
            
        await asyncio.sleep(poll_interval)

async def start_background_worker():
    """Starts the background loop as an un-awaited background task."""
    asyncio.create_task(run_worker_loop())

async def enqueue_background_job(tenant_id: str, job_type: str, payload: dict) -> dict:
    """Programmatically enqueues a new background job with local file fallback."""
    import uuid
    job_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    
    job_data = {
        "id": job_id,
        "tenant_id": tenant_id,
        "workflow_type": job_type,
        "status": "queued",
        "payload": payload,
        "result": {},
        "error": None,
        "created_at": now,
        "updated_at": now
    }

    if supabase_admin_client:
        try:
            res = supabase_admin_client.table("workflow_jobs").insert(job_data).execute()
            if res.data:
                logger.info("job_enqueued_programmatic_db", job_id=job_id, workflow_type=job_type, tenant_id=tenant_id)
                return res.data[0]
        except Exception as e:
            logger.error("programmatic_enqueue_job_db_failed", error=str(e))

    # Local Fallback
    logger.info("job_enqueued_programmatic_local", job_id=job_id, job_type=job_type, tenant_id=tenant_id)
    async with worker_lock:
        local_jobs = _load_local_json("local_background_jobs.json")
        local_jobs.append(job_data)
        _save_local_json("local_background_jobs.json", local_jobs)
    return job_data
