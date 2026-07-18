import os
import json
import asyncio
import structlog
import httpx
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from server.storage_manager import supabase_admin_client as supabase_client
from server.worker import register_job_handler
from crm.auto_advance import _load_local_json, _save_local_json
from ai_platform.agents.research_agent import ResearchAgent
from server.ai_gateway import gateway
from server.onboarding_api import in_house_crawl

logger = structlog.get_logger("visoora_company_research")

async def _update_job_status(tenant_id: str, payload: dict, progress: dict, job_id: str = None):
    if not supabase_client:
        return
        
    try:
        # We can update the payload of the workflow_job if job_id is known
        if job_id:
            res = supabase_client.table("workflow_jobs").select("payload").eq("id", job_id).execute()
            if res.data:
                current_payload = res.data[0]["payload"]
                current_payload["progress"] = progress
                supabase_client.table("workflow_jobs").update({"payload": current_payload}).eq("id", job_id).execute()
        
        mission_id = payload.get("mission_id")
        if mission_id:
            status = progress.get("stage", "running").lower()
            supabase_client.table("missions").update({"status": status}).eq("id", mission_id).execute()
            
    except Exception as e:
        logger.error("failed_to_update_job_status", error=str(e))

async def company_research_job_handler(payload: dict, job_id: str = None) -> dict:
    """
    Background job handler for doing company research and drafting an email artifact.
    """
    tenant_id = payload.get("tenant_id")
    mission_name = payload.get("mission_name")
    contact_id = payload.get("contact_id")

    if not tenant_id:
        raise ValueError("Missing required parameters: 'tenant_id'")

    logger.info("company_research_job_start", tenant_id=tenant_id, mission=mission_name)

    # Allow job_id to be passed via payload OR kwargs
    job_id = job_id or payload.get("job_id")
    
    if mission_name:
        # PMF Batch Flow
        await _update_job_status(tenant_id, payload, {"stage": "PLANNING", "pct": 10}, job_id)
        
        # 1. Fetch Business Brain
        from server.onboarding_api import resolve_tenant_uuid
        tenant_uuid = resolve_tenant_uuid(tenant_id)
        
        # In MVP, Business Brain is stored in tenants table under custom_fields or settings, or ICPSegments.
        # Let's mock a rich business brain for the MVP if not found
        business_brain = {
            "company_description": "Visoora AI helps B2B sales teams automate outbound pipeline.",
            "value_proposition": "Cut time to value by 40% with autonomous SDRs.",
            "competitors": ["Outreach", "Apollo"],
            "brand_voice_tone": "Direct, Professional, Concise"
        }
        try:
            res = supabase_client.table("business_brains").select("metadata").eq("tenant_id", tenant_uuid).order("created_at", desc=True).limit(1).execute()
            if res.data and res.data[0].get("metadata"):
                metadata = res.data[0]["metadata"]
                # The full report is in metadata.full_report
                if "full_report" in metadata:
                    report = metadata["full_report"]
                    business_brain["company_description"] = report.get("executive_summary", {}).get("company_description", business_brain["company_description"])
                    business_brain["value_proposition"] = report.get("executive_summary", {}).get("value_proposition", business_brain["value_proposition"])
                    business_brain["icp_industries"] = [icp.get("industry") for icp in report.get("icp_discovery", []) if icp.get("industry")]
                    business_brain["competitors"] = [comp.get("name") for comp in report.get("competitor_analysis", []) if comp.get("name")]
        except Exception as e:
            logger.warn("failed_to_fetch_business_brain", error=str(e))

        await _update_job_status(tenant_id, payload, {"stage": "TARGET_SELECTION", "pct": 20}, job_id)
        
        # 2. Fetch target contacts
        max_prospects = payload.get("max_prospects", 5) # Default to 5 for safety in batch
        contacts = []
        from server.services.prospecting.factory import get_prospect_provider
        
        try:
            provider = get_prospect_provider()
            contacts = await provider.search_prospects(tenant_id=tenant_uuid, business_brain=business_brain, max_results=max_prospects)
        except Exception as e:
            logger.error("failed_to_fetch_contacts_from_provider", error=str(e))
            
        if not contacts:
            # Fallback to a single mock contact for demo if DB is empty
            contacts = [{"id": "test_123", "company": "Acme Healthcare", "first_name": "John", "last_name": "Smith", "title": "CEO"}]

        from ai_platform.services.generation_service import generation_service
        
        total_contacts = len(contacts)
        for i, target in enumerate(contacts):
            pct = 20 + int(80 * (i / total_contacts))
            await _update_job_status(tenant_id, payload, {"stage": f"DRAFTING_EMAIL_{i+1}", "pct": pct}, job_id)
            
            # 3. Research & Draft (With Retry Logic)
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    knowledge = await run_company_research(target.get("id"), tenant_uuid, contact_data=target)
                    
                    email_result = await generation_service.draft_prospecting_email(business_brain, target, knowledge)
                    
                    draft = email_result.get("draft", {})
                    meta = email_result.get("meta", {})
                    
                    # Deterministic Scoring (Coverage based)
                    citations = draft.get("citations", [])
                    used_fields = set(c.get("field", "").lower() for c in citations)
                    score = 10 # Base score for running validation
                    if any("company" in f or "industry" in f for f in used_fields): score += 30
                    if any("product" in f or "pricing" in f for f in used_fields): score += 30
                    if any("case study" in f or "customer" in f for f in used_fields): score += 30
                    personalization_score = min(100, score)
                    
                    # Explainability Summary
                    explainability = []
                    for c in citations:
                        explainability.append(f"✓ Used {c.get('field')}")
                    if not explainability:
                        explainability.append("⚠ No verified facts used.")
                    
                    # 4. Save Artifact
                    artifact_record = {
                        "tenant_id": tenant_uuid,
                        "type": "EMAIL_DRAFT",
                        "status": "WAITING_APPROVAL",
                        "created_by": "Visoora Engine",
                        "mission_id": mission_name,
                        "confidence": personalization_score,
                        "cost_usd": 0.04,
                        "prospect_name": f"{target.get('first_name', 'John')} {target.get('last_name', '')}".strip(),
                        "company_name": target.get('company', 'Unknown Company'),
                        "email_subject": draft.get("subject", ""),
                        "email_body": draft.get("body", ""),
                        # Removed fake metrics (expected_reply_rate, expected_meeting_prob)
                        "metadata": {
                            "personalization_score": personalization_score,
                            "explainability_summary": explainability,
                            "citations": citations,
                            "prompt_version": meta.get("prompt_version"),
                            "model": meta.get("model"),
                            "temperature": meta.get("temperature"),
                            "versions": [],
                            "alternatives": []
                        }
                    }
                    
                    supabase_client.table("mission_artifacts").insert(artifact_record).execute()
                    break # Success, exit retry loop
                    
                except Exception as draft_err:
                    logger.warn("drafting_failed_for_target", target=target.get("id"), attempt=attempt+1, error=str(draft_err))
                    if attempt == max_attempts - 1:
                        logger.error("drafting_completely_failed_for_target", target=target.get("id"))
                    else:
                        await asyncio.sleep(2 * (attempt + 1)) # Exponential backoff
                
        await _update_job_status(tenant_id, payload, {"stage": "HUMAN_APPROVAL", "pct": 100}, job_id)
        
        try:
            from server.events.bus import bus
            bus.publish("ApprovalRequired", {
                "email": "ceo@visoora.com",
                "mission_name": mission_name,
                "count": total_contacts
            })
        except Exception as e:
            logger.warn("failed_to_publish_approval_required_event", error=str(e))
            
        return {"status": "success", "mission_name": mission_name, "processed": total_contacts}
    else:
        # Legacy single-contact flow
        research_data = await run_company_research(contact_id, tenant_id)
        return {"contact_id": contact_id, "status": "success", "research_data": research_data}

