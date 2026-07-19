import asyncio
import os
import uuid
import sys
from typing import Dict, Any

# Set development mode to force mock providers
os.environ["DEVELOPMENT_MODE"] = "true"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.ai_platform.runtime.models import MissionRequest
from backend.ai_platform.runtime.engine import runtime
from backend.ai_platform.events.bus import global_event_bus
from backend.ai_platform.events.models import MissionCompleted, ApprovalRequested
from backend.ai_platform.evaluation.evaluator import register_evaluator

def create_golden_test_cases():
    return [
        {
            "id": "tc_01_b2b_saas",
            "type": "AI_SDR",
            "parameters": {
                "company_name": "Acme SaaS",
                "icp_segment": "VP of Sales"
            },
            "expected_drafts": 5, # Mock provider returns 5 leads
            "expected_min_score": 8.0
        }
    ]

async def run_golden_tests():
    print("--- STARTING GOLDEN DATASET REGRESSION SUITE ---")
    
    register_evaluator()
    test_cases = create_golden_test_cases()
    
    for tc in test_cases:
        print(f"\nRunning Test Case: {tc['id']}")
        
        # 1. Setup Mission
        req = MissionRequest(
            mission_id=str(uuid.uuid4()),
            type=tc["type"],
            parameters=tc["parameters"],
            tenant_id="test_tenant"
        )
        
        # 2. Track Events
        events_received = []
        def on_event(event):
            if event.mission_id == req.mission_id:
                events_received.append(event)
                
        global_event_bus.subscribe_all(on_event)
        global_event_bus.start()
        
        # 3. Execute Mission (Will pause at Approval Node)
        print("  Executing AI SDR Mission (Phase 1)...")
        state = await runtime.execute(req)
        await asyncio.sleep(0.5)
        
        # 4. Verify Paused State
        approval_events = [e for e in events_received if isinstance(e, ApprovalRequested)]
        assert len(approval_events) == 1, "Mission did not emit ApprovalRequested event"
        
        drafts = state.get("outreach_drafts", [])
        print(f"  Found {len(drafts)} email drafts.")
        assert len(drafts) > 0, "No email drafts generated"
        
        # 5. Resume Mission
        print("  Resuming AI SDR Mission (Simulating Human Approval)...")
        final_state = await runtime.resume(req, approval_granted=True)
        
        # 6. Verify Completed State
        completed_events = [e for e in events_received if isinstance(e, MissionCompleted)]
        assert len(completed_events) == 1, "Mission did not emit MissionCompleted event"
        assert final_state.get("emails_sent") is True, "Emails were not dispatched"
        
        print("  Evaluating Results...")
        # Since MissionCompleted was emitted, Evaluator should have run asynchronously.
        # Wait a moment for async evaluation
        await asyncio.sleep(1.0)
        
        from backend.ai_platform.events.models import MissionEvaluated
        eval_events = [e for e in events_received if isinstance(e, MissionEvaluated)]
        assert len(eval_events) >= 1, "MissionEvaluated event not found"
        
        scores = eval_events[-1].payload.get("scores", {})
        print(f"  Scores: {scores}")
        
        overall = scores.get("overall", 0.0)
        assert overall >= tc["expected_min_score"], f"Overall score {overall} is below minimum {tc['expected_min_score']}"
        
        print(f"[PASSED] Test Case {tc['id']} passed!")
        
    print("\n--- ALL GOLDEN TESTS PASSED ---")

if __name__ == "__main__":
    asyncio.run(run_golden_tests())
