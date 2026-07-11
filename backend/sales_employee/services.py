import datetime
import hashlib
import html
import io
import json
import os
import re
import uuid
import zipfile
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
import structlog
from pydantic import BaseModel, Field, field_validator

from crm.auto_advance import _load_local_json, _save_local_json
from server.storage_manager import supabase_admin_client as supabase_client

logger = structlog.get_logger("visoora_sales_employee")


def utc_now() -> str:
    return datetime.datetime.utcnow().isoformat()


def require_tenant_id(tenant_id: str) -> str:
    if not tenant_id or tenant_id in {"default_tenant", "default_shared_tenant"}:
        raise ValueError("tenant_id is required and may not be a default placeholder.")
    return tenant_id


def normalize_domain(value: str) -> str:
    if not value:
        return ""
    candidate = value.strip().lower()
    if "@" in candidate:
        candidate = candidate.split("@", 1)[1]
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    return host.removeprefix("www.").split("/")[0]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]{3,}", text.lower())


def embed_text(text: str, dimensions: int = 32) -> List[float]:
    vector = [0.0] * dimensions
    for token, count in Counter(tokenize(text)).items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = digest[0] % dimensions
        vector[index] += float(count)
    magnitude = sum(v * v for v in vector) ** 0.5
    if not magnitude:
        return vector
    return [round(v / magnitude, 6) for v in vector]


def similarity(left: List[float], right: List[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        chunks.append(cleaned[start:start + size].strip())
        if start + size >= len(cleaned):
            break
        start += size - overlap
    return chunks


def extract_document_text(filename: str, content: bytes) -> str:
    suffix = os.path.splitext(filename.lower())[1]
    if suffix == ".txt":
        return content.decode("utf-8", errors="ignore")
    if suffix == ".docx":
        with zipfile.ZipFile(io.BytesIO(content)) as package:
            xml = package.read("word/document.xml").decode("utf-8", errors="ignore")
        return re.sub(r"<[^>]+>", " ", xml)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"Unable to parse PDF: {exc}") from exc
    raise ValueError("Unsupported knowledge source. Use PDF, DOCX, or TXT.")


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    persona_config: Dict[str, Any] = Field(default_factory=dict)


class LeadCreate(BaseModel):
    agent_id: str
    name: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    website: str = Field(..., min_length=3)
    email: str
    phone: str
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("Invalid email format.")
        return value

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str) -> str:
        if not re.match(r"^\+[1-9]\d{7,17}$", value):
            raise ValueError("Phone must be E.164 formatted.")
        return value


class StrategyDecision(BaseModel):
    action: str
    wait_hours: int = 0
    reason: str
    should_send: bool = False


class EmailDraft(BaseModel):
    subject: str
    body: str
    personalization_notes: List[str]


