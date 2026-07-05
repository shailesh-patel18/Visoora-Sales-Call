from typing import Any, Dict, List, Optional
import os
import uuid
import time
import json
import datetime
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
import structlog

from security.rbac import RoleChecker, UserPrincipal, get_current_user
from sales_employee.services import (
    AgentCreate,
    LeadCreate,
    create_lead_and_research,
    delivery_adapter,
    extract_document_text,
    history_service,
    knowledge_service,
    require_tenant_id,
    store,
    utc_now,
)
from sales_employee.mailbox_manager import (
    list_mailboxes,
    connect_mailbox,
    set_default_mailbox,
    disconnect_mailbox,
    verify_mailbox,
    get_default_mailbox,
    refresh_oauth_token_if_needed,
    enforce_mailbox_rate_limits,
)
from sales_employee.followup_engine import ai_followup_engine
from sales_employee.email_generator import ai_email_generator
from sales_employee.email_timeline import get_or_create_thread, add_message_to_thread
from sales_employee.delivery_tracker import (
    track_delivery_event,
    track_open_event,
    track_reply_event,
    verify_sendgrid_signature,
    check_replay_and_deduplicate,
)
from server.storage_manager import supabase_client

logger = structlog.get_logger("visoora_sales_employee_router")

sales_employee_router = APIRouter(
    prefix="/api/v1/sales-employee",
    tags=["AI Sales Employee"],
    dependencies=[Depends(RoleChecker(["agent", "admin"]))],
)

# Separate public router for unsubscribe links (no RBAC check)
public_sales_router = APIRouter(
    prefix="/api/v1/sales-employee",
    tags=["AI Sales Employee Public"],
)


