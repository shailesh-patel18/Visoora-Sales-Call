import asyncio
import uuid
import logging
from backend.ai_platform.runtime.engine import runtime
from backend.ai_platform.runtime.models import MissionRequest
from backend.ai_platform.events.bus import global_event_bus
from backend.ai_platform.evaluation.evaluator import register_evaluator
from backend.ai_platform.observability.tracker import register_tracker

logging.basicConfig(level=logging.INFO)

async def main():
    print("--- STARTING SDK & OBSERVABILITY TEST ---")
    
    # 1. Start Event Bus
    global_event_bus.start()
    
    # 2. Register Observers
    register_evaluator()
    register_tracker()
    
    # 3. Create Mission Request
    mission_id = str(uuid.uuid4())
    req = MissionRequest(
        mission_id=mission_id,
        type="LeadDiscovery",
        parameters={
            "company_name": "TestCorp SDK",
            "icp_segment": "HR Managers"
        }
    )
    
    # 4. Execute via Runtime
    final_state = await runtime.execute(req)
    
    # Allow async events to settle
    await asyncio.sleep(1)
    
    print("--- SDK MISSION COMPLETE ---")
    print("Leads found:", len(final_state.get("decision_makers", [])))
    
    await global_event_bus.stop()
    print("Test passed.")

if __name__ == "__main__":
    asyncio.run(main())