register_job_handler("company_research", company_research_job_handler)

async def check_robots_txt_allows(url: str, user_agent: str = "*") -> bool:
    """
    Reads website robots.txt and verifies if the Visoora research agent is permitted to read it.
    """
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            return False
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        rp = RobotFileParser()
        # Set a short timeout for robots.txt fetch
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(robots_url)
            if res.status_code == 200:
                # Parse lines
                rp.parse(res.text.splitlines())
                allowed = rp.can_fetch(user_agent, url)
                logger.info("robots_txt_checked", url=url, allowed=allowed)
                return allowed
            elif res.status_code == 404:
                # No robots.txt, default is allowed
                logger.info("robots_txt_not_found_allowed", url=url)
                return True
    except Exception as e:
        logger.warn("robots_txt_check_error_default_allow", url=url, error=str(e))
        return True
    return True

def _validate_evidence(fields: list, structured_text: str) -> list:
    """
    Evidence Validator Rule:
    1. Confidence < 80 -> Discard
    2. Snippet doesn't exist in text -> Discard
    3. Confidence >= 95 -> Auto-verify
    """
    valid_fields = []
    text_lower = structured_text.lower()
    
    for f in fields:
        if f.confidence < 80 or str(f.value).strip().lower() == "unknown":
            continue
            
        # Check snippet existence
        if f.snippet != "N/A" and f.snippet.lower() not in text_lower:
            continue
            
        f.verified = f.confidence >= 95
        valid_fields.append(f.model_dump())
        
    return valid_fields

