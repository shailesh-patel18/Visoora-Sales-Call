import logging
from typing import Dict, Any

from ..orchestration.planner import MissionPlanner
from ..orchestration.graph import ExecutionGraph, MissionPausedException
from ..events.models import MissionStarted, MissionCompleted, ApprovalRequested
from ..events.bus import global_event_bus
from server.prospecting.registry import global_capability_registry
from server.prospecting.capability import PeopleDiscoveryCapability, CompanyDiscoveryCapability, EmailFinderCapability
from ..agents.email_agent import EmailAgent

logger = logging.getLogger(__name__)

class AISDRMissionPlanner(MissionPlanner):
    """
    Orchestrates the AI SDR Mission.
    Graph: Lead Discovery -> Research -> Personalize -> Email Draft -> Approval Node -> Dispatch
    """
    
    async def execute_mission(self, icp_segment: str, company_name: str) -> Dict[str, Any]:
        graph = ExecutionGraph(self.memory.mission_id)
        global_event_bus.publish(MissionStarted(self.memory.mission_id))
        graph_results = self.memory.get("graph_results") or {}
        
        # 1. Company Discovery
        async def run_company_discovery(context, results):
            provider = global_capability_registry.get_best_provider(CompanyDiscoveryCapability)
            data = await provider.research_company(company_name)
            self.memory.set("website_summary", data.get("description"))
            self.memory.set("pain_points", data.get("pain_points", []))
            return data

        graph.add_node("company_discovery", run_company_discovery)

        # 2. People Discovery & Email Finding (Combined for brevity)
        async def run_people_discovery(context, results):
            provider = global_capability_registry.get_best_provider(PeopleDiscoveryCapability)
            leads = await provider.find_leads(icp_segment, limit=5)
            
            email_provider = global_capability_registry.get_best_provider(EmailFinderCapability)
            enriched_leads = []
            for lead in leads:
                name = lead.get("name")
                domain = lead.get("company", "").replace(" ", "").lower() + ".com"
                if name and domain:
                    emails = await email_provider.find_emails(name, domain)
                    if emails:
                        lead["email"] = emails[0]
                enriched_leads.append(lead)
            
            self.memory.set("decision_makers", enriched_leads)
            return enriched_leads

        graph.add_node("people_discovery", run_people_discovery)

        # 3. Personalization & Email Draft
        async def run_email_draft(context, results):
            leads = results.get("people_discovery", [])
            company_data = results.get("company_discovery", {})
            
            agent = EmailAgent(self.memory.tenant_id)
            drafts = []
            for lead in leads:
                if not lead.get("email"):
                    continue
                context_str = f"Draft an email for {lead.get('name')} at {lead.get('company')}. Context: {company_data.get('description')}"
                draft = await agent.draft_email(context_str, memory=self.memory)
                drafts.append({"lead": lead, "draft": draft.model_dump()})
                
            self.memory.set("outreach_drafts", drafts)
            return drafts
            
        graph.add_node("email_draft", run_email_draft, dependencies=["company_discovery", "people_discovery"])

        # 4. Approval Node
        async def run_approval(context, results):
            drafts = results.get("email_draft", [])
            if not drafts:
                return {"status": "skipped", "reason": "No drafts generated"}
            
            # Emit approval requested
            global_event_bus.publish(ApprovalRequested(self.memory.mission_id, policy="email_send", payload={"drafts_count": len(drafts)}))
            
            # Halt graph execution
            raise MissionPausedException("Approval required for email dispatch")
            
        graph.add_node("approval", run_approval, dependencies=["email_draft"])

        # 5. Email Dispatch
        async def run_dispatch(context, results):
            # In a real app, this would integrate with an SMTP provider / Gmail API.
            drafts = results.get("email_draft", [])
            logger.info(f"Dispatching {len(drafts)} emails...")
            self.memory.set("emails_sent", True)
            return {"sent": len(drafts)}
            
        graph.add_node("email_dispatch", run_dispatch, dependencies=["approval"])

        # Execute Graph
        logger.info(f"AISDRMissionPlanner: Starting ExecutionGraph for mission {self.memory.mission_id}")
        
        results = await graph.execute(previous_results=graph_results)
        self.memory.set("graph_results", results)
        
        # Check if paused
        if isinstance(results.get("approval"), MissionPausedException):
            logger.info(f"AISDRMissionPlanner: Mission {self.memory.mission_id} paused pending approval.")
            final_state = self.memory.snapshot()
            return final_state
        
        logger.info(f"AISDRMissionPlanner: Mission completed. Final state saved.")
        final_state = self.memory.snapshot()
        global_event_bus.publish(MissionCompleted(self.memory.mission_id, final_state))
        
        return final_state
