import asyncio
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)

from server.prospecting import *
from ai_platform.memory.mission import MissionMemory
from ai_platform.orchestration.planner import MissionPlanner

async def main():
    from backend.ai_platform.events.bus import global_event_bus
    global_event_bus.start()
    
    print("--- STARTING MISSION PLANNER TEST ---")
    mission_id = str(uuid.uuid4())
    memory = MissionMemory(mission_id)
    planner = MissionPlanner(memory)
    
    final_state = await planner.execute_mission("VP Engineering B2B SaaS", "Acme Corp")
    print("\n--- FINAL MISSION STATE ---")
    
    print(f"Website Summary: {final_state.get('website_summary')}")
    print(f"Pain Points: {final_state.get('pain_points')}")
    print(f"Technologies: {final_state.get('technologies')}")
    print("\nDecision Makers:")
    for lead in final_state.get("decision_makers", []):
        print(f"- {lead['name']} ({lead['title']}) at {lead['company']} | Email: {lead.get('email', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
