from typing import Any, Dict, List, Optional
import uuid
import time
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from security.rbac import RoleChecker, UserPrincipal
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
)
from sales_employee.mailbox_manager import (
    list_mailboxes,
    connect_mailbox,
    set_default_mailbox,
    disconnect_mailbox,
    verify_mailbox,
    get_default_mailbox,
)
from sales_employee.followup_engine import ai_followup_engine
from sales_employee.email_generator import ai_email_generator
from sales_employee.email_timeline import get_or_create_thread, add_message_to_thread
from sales_employee.delivery_tracker import track_delivery_event, track_open_event, track_reply_event

sales_employee_router = APIRouter(
    prefix="/api/v1/sales-employee",
    tags=["AI Sales Employee"],
    dependencies=[Depends(RoleChecker(["agent", "admin"]))],
)


def tenant_from_header(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> str:
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
    return ai_email_generator.generate_followup(tenant_id, lead["agent_id"], lead, history)


@sales_employee_router.post("/leads/{lead_id}/emails/send")
async def send_email(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    history = history_service.list_for_lead(tenant_id, lead_id)
    
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
    
    # Generate draft with subject aligning with the thread
    draft = ai_email_generator.generate_followup(
        tenant_id=tenant_id,
        agent_id=lead["agent_id"],
        lead=lead,
        history=history,
        original_subject=thread.get("subject"),
    )
    
    if mailbox:
        # Route dispatch through tenant's verified mailbox
        from sales_employee.email_provider import send_via_mailbox
        result = await send_via_mailbox(
            mailbox=mailbox,
            to_email=lead["email"],
            subject=draft.subject,
            body=draft.body,
            prev_msg_id=prev_msg_id,
        )
    else:
        # Fallback to SendGrid default sender address for testing/dev environments
        result = await delivery_adapter.send(lead["email"], draft.subject, draft.body)
        
    msg_id = result.get("message_id", f"msg_{uuid.uuid4()}")
    add_message_to_thread(tenant_id, thread["id"], msg_id)
    
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
async def sendgrid_events(events: List[Dict[str, Any]], tenant_id: str = Depends(tenant_from_header)):
    written = []
    for event in events:
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
async def inbound_reply(payload: Dict[str, Any], tenant_id: str = Depends(tenant_from_header)):
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


