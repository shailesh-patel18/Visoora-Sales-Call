import sys
from unittest.mock import MagicMock

# Dynamically mock google.antigravity if not installed to allow local testing
try:
    import google.antigravity
except ImportError:
    class DummyAntigravity:
        class AgentSession:
            pass
        def tool(self, func):
            return func
    sys.modules["google.antigravity"] = DummyAntigravity()

import asyncio
import struct
import math
from pipeline.states import StateMachineController
from pipeline.vad import VoiceActivityDetector
from pipeline.tools import handle_sub_agent_handover
from pipeline.states import CallStateContext

# Mock AgentSession for simulation purposes
class MockAgentSession:
    def __init__(self):
        self.aborted = False

    async def abort_generation(self):
        self.aborted = True
        print("[MOCK] session.abort_generation() triggered.")

    async def receive_audio(self):
        yield b'\x00' * 640

# Mock VoicePipelineManager for simulation purposes
class MockVoicePipelineManager:
    def __init__(self, session, state_controller):
        self.session = session
        self.state_controller = state_controller
        self.inbound_queue = asyncio.Queue()
        self.outbound_queue = asyncio.Queue()
        self.is_speaking = True
        self.is_streaming = True

async def run_simulation():
    print("==================================================")
    print("STARTING OUTBOUND VOICE AGENT E2E SIMULATION HARNESS")
    print("==================================================\n")

    # ----------------------------------------------------
    # TEST 1: FSM State Validation and Normal Call Flow
    # ----------------------------------------------------
    print("[TEST 1] Testing FSM State Transitions...")
    lead_metadata = {"name": "Alice Smith", "company": "Acme Corp", "phone": "+15550199"}
    fsm = StateMachineController(initial_metadata=lead_metadata, tenant_id="default_shared_tenant")
    
    assert fsm.context.current_state == "INITIATION"
    print(f"  - Initial state: {fsm.context.current_state}")
    print(f"  - Prompt modifier directive: '{fsm.generate_state_prompt_modifier()}'")

    # Verify Expert Prompt Compilation with dynamic token replacements
    prompt = fsm.compile_expert_system_prompt()
    print("  - Verifying Expert Prompt Compilation...")
    assert "Current call state: INITIATION" in prompt
    assert "Alice Smith" in prompt
    assert "Acme Corp" in prompt
    print("  => Expert Prompt Compilation validation passed.")

    # Transition to PITCH
    success = fsm.validate_and_transition("PITCH")
    assert success
    print(f"  - Transitioned to: {fsm.context.current_state}")

    # Transition to QUALIFICATION
    success = fsm.validate_and_transition("QUALIFICATION")
    assert success
    print(f"  - Transitioned to: {fsm.context.current_state}")

    # Transition to BOOKING
    success = fsm.validate_and_transition("BOOKING")
    assert success
    print(f"  - Transitioned to: {fsm.context.current_state}")

    # Transition to SUCCESS_COMPLETE
    success = fsm.validate_and_transition("SUCCESS_COMPLETE")
    assert success
    print(f"  - Transitioned to terminal state: {fsm.context.current_state}")
    assert fsm.context.is_terminal
    print("  => FSM Transition validations passed successfully.\n")

    # ----------------------------------------------------
    # TEST 2: VAD Calculation and Interruption Logic
    # ----------------------------------------------------
    print("[TEST 2] Testing Voice Activity Detection & Interruption...")
    vad = VoiceActivityDetector(threshold=300.0)
    session = MockAgentSession()
    voice_manager = MockVoicePipelineManager(session, StateMachineController(lead_metadata, tenant_id="default_shared_tenant"))
    
    # Transition FSM to PITCH so that transitioning to OBJECTION is a valid state change
    voice_manager.state_controller.validate_and_transition("PITCH")
    
    # Fill the outbound queue with some mock frames to simulate speaking
    await voice_manager.outbound_queue.put(b'\x01' * 640)
    await voice_manager.outbound_queue.put(b'\x02' * 640)
    
    # Generate high amplitude PCM frame (exceeds threshold)
    # Amplitude of 15000 leads to massive RMS (>10000)
    high_energy_samples = [15000] * 320
    high_energy_pcm = struct.pack("<320h", *high_energy_samples)
    
    energy = vad.calculate_frame_energy(high_energy_pcm)
    print(f"  - Generated PCM frame energy (RMS): {energy:.2f} (Threshold: {vad.threshold})")
    
    # Execute VAD monitor and interrupt check
    await vad.monitor_and_interrupt(high_energy_pcm, voice_manager)
    
    # Verify that the outbound queue was successfully purged
    assert voice_manager.outbound_queue.empty()
    print("  - Outbound voice playout queue purged successfully.")
    
    # Verify that the session abort was called
    assert session.aborted
    print("  - Session active generation abort hook fired successfully.")
    
    # Verify that the FSM state was immediately transitioned to OBJECTION
    assert voice_manager.state_controller.context.current_state == "OBJECTION"
    print(f"  - State machine correctly forced to target state: {voice_manager.state_controller.context.current_state}")
    print("  => Voice Activity Detection interruption flow validated.\n")

    # ----------------------------------------------------
    # TEST 3: Sub-Agent Handover & Context Retention
    # ----------------------------------------------------
    print("[TEST 3] Testing Sub-agent Handover Context and Logic...")
    session_handover = MockAgentSession()
    state_ctx = CallStateContext(lead_metadata=lead_metadata, current_state="INITIATION")
    
    # Mocking handover call with a prospect objection utterance
    user_objection = "We don't have budget for any new platforms this quarter."
    rebuttal_text = await handle_sub_agent_handover(session_handover, state_ctx, user_objection)
    
    print(f"  - Current state inside context updated to: {state_ctx.current_state}")
    print(f"  - Objection count tracked inside context: {state_ctx.objection_count}")
    print(f"  - Objection history memory logs: {state_ctx.objection_history}")
    print(f"  - Sub-agent Voice Rebuttal output: '{rebuttal_text}'")
    
    assert state_ctx.current_state == "OBJECTION"
    assert state_ctx.objection_count == 1
    assert user_objection in state_ctx.objection_history
    print("  => Sub-agent handover and context routing validated successfully.\n")

    print("==================================================")
    print("ALL SIMULATION AND INTEGRATION HARNESS TESTS PASSED")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_simulation())