class LocalStore:
    table_files = {
        "agents": "sales_agents.json",
        "agent_knowledge_chunks": "sales_agent_knowledge_chunks.json",
        "leads": "sales_leads.json",
        "interaction_history": "interaction_history.json",
        "outreach_decisions": "outreach_decisions.json",
        "mailboxes": "connected_mailboxes.json",
        "mailbox_verifications": "mailbox_verifications.json",
        "email_threads": "email_threads.json",
        "followup_plans": "followup_plans.json",
        "delivery_events": "delivery_events.json",
        "open_events": "open_events.json",
        "reply_events": "reply_events.json",
        "timeline_events": "timeline_events.json",
        "reasoning_logs": "reasoning_logs.json",
        "communication_history": "communication_history.json",
        "next_scheduled_decisions": "next_scheduled_decisions.json",
    }

    def list(self, table: str, tenant_id: str, **filters: Any) -> List[Dict[str, Any]]:
        require_tenant_id(tenant_id)
        rows = _load_local_json(self.table_files[table])
        result = [r for r in rows if r.get("tenant_id") == tenant_id]
        for key, value in filters.items():
            result = [r for r in result if r.get(key) == value]
        return result

    def insert(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        require_tenant_id(payload.get("tenant_id", ""))
        payload.setdefault("id", str(uuid.uuid4()))
        payload.setdefault("created_at", utc_now())
        payload.setdefault("updated_at", utc_now())
        if supabase_client:
            try:
                res = supabase_client.table(table).insert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as exc:
                logger.error("sales_employee_supabase_insert_failed", table=table, error=str(exc))
        rows = _load_local_json(self.table_files[table])
        rows.append(payload)
        _save_local_json(self.table_files[table], rows)
        return payload

    def update(self, table: str, tenant_id: str, row_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        require_tenant_id(tenant_id)
        updates["updated_at"] = utc_now()
        if supabase_client:
            try:
                res = supabase_client.table(table).update(updates).eq("tenant_id", tenant_id).eq("id", row_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as exc:
                logger.error("sales_employee_supabase_update_failed", table=table, error=str(exc))
        rows = _load_local_json(self.table_files[table])
        for row in rows:
            if row.get("tenant_id") == tenant_id and row.get("id") == row_id:
                row.update(updates)
                _save_local_json(self.table_files[table], rows)
                return row
        raise KeyError(f"{table} row not found.")


store = LocalStore()


class AgentKnowledgeService:
    def create_agent(self, tenant_id: str, payload: AgentCreate) -> Dict[str, Any]:
        require_tenant_id(tenant_id)
        persona = dict(payload.persona_config)
        return store.insert("agents", {
            "tenant_id": tenant_id,
            "name": payload.name,
            "persona_config": persona,
        })

    def get_agent(self, tenant_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        rows = store.list("agents", tenant_id, id=agent_id)
        return rows[0] if rows else None

    def ingest_text(self, tenant_id: str, agent_id: str, source_file: str, text: str) -> List[Dict[str, Any]]:
        require_tenant_id(tenant_id)
        if not self.get_agent(tenant_id, agent_id):
            raise KeyError("Agent not found.")
        records = []
        for chunk in chunk_text(text):
            records.append(store.insert("agent_knowledge_chunks", {
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "source_file": source_file,
                "chunk_text": chunk,
                "embedding_vector": embed_text(chunk),
            }))
        if not records:
            raise ValueError("Knowledge source had no extractable text.")
        return records

    async def ingest_website(self, tenant_id: str, agent_id: str, url: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url if "://" in url else f"https://{url}")
            response.raise_for_status()
        text = re.sub(r"<(script|style).*?</\1>", " ", response.text, flags=re.I | re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        return self.ingest_text(tenant_id, agent_id, url, text)

    def retrieve(self, tenant_id: str, agent_id: str, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        query_vector = embed_text(query)
        rows = store.list("agent_knowledge_chunks", tenant_id, agent_id=agent_id)
        scored = [(similarity(query_vector, row.get("embedding_vector", [])), row) for row in rows]
        return [row for score, row in sorted(scored, key=lambda item: item[0], reverse=True)[:limit] if score > 0]

    def build_persona_context(self, tenant_id: str, agent_id: str, query: str = "") -> Dict[str, Any]:
        agent = self.get_agent(tenant_id, agent_id)
        if not agent:
            return {}
        chunks = self.retrieve(tenant_id, agent_id, query or agent.get("name", ""), limit=5)
        return {
            "agent_id": agent_id,
            "persona_config": agent.get("persona_config", {}),
            "knowledge_context": "\n".join(chunk["chunk_text"] for chunk in chunks),
        }


knowledge_service = AgentKnowledgeService()


class LeadResearchService:
    async def research(self, tenant_id: str, lead: Dict[str, Any]) -> Dict[str, Any]:
        require_tenant_id(tenant_id)
        website = lead.get("website", "")
        email_domain = normalize_domain(lead.get("email", ""))
        website_domain = normalize_domain(website)
        mismatches = []
        if email_domain and website_domain and email_domain != website_domain:
            mismatches.append(f"email domain {email_domain} differs from website domain {website_domain}")

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                response = await client.get(website if "://" in website else f"https://{website}")
                response.raise_for_status()
            page_text = html.unescape(re.sub(r"<[^>]+>", " ", response.text))
            words = tokenize(page_text)
            confidence = 0.75 if words else 0.2
            summary = " ".join(page_text.split()[:55])
            brief = {
                "company_summary": summary,
                "likely_pain_points": ["manual prospecting", "slow follow-up", "pipeline consistency"],
                "personalization_hooks": [lead.get("company_name", ""), website_domain],
                "domain_mismatches": mismatches,
            }
        except Exception as exc:
            confidence = 0.0
            brief = {
                "company_summary": "",
                "likely_pain_points": [],
                "personalization_hooks": [],
                "domain_mismatches": mismatches,
                "error": str(exc),
            }

        needs_review = confidence < 0.5
        return {
            "research_brief": brief,
            "research_confidence": confidence,
            "needs_review": needs_review,
        }


research_service = LeadResearchService()


class InteractionHistoryService:
    def add(self, tenant_id: str, lead_id: str, channel: str, direction: str, status: str, content_ref: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        require_tenant_id(tenant_id)
        return store.insert("interaction_history", {
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "channel": channel,
            "direction": direction,
            "content_ref": content_ref,
            "status": status,
            "metadata": metadata or {},
        })

    def list_for_lead(self, tenant_id: str, lead_id: str) -> List[Dict[str, Any]]:
        rows = store.list("interaction_history", tenant_id, lead_id=lead_id)
        return sorted(rows, key=lambda row: row.get("created_at", ""))


history_service = InteractionHistoryService()


class OutreachStrategyEngine:
    stop_after_touches = 5

    def decide_next_action(self, lead: Dict[str, Any], history: List[Dict[str, Any]], agent_config: Dict[str, Any]) -> StrategyDecision:
        if lead.get("needs_review"):
            return StrategyDecision(action="escalate_to_human", reason="Lead research needs review before automated outreach.")

        replies = [h for h in history if h.get("channel") == "email" and h.get("direction") == "inbound"]
        if replies:
            return StrategyDecision(action="escalate_to_human", reason="Lead replied; human review required before next automated touch.")

        touches = [h for h in history if h.get("direction") == "outbound" and h.get("channel") in {"call", "email"}]
        if len(touches) >= self.stop_after_touches:
            return StrategyDecision(action="mark_no_response_stop", reason=f"{len(touches)} outbound touches reached the no-response stop threshold.")

        opened = any(h.get("status") == "opened" for h in history)
        if opened:
            return StrategyDecision(action="retry_call", reason="Email was opened; calling is now a higher intent next step.", should_send=False)

        last = history[-1] if history else None
        if not last:
            return StrategyDecision(action="send_email_now", reason="No prior touches; start with researched personalized email.", should_send=True)
        if last.get("channel") == "call" and last.get("status") in {"no-answer", "voicemail"}:
            return StrategyDecision(action="send_email_referencing_prior_call", reason="Prior call did not connect; email should reference the attempted call.", should_send=True)
        if last.get("channel") == "email" and last.get("status") in {"sent", "delivered"}:
            return StrategyDecision(action="wait", wait_hours=48, reason="Recent email has no engagement signal yet; wait before another touch.")
        return StrategyDecision(action="call_now", reason="No blocking review, reply, or wait state; call is the next useful touch.")

    def log_decision(self, tenant_id: str, lead_id: str, decision: StrategyDecision) -> Dict[str, Any]:
        return store.insert("outreach_decisions", {
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "decision": decision.model_dump(),
            "reason": decision.reason,
        })


strategy_engine = OutreachStrategyEngine()


class EmailGenerationService:
    def generate(self, tenant_id: str, agent_id: str, lead: Dict[str, Any], history: List[Dict[str, Any]]) -> EmailDraft:
        context = knowledge_service.build_persona_context(tenant_id, agent_id, lead.get("company_name", ""))
        persona = context.get("persona_config", {})
        brief = lead.get("research_brief") or {}
        hooks = brief.get("personalization_hooks") or [lead.get("company_name", "")]
        tone = persona.get("tone", "consultative")
        value_prop = persona.get("value_proposition") or persona.get("business_description") or "help sales teams follow up faster"
        prior_call = any(h.get("channel") == "call" for h in history)
        subject = f"Idea for {lead.get('company_name')}"
        opener = f"Hi {lead.get('name')},"
        reference = "I tried calling earlier and wanted to send a cleaner note." if prior_call else f"I was looking at {hooks[0]} and thought this may be relevant."
        knowledge_line = context.get("knowledge_context", "").split(".")[0][:180]
        body = (
            f"{opener}\n\n"
            f"{reference} We usually work in a {tone} way around one problem: {value_prop}.\n\n"
            f"For {lead.get('company_name')}, the useful angle looks like {', '.join(str(h) for h in hooks if h)[:160]}. "
            f"{knowledge_line}.\n\n"
            "Would it be worth a short conversation this week?\n\n"
            f"Best,\n{persona.get('agent_name', 'Alex')}"
        )
        return EmailDraft(subject=subject, body=body, personalization_notes=[str(h) for h in hooks if h])


email_generation_service = EmailGenerationService()


class SendGridDeliveryAdapter:
    def __init__(self) -> None:
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "")

    async def send(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        if not self.api_key or not self.from_email:
            raise RuntimeError("SendGrid credentials missing: set SENDGRID_API_KEY and SENDGRID_FROM_EMAIL.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.from_email},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
            )
            if response.status_code >= 300:
                raise RuntimeError(f"SendGrid send failed with {response.status_code}: {response.text[:300]}")
            return {"provider": "sendgrid", "status_code": response.status_code, "message_id": response.headers.get("X-Message-Id", "")}


delivery_adapter = SendGridDeliveryAdapter()


async def create_lead_and_research(tenant_id: str, lead: LeadCreate) -> Dict[str, Any]:
    require_tenant_id(tenant_id)
    payload = lead.model_dump()
    payload["tenant_id"] = tenant_id
    payload.update(await research_service.research(tenant_id, payload))
    return store.insert("leads", payload)
