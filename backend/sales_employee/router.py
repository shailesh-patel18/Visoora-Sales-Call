from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from security.rbac import RoleChecker, UserPrincipal
from sales_employee.services import (
    AgentCreate,
    LeadCreate,
    create_lead_and_research,
    delivery_adapter,
    email_generation_service,
    extract_document_text,
    history_service,
    knowledge_service,
    require_tenant_id,
    store,
    strategy_engine,
)

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
    decision = strategy_engine.decide_next_action(lead, history, agent.get("persona_config", {}))
    strategy_engine.log_decision(tenant_id, lead_id, decision)
    return decision


@sales_employee_router.post("/leads/{lead_id}/emails/draft")
async def draft_email(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    return email_generation_service.generate(tenant_id, lead["agent_id"], lead, history_service.list_for_lead(tenant_id, lead_id))


@sales_employee_router.post("/leads/{lead_id}/emails/send")
async def send_email(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    leads = store.list("leads", tenant_id, id=lead_id)
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found.")
    lead = leads[0]
    history = history_service.list_for_lead(tenant_id, lead_id)
    decision = strategy_engine.decide_next_action(lead, history, {})
    strategy_engine.log_decision(tenant_id, lead_id, decision)
    if not decision.should_send:
        raise HTTPException(status_code=409, detail=f"Strategy engine blocked send: {decision.reason}")
    draft = email_generation_service.generate(tenant_id, lead["agent_id"], lead, history)
    result = await delivery_adapter.send(lead["email"], draft.subject, draft.body)
    return history_service.add(tenant_id, lead_id, "email", "outbound", "sent", result.get("message_id", ""), {"draft": draft.model_dump(), "provider": result})


@sales_employee_router.post("/webhooks/sendgrid/events")
async def sendgrid_events(events: List[Dict[str, Any]], tenant_id: str = Depends(tenant_from_header)):
    written = []
    for event in events:
        lead_id = event.get("lead_id") or event.get("custom_args", {}).get("lead_id")
        if lead_id:
            written.append(history_service.add(tenant_id, lead_id, "email", "outbound", event.get("event", "delivered"), event.get("sg_message_id", ""), event))
    return {"accepted": len(written)}


@sales_employee_router.post("/webhooks/email/replies")
async def inbound_reply(payload: Dict[str, Any], tenant_id: str = Depends(tenant_from_header)):
    lead_id = payload.get("lead_id")
    if not lead_id:
        raise HTTPException(status_code=400, detail="lead_id is required.")
    return history_service.add(tenant_id, lead_id, "email", "inbound", "replied", payload.get("message_id", ""), payload)


@sales_employee_router.get("/leads/{lead_id}/timeline")
async def lead_timeline(lead_id: str, tenant_id: str = Depends(tenant_from_header)):
    return history_service.list_for_lead(tenant_id, lead_id)

