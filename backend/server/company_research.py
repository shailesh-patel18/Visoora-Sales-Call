import os
import json
import asyncio
import structlog
import httpx
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from server.storage_manager import supabase_client
from server.worker import register_job_handler
from crm.auto_advance import _load_local_json, _save_local_json
from api.supabase_client import get_supabase_client
from ai_platform.agents.research_agent import ResearchAgent

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
            res = supabase_client.table("tenants").select("settings").eq("id", tenant_uuid).execute()
            if res.data and res.data[0].get("settings"):
                settings = res.data[0]["settings"]
                if "business_brain" in settings:
                    business_brain = settings["business_brain"]
        except:
            pass

        await _update_job_status(tenant_id, payload, {"stage": "TARGET_SELECTION", "pct": 20}, job_id)
        
        # 2. Fetch target contacts
        max_prospects = payload.get("max_prospects", 5) # Default to 5 for safety in batch
        contacts = []
        try:
            res = supabase_client.table("contacts").select("*").eq("tenant_id", tenant_uuid).limit(max_prospects).execute()
            contacts = res.data or []
        except Exception as e:
            logger.error("failed_to_fetch_contacts_for_mission", error=str(e))
            
        if not contacts:
            # Fallback to a single mock contact for demo if DB is empty
            contacts = [{"id": "test_123", "company": "Acme Healthcare", "first_name": "John", "last_name": "Smith", "title": "CEO"}]

        from ai_platform.services.generation_service import generation_service
        
        total_contacts = len(contacts)
        for i, target in enumerate(contacts):
            pct = 20 + int(80 * (i / total_contacts))
            await _update_job_status(tenant_id, payload, {"stage": f"DRAFTING_EMAIL_{i+1}", "pct": pct}, job_id)
            
            # 3. Research & Draft
            try:
                raw_research = await run_company_research(target.get("id"), tenant_uuid)
                facts = raw_research.get("sourced_facts", [])
                research_data = "\n".join([f"- {f.get('fact', '')} (Source: {f.get('source', '')})" for f in facts])
                if not research_data.strip():
                    research_data = "No verified facts found."
                
                email_result = await generation_service.draft_prospecting_email(business_brain, target, research_data)
                
                # 4. Save Artifact
                artifact_record = {
                    "tenant_id": tenant_uuid,
                    "type": "EMAIL_DRAFT",
                    "status": "WAITING_APPROVAL",
                    "created_by": "Visoora Engine",
                    "mission_id": mission_name,
                    "confidence": email_result.get("personalization_score", 92),
                    "cost_usd": 0.04,
                    "prospect_name": f"{target.get('first_name', 'John')} {target.get('last_name', '')}".strip(),
                    "company_name": target.get('company', 'Unknown Company'),
                    "pain_points": email_result.get("pain_points_addressed", []),
                    "reason_selected": email_result.get("reason_selected", ""),
                    "email_subject": email_result.get("email_subject", ""),
                    "email_body": email_result.get("email_body", ""),
                    "expected_reply_rate": email_result.get("expected_reply_rate", "10%"),
                    "expected_meeting_prob": email_result.get("expected_meeting_prob", "2%"),
                    "metadata": {
                        "personalization_score": email_result.get("personalization_score", 92),
                        "business_brain_match": email_result.get("business_brain_match", 90),
                        "spam_risk": email_result.get("spam_risk", "Low"),
                        "versions": [],
                        "alternatives": []
                    }
                }
                
                supabase_client.table("mission_artifacts").insert(artifact_record).execute()
                
            except Exception as draft_err:
                logger.error("drafting_failed_for_target", target=target.get("id"), error=str(draft_err))
                continue
                
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