async def run_company_research(contact_id: str, tenant_id: str, contact_data: dict = None) -> dict:
    """
    Performs safe company research using the Deterministic Knowledge Engine.
    Structures data exclusively as verified EvidenceFields.
    """
    # 1. Fetch contact
    contact = contact_data
    if not contact and supabase_client:
        try:
            try:
                res = supabase_client.table("contacts").select("*").eq("id", contact_id).eq("tenant_id", tenant_id).execute()
                if res.data:
                    contact = res.data[0]
            except Exception:
                res = supabase_client.table("crm_contacts").select("*").eq("id", contact_id).eq("tenant_id", tenant_id).execute()
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

    company_name = contact.get("company_name") or contact.get("company") or "Independent"
    website = contact.get("website") or contact.get("email", "").split("@")[-1] if "@" in contact.get("email", "") else ""
    if website and not website.startswith("http"):
        website = f"https://{website}"

    # 2. Deterministic Crawl (No Raw HTML to AI)
    can_scrape = False
    metadata_facts = []
    structured_data = {}
    
    if website and "gmail.com" not in website and "yahoo.com" not in website and "hotmail.com" not in website:
        can_scrape = await check_robots_txt_allows(website)
        if can_scrape:
            try:
                structured_data = await in_house_crawl(website)
                metadata_facts.append(f"Successfully scraped {website}")
            except Exception as scrape_err:
                logger.warn("scrape_home_page_failed", url=website, error=str(scrape_err))
                metadata_facts.append(f"Attempted scraping {website} but request failed.")
        else:
            metadata_facts.append(f"Scraping website {website} disallowed by robots.txt compliance rule.")
    else:
        metadata_facts.append("No valid custom company domain website listed.")

    # Convert structured data to a searchable string for validation
    structured_text_blob = json.dumps(structured_data)
    
    knowledge = {
        "identity": [],
        "products": [],
        "social_proof": [],
        "metadata_facts": metadata_facts
    }

    if structured_data and structured_data.get("pages"):
        try:
            # 3. Small Focused Extractors
            identity_ext = await gateway.extract_identity(structured_data, website)
            products_ext = await gateway.extract_products(structured_data, website)
            proof_ext = await gateway.extract_social_proof(structured_data, website)
            
            # 4. Evidence Validation
            knowledge["identity"] = _validate_evidence(identity_ext.fields, structured_text_blob)
            knowledge["products"] = _validate_evidence(products_ext.fields, structured_text_blob)
            knowledge["social_proof"] = _validate_evidence(proof_ext.fields, structured_text_blob)
            
        except Exception as llm_err:
            logger.error("research_extraction_failed", error=str(llm_err))

    # 5. Save Knowledge Object
    if supabase_client:
        try:
            try:
                supabase_client.table("contacts")\
                    .update({
                        "custom_fields": {
                            **contact.get("custom_fields", {}),
                            "research_data": knowledge
                        }
                    })\
                    .eq("id", contact_id)\
                    .execute()
            except Exception:
                supabase_client.table("crm_contacts")\
                    .update({
                        "custom_fields": {
                            **contact.get("custom_fields", {}),
                            "research_data": knowledge
                        }
                    })\
                    .eq("id", contact_id)\
                    .execute()
        except Exception as db_err:
            logger.error("db_save_research_failed", contact_id=contact_id, error=str(db_err))

    # Local fallback
    local_contacts = _load_local_json("local_crm_contacts.json")
    for c in local_contacts:
        if c.get("id") == contact_id:
            c["custom_fields"] = c.get("custom_fields") or {}
            c["custom_fields"]["research_data"] = knowledge
            break
    _save_local_json("local_crm_contacts.json", local_contacts)

    logger.info("company_research_completed", contact_id=contact_id, company=company_name)
    return knowledge
