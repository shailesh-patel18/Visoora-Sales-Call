import os
import json
import httpx
import structlog
from typing import Dict, Any
from server.storage_manager import supabase_client
from pipeline.states import get_tenant_config
from server.worker import register_job_handler
from crm.auto_advance import _load_local_json, _save_local_json
from ai_platform.agents.email_agent import EmailAgent

logger = structlog.get_logger("visoora_email_generator")

async def generate_email_job_handler(payload: dict) -> dict:
    """
    Background job handler for generating cold email outreach.
    Payload parameters:
      - tenant_id: str (required)
      - contact_id: str (required)
    """
    tenant_id = payload.get("tenant_id")
    contact_id = payload.get("contact_id")

    if not tenant_id or not contact_id:
        raise ValueError("Missing required parameters: 'tenant_id' and 'contact_id'")

    logger.info("email_generation_job_start", tenant_id=tenant_id, contact_id=contact_id)

    try:
        email_data = await run_email_generation(contact_id, tenant_id)
        return {"contact_id": contact_id, "status": "success", "email": email_data}
    except Exception as err:
        logger.error("email_generation_job_failed", contact_id=contact_id, error=str(err))
        raise err

register_job_handler("generate_email", generate_email_job_handler)

async def run_email_generation(contact_id: str, tenant_id: str) -> dict:
    """
    Constructs cold email outreach and stores it on the contact record.
    Ensures zero hallucination compliance by utilizing verified facts from research_data.
    """
    # 1. Fetch contact
    contact = None
    if supabase_client:
        try:
            try:
                res = supabase_client.table("contacts").select("*").eq("id", contact_id).execute()
                if res.data:
                    contact = res.data[0]
            except Exception:
                res = supabase_client.table("crm_contacts").select("*").eq("id", contact_id).execute()
                if res.data:
                    contact = res.data[0]
        except Exception as e:
            logger.error("db_fetch_contact_failed", contact_id=contact_id, error=str(e))

    if not contact:
        # Local Fallback
        local_contacts = _load_local_json("local_crm_contacts.json")
        for c in local_contacts:
            if c.get("id") == contact_id:
                contact = c
                break

    if not contact:
        raise ValueError(f"Contact not found: {contact_id}")

    custom_fields = contact.get("custom_fields") or {}
    research_data = custom_fields.get("research_data") or {}
    sourced_facts = research_data.get("sourced_facts") or []
    
    # Format verified facts into a string block
    facts_block = "\n".join([f"- {f.get('fact')} (Source: {f.get('source')})" for f in sourced_facts])
    if not facts_block:
        facts_block = "- Target is a prospect in the CRM."

    # 2. Load tenant configuration
    config = get_tenant_config(tenant_id)
    company_name = config.get("company_name") or "Visoora"
    company_description = config.get("company_description") or ""
    value_proposition = config.get("value_proposition") or ""
    brand_voice_tone = config.get("brand_voice_tone") or "Professional and consultative"
    playbook_greeting = config.get("playbook_greeting") or "Hi"

    # Default fallback email template (No Hallucinations)
    subject = f"Question regarding {contact.get('company_name', 'your company')}'s processes"
    body = f"{playbook_greeting} {contact.get('full_name', contact.get('name', 'there'))},\n\nI was looking into {contact.get('company_name', 'your organization')} and wanted to share how we help teams at {company_name} improve booking rates.\n\nWe would love to connect. Let me know if you have 10 minutes next week.\n\nBest regards,\nOutreach Team\n{company_name}"

    # Call LLM via AI Platform
    try:
        agent = EmailAgent(tenant_id=contact.get("tenant_id", "system"), user_id=contact_id)
        
        prompt = f"""
        OUR PRODUCT DETAIL:
        Description: {company_description}
        Value Proposition: {value_proposition}
        Brand Voice/Tone: {brand_voice_tone}

        PROSPECT DETAILS:
        Name: {contact.get("full_name") or contact.get("name")}
        Company: {contact.get("company_name") or contact.get("company")}
        Job Title: {contact.get("title")}
        Verified Sourced Facts (ONLY use these verified facts, do NOT make up testimonials or state we have worked together previously):
        {facts_block}

        Write a short, engaging email (under 150 words) with a clear subject line and body.
        """
        email_res = await agent.draft_email(context_str=prompt)
        
        subject = email_res.subject
        body = email_res.body
        
    except Exception as llm_err:
        logger.error("email_llm_failed", error=str(llm_err))

    email_data = {
        "subject": subject,
        "body": body,
        "status": "review"
    }

    # Save to database or local fallback
    custom_fields["outreach_email"] = email_data
    if supabase_client:
        try:
            try:
                supabase_client.table("contacts").update({"custom_fields": custom_fields}).eq("id", contact_id).execute()
            except Exception:
                supabase_client.table("crm_contacts").update({"custom_fields": custom_fields}).eq("id", contact_id).execute()
        except Exception as db_err:
            logger.error("db_save_email_failed", contact_id=contact_id, error=str(db_err))

    # Local fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    for c in local_contacts:
        if c.get("id") == contact_id:
            c["custom_fields"] = custom_fields
            break
    _save_local_json("local_crm_contacts.json", local_contacts)

    logger.info("email_outreach_generated", contact_id=contact_id, subject=subject)
    return email_data