def tenant_from_header(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    user: UserPrincipal = Depends(get_current_user)
) -> str:
    if not x_tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID header is required."
        )

    # Enforce isolation for human users:
    if not user.is_m2m and x_tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Tenant context mismatch. Token tenant '{user.tenant_id}' does not match requested tenant '{x_tenant_id}'."
        )

    try:
        return require_tenant_id(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class MailboxConnectPayload(BaseModel):
    email: str = Field(..., description="Email address for connected sending identity")
    provider: str = Field(..., description="Email provider: gmail, outlook, smtp, sendgrid, resend, ses, postmark")
    connection_config: Dict[str, Any] = Field(..., description="Credentials config")
    is_default: bool = False


# ====================================================
# CONNECTED MAILBOXES MANAGEMENT
# ====================================================
@sales_employee_router.get("/mailboxes")
async def api_list_mailboxes(tenant_id: str = Depends(tenant_from_header)):
    return list_mailboxes(tenant_id)


@sales_employee_router.post("/mailboxes", status_code=status.HTTP_201_CREATED)
async def api_connect_mailbox(payload: MailboxConnectPayload, tenant_id: str = Depends(tenant_from_header)):
    try:
        return connect_mailbox(
            tenant_id=tenant_id,
            email=payload.email,
            provider=payload.provider,
            connection_config=payload.connection_config,
            is_default=payload.is_default,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@sales_employee_router.put("/mailboxes/{mailbox_id}/default")
async def api_set_default_mailbox(mailbox_id: str, tenant_id: str = Depends(tenant_from_header)):
    try:
        return set_default_mailbox(tenant_id, mailbox_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@sales_employee_router.delete("/mailboxes/{mailbox_id}")
async def api_disconnect_mailbox(mailbox_id: str, tenant_id: str = Depends(tenant_from_header)):
    success = disconnect_mailbox(tenant_id, mailbox_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mailbox not found.")
    return {"success": True}


# ====================================================
# OAUTH HANDLERS
# ====================================================
@sales_employee_router.get("/mailboxes/oauth/authorize")
async def oauth_authorize(provider: str, tenant_id: str = Depends(tenant_from_header)):
    # Returns redirect consent URL. Fallbacks to mock authorization in development/testing.
    redirect_uri = f"http://localhost:8000/api/v1/sales-employee/mailboxes/oauth/callback?provider={provider}&tenant_id={tenant_id}"
    return {"url": f"https://visoora-mock-auth.com/oauth/authorize?redirect_uri={redirect_uri}"}


@sales_employee_router.get("/mailboxes/oauth/callback")
async def oauth_callback(code: str = "mock_code", provider: str = "gmail", tenant_id: str = "acme_tenant"):
    # Receives callback authorization code, obtains credentials, connects mailbox, and redirects back to Settings
    email = f"user_{tenant_id[:5]}@{provider}.com"
    connection_config = {
        "access_token": f"mock_access_token_{code}",
        "refresh_token": f"mock_refresh_token_{code}",
        "expiry": int(time.time()) + 3600,
    }
    connect_mailbox(tenant_id, email, provider, connection_config, is_default=True)
    # Redirect to Next.js frontend settings page
    return RedirectResponse(url="http://localhost:3000/settings/email?connected=true")


# ====================================================
# SALES AGENT & KNOWLEDGE MANAGEMENT
# ====================================================
@sales_employee_router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, tenant_id: str = Depends(tenant_from_header)):
    return knowledge_service.create_agent(tenant_id, payload)


@sales_employee_router.get("/agents")
async def list_agents(tenant_id: str = Depends(tenant_from_header)):
    return store.list("agents", tenant_id)


@sales_employee_router.post("/agents/{agent_id}/knowledge/text", status_code=status.HTTP_201_CREATED)
async def ingest_text(agent_id: str, payload: Dict[str, str], tenant_id: str = Depends(tenant_from_header)):
    try:
        return knowledge_service.ingest_text(tenant_id, agent_id, payload.get("source_file", "manual.txt"), payload.get("text", ""))
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@sales_employee_router.post("/agents/{agent_id}/knowledge/file", status_code=status.HTTP_201_CREATED)
async def ingest_file(agent_id: str, file: UploadFile = File(...), tenant_id: str = Depends(tenant_from_header)):
    try:
        content = await file.read()
        text = extract_document_text(file.filename or "upload.txt", content)
        return knowledge_service.ingest_text(tenant_id, agent_id, file.filename or "upload", text)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@sales_employee_router.post("/agents/{agent_id}/knowledge/website", status_code=status.HTTP_201_CREATED)
async def ingest_website(agent_id: str, payload: Dict[str, str], tenant_id: str = Depends(tenant_from_header)):
    try:
        return await knowledge_service.ingest_website(tenant_id, agent_id, payload["url"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Website ingestion failed: {exc}") from exc


@sales_employee_router.get("/agents/{agent_id}/knowledge/search")
async def search_knowledge(agent_id: str, q: str, tenant_id: str = Depends(tenant_from_header)):
    return knowledge_service.retrieve(tenant_id, agent_id, q)


# ====================================================
# LEADS & CRM PIPELINE OUTREACH
# ====================================================
@sales_employee_router.post("/leads", status_code=status.HTTP_201_CREATED)
async def create_lead(payload: LeadCreate, tenant_id: str = Depends(tenant_from_header)):
    try:
        return await create_lead_and_research(tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@sales_employee_router.get("/leads")
async def list_leads(tenant_id: str = Depends(tenant_from_header)):
    return store.list("leads", tenant_id)


@sales_employee_router.post("/leads/{lead_id}/decide")
async def decide_next_action(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    history = history_service.list_for_lead(tenant_id, lead_id)
    agent = knowledge_service.get_agent(tenant_id, lead["agent_id"]) or {}
    
    # Route reasoning logic through the AIFollowupEngine
    decision = ai_followup_engine.decide_next_action(lead, history, agent.get("persona_config", {}))
    ai_followup_engine.log_reasoning(tenant_id, lead_id, {"lead": lead, "history": history}, decision)
    return decision


@sales_employee_router.post("/leads/{lead_id}/emails/draft")
async def draft_email(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    history = history_service.list_for_lead(tenant_id, lead_id)
    
    # Use configure domain base URL
    public_base_url = os.getenv("SERVER_PUBLIC_DOMAIN", "http://localhost:8000")
    return ai_email_generator.generate_followup(tenant_id, lead["agent_id"], lead, history, public_base_url=public_base_url)


@sales_employee_router.post("/leads/{lead_id}/emails/send")
async def send_email(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    
    # Deterministic Guardrail 1: Unsubscribe / Stopped status check
    follow_up_status = lead.get("follow_up_status", "").lower()
    lead_status = lead.get("status", "").lower()
    if follow_up_status == "stopped" or lead_status == "unsubscribed" or follow_up_status == "unsubscribed":
        raise HTTPException(status_code=400, detail="Outreach blocked: Prospect has unsubscribed.")
        
    # Deterministic Guardrail 2: Stop-on-company-reply check
    company_name = lead.get("company_name", "")
    if company_name:
        try:
            all_leads = store.list("leads", tenant_id)
        except Exception:
            all_leads = []
        company_leads = [l for l in all_leads if l.get("company_name", "").lower() == company_name.lower()]
        for cl in company_leads:
            try:
                cl_history = history_service.list_for_lead(tenant_id, cl["id"])
            except Exception:
                cl_history = []
            replied = any(h.get("channel") == "email" and h.get("direction") == "inbound" for h in cl_history)
            if replied:
                raise HTTPException(
                    status_code=400,
                    detail="Outreach blocked: another contact from the same company has replied."
                )
                
    history = history_service.list_for_lead(tenant_id, lead_id)
    
    # Deterministic Guardrail 3: Outbound cap limit (5 touches)
    outbound_touches = [h for h in history if h.get("direction") == "outbound" and h.get("channel") in {"call", "email"}]
    if len(outbound_touches) >= 5:
        raise HTTPException(status_code=400, detail="Outbound touch cap (5) reached. Outreach is blocked.")
        
    # Assert outreach next best action
    decision = ai_followup_engine.decide_next_action(lead, history, {})
    ai_followup_engine.log_reasoning(tenant_id, lead_id, {"lead": lead, "history": history}, decision)
    
    if not decision.should_send:
        raise HTTPException(status_code=409, detail=f"Strategy engine blocked send: {decision.reason}")
        
    # Get active connected sending account
    mailbox = get_default_mailbox(tenant_id)
    
    # Threading subject alignment
    subj_root = f"Idea for {lead.get('company_name')}"
    thread = get_or_create_thread(tenant_id, lead_id, subj_root)
    
    # Retrieve previous message ID if threading
    prev_msg_id = thread.get("message_ids")[-1] if thread.get("message_ids") else None
    
    # Resolve public base URL
    public_base_url = os.getenv("SERVER_PUBLIC_DOMAIN", "http://localhost:8000")
    
    # Generate draft with subject aligning with the thread and unsubscribe links
    draft = ai_email_generator.generate_followup(
        tenant_id=tenant_id,
        agent_id=lead["agent_id"],
        lead=lead,
        history=history,
        original_subject=thread.get("subject"),
        public_base_url=public_base_url,
    )
    
    extra_headers = {
        "List-Unsubscribe": f"<{public_base_url}/api/v1/sales-employee/leads/unsubscribe?lead_id={lead_id}>"
    }
    
    if mailbox:
        # Enforce rate limits (sending gap and cap checks)
        await enforce_mailbox_rate_limits(tenant_id, mailbox["id"])
        
        # Check and auto-refresh credentials if expiring
        mailbox = await refresh_oauth_token_if_needed(tenant_id, mailbox["id"])
        
        from sales_employee.email_provider import send_via_mailbox
        try:
            result = await send_via_mailbox(
                mailbox=mailbox,
                to_email=lead["email"],
                subject=draft.subject,
                body=draft.body,
                prev_msg_id=prev_msg_id,
                extra_headers=extra_headers,
            )
        except Exception as exc:
            # Token refresh retry loop (if token expired/revoked mid-campaign)
            if "unauthorized" in str(exc).lower() or "expired" in str(exc).lower() or "401" in str(exc).lower():
                logger.info("send_email_unauthorized_token_retry", error=str(exc))
                # Attempt forced refresh once
                mailbox = await refresh_oauth_token_if_needed(tenant_id, mailbox["id"])
                try:
                    result = await send_via_mailbox(
                        mailbox=mailbox,
                        to_email=lead["email"],
                        subject=draft.subject,
                        body=draft.body,
                        prev_msg_id=prev_msg_id,
                        extra_headers=extra_headers,
                    )
                except Exception as retry_exc:
                    # Token refresh failed, escalate to human
                    store.update("leads", tenant_id, lead_id, {"needs_review": True, "follow_up_status": "escalated"})
                    history_service.add(
                        tenant_id, lead_id, "email", "outbound", "failed", "",
                        {"error": f"Mailbox credentials invalid: {retry_exc}"}
                    )
                    raise HTTPException(status_code=400, detail=f"Mailbox token refresh failed. Outbound outreach escalated to human review.")
            else:
                # Other connection failures, escalate to human
                store.update("leads", tenant_id, lead_id, {"needs_review": True, "follow_up_status": "escalated"})
                history_service.add(
                    tenant_id, lead_id, "email", "outbound", "failed", "",
                    {"error": f"Mailbox dispatch failed: {exc}"}
                )
                raise HTTPException(status_code=400, detail=f"Mailbox send failed: {exc}. Outreach escalated to human review.")
    else:
        # Fallback to SendGrid default sender address ONLY allowed for testing/development environments
        app_env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
        if app_env in ("development", "test"):
            result = await delivery_adapter.send(lead["email"], draft.subject, draft.body)
        else:
            raise HTTPException(
                status_code=400,
                detail="No connected mailbox configured for this workspace. Outbound email is blocked in production."
            )
        
    msg_id = result.get("message_id", f"msg_{uuid.uuid4()}")
    add_message_to_thread(tenant_id, thread["id"], msg_id)
    
    # Increment total touches on lead
    total_touches = lead.get("total_touches", 0) + 1
    store.update("leads", tenant_id, lead_id, {
        "total_touches": total_touches,
        "last_touch_at": utc_now(),
        "last_touch_channel": "email"
    })
    
    # Log sent outreach event in lead timeline history
    return history_service.add(
        tenant_id,
        lead_id,
        "email",
        "outbound",
        "sent",
        msg_id,
        {
            "draft": draft.model_dump(),
            "provider": result,
            "thread_id": thread["id"],
            "sender_mailbox": mailbox.get("email") if mailbox else "default_fallback",
        },
    )


# ====================================================
# DELIVERY WEBHOOK RECEIVERS
# ====================================================
@sales_employee_router.post("/webhooks/sendgrid/events")
async def sendgrid_events(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-Twilio-Email-Event-Webhook-Signature"),
    timestamp: Optional[str] = Header(None, alias="X-Twilio-Email-Event-Webhook-Timestamp"),
    tenant_id: str = Depends(tenant_from_header)
):
    body_bytes = await request.body()
    
    # 1. Verify webhook signature
    if signature and timestamp:
        if not verify_sendgrid_signature(signature, timestamp, body_bytes):
            raise HTTPException(status_code=401, detail="Invalid SendGrid webhook signature")
            
    events = json.loads(body_bytes)
    written = []
    for event in events:
        event_id = event.get("sg_event_id") or str(uuid.uuid4())
        event_timestamp = float(event.get("timestamp", time.time()))
        
        # 2. Replay and Deduplication Checks
        if not check_replay_and_deduplicate(event_id, event_timestamp):
            continue
            
        lead_id = event.get("lead_id") or event.get("custom_args", {}).get("lead_id")
        if lead_id:
            written.append(
                history_service.add(
                    tenant_id,
                    lead_id,
                    "email",
                    "outbound",
                    event.get("event", "delivered"),
                    event.get("sg_message_id", ""),
                    event,
                )
            )
    return {"accepted": len(written)}


@sales_employee_router.post("/webhooks/email/replies")
async def inbound_reply(
    payload: Dict[str, Any], 
    secret: Optional[str] = None,
    tenant_id: str = Depends(tenant_from_header)
):
    # Shared secret query verify
    expected_secret = os.getenv("WEBHOOK_SHARED_SECRET", "mock_secret")
    if secret != expected_secret and os.getenv("APP_ENV") != "test":
        raise HTTPException(status_code=401, detail="Unauthorized shared secret mismatch")
        
    event_id = payload.get("message_id") or str(uuid.uuid4())
    event_timestamp = float(payload.get("timestamp", time.time()))
    
    # Replay protection
    if not check_replay_and_deduplicate(event_id, event_timestamp):
        raise HTTPException(status_code=409, detail="Duplicate or replay webhook rejected")
        
    lead_id = payload.get("lead_id")
    if not lead_id:
        raise HTTPException(status_code=400, detail="lead_id is required.")
    return history_service.add(tenant_id, lead_id, "email", "inbound", "replied", payload.get("message_id", ""), payload)


@sales_employee_router.post("/webhooks/mailbox/test-event")
async def mailbox_test_event(
    lead_id: str,
    event_type: str,  # bounce, open, reply
    reply_body: Optional[str] = None,
    tenant_id: str = Depends(tenant_from_header),
):
    """
    Test helper receiver to simulate inbound email actions (opened, replied, bounced).
    """
    msg_id = f"test_{uuid.uuid4()}"
    if event_type == "open":
        return track_open_event(tenant_id, lead_id, msg_id, {"source": "test_hook"})
    elif event_type == "reply":
        return track_reply_event(tenant_id, lead_id, msg_id, reply_body or "Thanks for reaching out!", {"source": "test_hook"})
    elif event_type == "bounce":
        return track_delivery_event(tenant_id, lead_id, "bounced", msg_id, {"source": "test_hook"})
    else:
        return track_delivery_event(tenant_id, lead_id, "delivered", msg_id, {"source": "test_hook"})


@sales_employee_router.get("/leads/{lead_id}/timeline")
async def lead_timeline(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    return history_service.list_for_lead(tenant_id, lead_id)


# ====================================================
# PUBLIC ROUTES (No RBAC dependency)
# ====================================================
@public_sales_router.get("/leads/unsubscribe")
async def unsubscribe_lead(lead_id: str):
    """
    Public opt-out endpoint accessed by prospects via unsubscribe link.
    Sets follow_up_status = "stopped" and status = "unsubscribed".
    """
    from crm.auto_advance import _load_local_json, _save_local_json
    
    # 1. Update in local leads database file
    leads = _load_local_json("leads.json")
    found = False
    for l in leads:
        if l.get("id") == lead_id:
            l["follow_up_status"] = "stopped"
            l["status"] = "unsubscribed"
            found = True
            
            # Record unsubscribe event in timeline
            history_service.add(
                tenant_id=l.get("tenant_id", "acme_tenant"),
                lead_id=lead_id,
                channel="email",
                direction="inbound",
                status="unsubscribed",
                content_ref="unsubscribe_link",
                metadata={"unsubscribed": True}
            )
            break
            
    if found:
        _save_local_json("leads.json", leads)
        
        # 2. Update in Supabase DB if configured
        if supabase_client:
            try:
                supabase_client.table("leads").update({
                    "follow_up_status": "stopped",
                    "status": "unsubscribed"
                }).eq("id", lead_id).execute()
            except Exception as exc:
                logger.error("supabase_unsubscribe_db_write_failed", error=str(exc))
                
        # Return a premium success confirmation page
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Unsubscribed Successfully</title>
                <style>
                    body {
                        background: #0a0a0a;
                        color: #ffffff;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .container {
                        background: rgba(255, 255, 255, 0.02);
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        padding: 40px;
                        border-radius: 16px;
                        text-align: center;
                        max-width: 420px;
                        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                        backdrop-filter: blur(8px);
                    }
                    .icon {
                        font-size: 32px;
                        margin-bottom: 16px;
                        color: #10b981;
                    }
                    h1 {
                        font-size: 20px;
                        font-weight: 700;
                        margin: 0 0 12px 0;
                        letter-spacing: -0.5px;
                    }
                    p {
                        color: #888888;
                        font-size: 13px;
                        line-height: 1.6;
                        margin: 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">✓</div>
                    <h1>Outreach Discontinued</h1>
                    <p>You have been successfully unsubscribed. Visoora has permanently stopped all automated sales follow-ups for your profile.</p>
                </div>
            </body>
            </html>
        """)
        
    raise HTTPException(status_code=404, detail="Lead not found")
