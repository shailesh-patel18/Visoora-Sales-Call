import logging
from typing import Dict, Any
from .graph import ExecutionGraph
from ..memory.mission import MissionMemory
from server.prospecting.registry import global_capability_registry
from server.prospecting.capability import PeopleDiscoveryCapability, CompanyDiscoveryCapability, EmailFinderCapability

logger = logging.getLogger(__name__)

class MissionPlanner:
    """
    Intelligently orchestrates tasks by defining an ExecutionGraph 
    and resolving the best providers for required capabilities.
    """
    def __init__(self, memory: MissionMemory):
        self.memory = memory

    async def execute_mission(self, icp_segment: str, company_name: str) -> Dict[str, Any]:
        """
        Dynamically plans and executes a mission to find leads, emails, and company context.
        """
        graph = ExecutionGraph(self.memory.mission_id)

        from ..events.models import MissionStarted, MissionCompleted
        from ..events.bus import global_event_bus
        
        global_event_bus.publish(MissionStarted(self.memory.mission_id))
        
        # Load from memory to support resume
        graph_results = self.memory.get("graph_results") or {}
        
        # Step 1: Add Company Discovery Node
        async def run_company_discovery(context, results):
            provider = global_capability_registry.get_best_provider(CompanyDiscoveryCapability)
            data = await provider.research_company(company_name)
            self.memory.set("website_summary", data.get("description"))
            self.memory.set("pain_points", data.get("pain_points", []))
            self.memory.set("technologies", data.get("technologies", []))
            return data

        graph.add_node("company_discovery", run_company_discovery)

        # Step 2: Add People Discovery Node (runs in parallel)
        async def run_people_discovery(context, results):
            provider = global_capability_registry.get_best_provider(PeopleDiscoveryCapability)
            leads = await provider.find_leads(icp_segment, limit=5)
            self.memory.set("decision_makers", leads)
            return leads

        graph.add_node("people_discovery", run_people_discovery)

        # Step 3: Add Email Finding Node (depends on people discovery)
        async def run_email_finding(context, results):
            leads = results.get("people_discovery", [])
            provider = global_capability_registry.get_best_provider(EmailFinderCapability)
            
            emails_found = []
            if isinstance(leads, list):
                for lead in leads:
                    name = lead.get("name")
                    domain = lead.get("company", "").replace(" ", "").lower() + ".com"
                    if name and domain:
                        emails = await provider.find_emails(name, domain)
                        if emails:
                            lead["email"] = emails[0]
                            emails_found.append(emails[0])
            
            # Update memory with enriched leads
            self.memory.set("decision_makers", leads)
            return emails_found

        graph.add_node("email_finding", run_email_finding, dependencies=["people_discovery"])

        # Execute Graph
        logger.info(f"MissionPlanner: Starting ExecutionGraph for mission {self.memory.mission_id}")
        
        # We wrap execution to save results incrementally if we had a node callback, 
        # but for now we just pass previous_results and save at the end.
        results = await graph.execute(previous_results=graph_results)
        
        # Save checkpoints
        self.memory.set("graph_results", results)
        
        logger.info(f"MissionPlanner: Mission completed. Final state saved to MissionMemory.")
        
        final_state = self.memory.snapshot()
        global_event_bus.publish(MissionCompleted(self.memory.mission_id, final_state))
        
        return final_state
