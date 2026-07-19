import asyncio
from backend.ai_platform.events.bus import global_event_bus
from backend.ai_platform.events.models import MissionEvent

async def test_event_bus():
    global_event_bus.start()
    print("--- TESTING EVENT BUS ---")
    
    received_events = []
    
    async def dummy_handler(event: MissionEvent):
        print(f"Received event: {event.event_type} for mission {event.mission_id}")
        received_events.append(event)
        
    global_event_bus.subscribe("TestEvent", dummy_handler)
    global_event_bus.subscribe_all(lambda e: print(f"[Audit] Caught {e.event_type}"))
    
    # Fire event
    global_event_bus.publish(MissionEvent(mission_id="123", event_type="TestEvent", payload={"status": "ok"}))
    global_event_bus.publish(MissionEvent(mission_id="123", event_type="OtherEvent", payload={}))
    
    # Wait for events to process
    await asyncio.sleep(0.5)
    
    assert len(received_events) == 1
    assert received_events[0].event_type == "TestEvent"
    
    print("Test passed! Shutting down bus...")
    await global_event_bus.stop()

if __name__ == "__main__":
    asyncio.run(test_event_bus())
