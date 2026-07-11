import uuid
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field
import structlog
from server.storage_manager import get_scoped_supabase_client
from security.rbac import get_current_user, UserPrincipal
from security.config import settings
from crm.auto_advance import _load_local_json, _save_local_json

logger = structlog.get_logger("visoora_jobs_api")

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs Queue"])

class JobCreate(BaseModel):
    job_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class JobResponse(BaseModel):
    id: str
    tenant_id: str
    job_type: str
    status: str
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    user: UserPrincipal = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Enqueues a new background job under the tenant context."""
    tenant_id = x_tenant_id or user.tenant_id
    
    # Enforce RLS tenant matching
    if not user.is_m2m and tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Tenant context mismatch."
        )

    job_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    
    job_data = {
        "id": job_id,
        "tenant_id": tenant_id,
        "job_type": payload.job_type,
        "status": "queued",
        "payload": payload.payload,
        "result": {},
        "error": None,
        "created_at": now,
        "updated_at": now
    }

    scoped_db = get_scoped_supabase_client(user.raw_token)
    if scoped_db:
        try:
            res = scoped_db.table("background_jobs").insert(job_data).execute()
            if res.data:
                logger.info("job_enqueued_db", job_id=job_id, job_type=payload.job_type, tenant_id=tenant_id)
                return res.data[0]
        except Exception as e:
            logger.error("api_enqueue_job_db_failed", error=str(e))
            # Fall back to local only in dev/test
            if user.tenant_id == "phase_a_tenant" or settings.app_env in ("development", "test"):
                pass
            else:
                raise HTTPException(status_code=500, detail="Database error during job queue write.")

    # Local Fallback
    logger.info("job_enqueued_local", job_id=job_id, job_type=payload.job_type, tenant_id=tenant_id)
    local_jobs = _load_local_json("local_background_jobs.json")
    local_jobs.append(job_data)
    _save_local_json("local_background_jobs.json", local_jobs)
    return job_data

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: UserPrincipal = Depends(get_current_user)
):
    """Retrieves current job status, results, and error details."""
    scoped_db = get_scoped_supabase_client(user.raw_token)
    if scoped_db:
        try:
            res = scoped_db.table("background_jobs")\
                .select("*")\
                .eq("id", job_id)\
                .execute()
            if res.data:
                job = res.data[0]
                # Enforce RLS tenant matching
                if not user.is_m2m and job["tenant_id"] != user.tenant_id:
                    raise HTTPException(status_code=403, detail="Forbidden: Cross-tenant data access blocked.")
                return job
            raise HTTPException(status_code=404, detail="Job not found.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("api_get_job_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database query error.")

    # Local Fallback
    local_jobs = _load_local_json("local_background_jobs.json")
    for j in local_jobs:
        if j["id"] == job_id:
            if not user.is_m2m and j["tenant_id"] != user.tenant_id:
                raise HTTPException(status_code=403, detail="Forbidden: Cross-tenant data access blocked.")
            return j
            
    raise HTTPException(status_code=404, detail="Job not found in local fallback.")

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    user: UserPrincipal = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Lists all background jobs under the tenant context."""
    tenant_id = x_tenant_id or user.tenant_id
    
    # Enforce RLS tenant matching
    if not user.is_m2m and tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Tenant context mismatch."
        )

    scoped_db = get_scoped_supabase_client(user.raw_token)
    if scoped_db:
        try:
            res = scoped_db.table("background_jobs")\
                .select("*")\
                .eq("tenant_id", user.tenant_id)\
                .order("created_at", desc=True)\
                .execute()
            return res.data or []
        except Exception as e:
            logger.error("api_list_jobs_db_failed", error=str(e))
            if settings.app_env not in ("development", "test"):
                raise HTTPException(status_code=500, detail="Database query error.")

    # Local Fallback
    local_jobs = _load_local_json("local_background_jobs.json")
    return [j for j in local_jobs if j.get("tenant_id") == tenant_id]