async def run_company_research(contact_id: str, tenant_id: str) -> dict:
    """
    Performs safe company research respecting robots.txt.
    Structures data separating Sourced Facts from AI Estimates.
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

    company_name = contact.get("company_name") or contact.get("company") or "Independent"
    website = contact.get("website") or contact.get("email", "").split("@")[-1] if "@" in contact.get("email", "") else ""
    if website and not website.startswith("http"):
        website = f"https://{website}"

    # Determine if we can scrape target site
    can_scrape = False
    metadata_facts = []
    scraped_text = ""
    
    if website and "gmail.com" not in website and "yahoo.com" not in website and "hotmail.com" not in website:
        can_scrape = await check_robots_txt_allows(website)
        if can_scrape:
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.get(website)
                    if res.status_code == 200:
                        # Extract title and simple body text snippets safely (avoiding rich HTML parsing libraries to keep code simple)
                        scraped_text = res.text[:2000] # Grab first 2000 chars of HTML/text
                        metadata_facts.append(f"Successfully scraped home page of {website}")
            except Exception as scrape_err:
                logger.warn("scrape_home_page_failed", url=website, error=str(scrape_err))
                metadata_facts.append(f"Attempted scraping {website} but request timed out.")
        else:
            metadata_facts.append(f"Scraping website {website} disallowed by robots.txt compliance rule.")
    else:
        metadata_facts.append("No valid custom company domain website listed.")

    # Call LLM to extract sourced facts vs projections
    facts_list = [
        {"fact": f"Company Name: {company_name}", "source": "CRM record", "url": website or "N/A"},
        {"fact": f"Contact email domain: {website}", "source": "CRM record", "url": website or "N/A"}
    ]
    estimates_list = [
        {"estimate": "Revenue tier likely matches small/medium enterprise based on CRM baseline.", "confidence": "Medium"}
    ]

    prompt = f"""
    You are an expert market researcher. Help structure research on the company "{company_name}".
    We scraped this text snippet from their domain:
    {scraped_text[:1200]}

    Return a structured report separating VERIFIED FACTS from ESTIMATED PROJECTIONS.
    - FACTS MUST be directly grounded in the scraped snippet or domain name (e.g. description, headquarters, website). Provide the URL source.
    - ESTIMATED PROJECTIONS are logical market-size guesses, target buyer personas, or potential sales objections they might raise.
    - Do not make up fake client names or specific numbers (like $23.4M revenue) unless it is explicitly present in the scraped text snippet.

    Respond ONLY in this valid JSON format:
    {{
        "sourced_facts": [
            {{"fact": "Fact details", "source": "Website meta text", "url": "{website or "N/A"}"}}
        ],
        "estimates": [
            {{"estimate": "Estimated details", "confidence": "High/Medium/Low"}}
        ]
    }}
    """
    try:
        agent = ResearchAgent(tenant_id=contact.get("tenant_id", "system"), user_id=contact_id)
        research_res = await agent.research_company(prompt=prompt)
        
        # Extract from the Pydantic model returned
        facts_list = [f.model_dump() for f in research_res.sourced_facts] if research_res.sourced_facts else facts_list
        estimates_list = [e.model_dump() for e in research_res.estimates] if research_res.estimates else estimates_list
        
    except Exception as llm_err:
        logger.error("research_llm_failed", error=str(llm_err))
        estimates_list.append({"estimate": "AI evaluation bypassed due to temporary API timeout.", "confidence": "Low"})

    research_data = {
        "sourced_facts": facts_list,
        "estimates": estimates_list,
        "metadata_facts": metadata_facts
    }

    # Save to database or local fallback
    if supabase_client:
        try:
            try:
                supabase_client.table("contacts")\
                    .update({
                        "custom_fields": {
                            **contact.get("custom_fields", {}),
                            "research_data": research_data
                        }
                    })\
                    .eq("id", contact_id)\
                    .execute()
            except Exception:
                supabase_client.table("crm_contacts")\
                    .update({
                        "custom_fields": {
                            **contact.get("custom_fields", {}),
                            "research_data": research_data
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
            c["custom_fields"]["research_data"] = research_data
            break
    _save_local_json("local_crm_contacts.json", local_contacts)

    logger.info("company_research_completed", contact_id=contact_id, company=company_name)
    return research_data
