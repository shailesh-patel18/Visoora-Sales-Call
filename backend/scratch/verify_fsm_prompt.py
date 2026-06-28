"""
Quick FSM validation: tests INITIATION → DISCOVERY → PITCH → OBJECTION → BOOKING → TRANSFER_TO_HUMAN path
Run from: backend/ directory
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.states import StateMachineController

def test_full_happy_path():
    fsm = StateMachineController({"name": "John Doe", "company": "Acme", "phone": "+15005550006"}, "default_shared_tenant")
    assert fsm.context.current_state == "INITIATION", "Should start in INITIATION"

    assert fsm.validate_and_transition("DISCOVERY"), "INITIATION → DISCOVERY should succeed"
    assert fsm.context.current_state == "DISCOVERY"

    assert fsm.validate_and_transition("PITCH"), "DISCOVERY → PITCH should succeed"
    assert fsm.context.current_state == "PITCH"

    assert fsm.validate_and_transition("OBJECTION"), "PITCH → OBJECTION should succeed"
    assert fsm.context.current_state == "OBJECTION"
    assert fsm.context.objection_count == 1

    assert fsm.validate_and_transition("QUALIFICATION"), "OBJECTION → QUALIFICATION should succeed"
    assert fsm.context.current_state == "QUALIFICATION"

    assert fsm.validate_and_transition("BOOKING"), "QUALIFICATION → BOOKING should succeed"
    assert fsm.context.current_state == "BOOKING"

    assert fsm.validate_and_transition("SUCCESS_COMPLETE"), "BOOKING → SUCCESS_COMPLETE should succeed"
    assert fsm.context.current_state == "SUCCESS_COMPLETE"
    assert fsm.context.is_terminal, "SUCCESS_COMPLETE should be terminal"

    # Terminal state guard
    assert not fsm.validate_and_transition("OBJECTION"), "Terminal state should not allow transitions"
    print("✅ Happy path test passed: INITIATION → DISCOVERY → PITCH → OBJECTION → QUALIFICATION → BOOKING → SUCCESS_COMPLETE")

def test_transfer_to_human():
    fsm = StateMachineController({"name": "Jane", "company": "Beta Corp", "phone": "+15005550007"}, "default_shared_tenant")
    assert fsm.validate_and_transition("DISCOVERY")
    assert fsm.validate_and_transition("PITCH")
    assert fsm.validate_and_transition("TRANSFER_TO_HUMAN"), "PITCH → TRANSFER_TO_HUMAN should succeed"
    assert fsm.context.current_state == "TRANSFER_TO_HUMAN"
    assert fsm.context.is_terminal, "TRANSFER_TO_HUMAN should be terminal"
    assert not fsm.validate_and_transition("DISCOVERY"), "Terminal TRANSFER_TO_HUMAN should block further transitions"
    print("✅ TRANSFER_TO_HUMAN test passed: warm handoff state is terminal and correctly blocked from re-entry")

def test_prompt_compilation():
    fsm = StateMachineController({"name": "Bob", "company": "Tech Co", "phone": "+15005550008"}, "default_shared_tenant")
    prompt = fsm.compile_expert_system_prompt()
    assert "INITIATION" in prompt or "consultative" in prompt, "Prompt should contain state-level context"
    modifier = fsm.generate_state_prompt_modifier()
    assert "CRITICAL" in modifier, "State modifier must have CRITICAL directive"
    print(f"✅ Prompt compilation test passed. Prompt length: {len(prompt)} chars | Modifier: '{modifier[:80]}...'")

def test_objection_reentry():
    fsm = StateMachineController({"name": "Alice", "company": "Sales Inc", "phone": "+15005550009"}, "default_shared_tenant")
    fsm.validate_and_transition("DISCOVERY")
    fsm.validate_and_transition("PITCH")
    fsm.validate_and_transition("OBJECTION")
    assert fsm.context.objection_count == 1
    fsm.validate_and_transition("PITCH")  # Return from objection
    fsm.validate_and_transition("OBJECTION")  # Second objection
    assert fsm.context.objection_count == 2
    modifier = fsm.generate_state_prompt_modifier()
    assert "multiple objections" in modifier.lower() or "objection count" in modifier.lower(), "Multiple objection count should appear in modifier"
    print(f"✅ Re-entrant OBJECTION test passed: objection_count={fsm.context.objection_count}")

if __name__ == "__main__":
    print("\n=== Visoora FSM Validation Suite ===\n")
    test_full_happy_path()
    test_transfer_to_human()
    test_prompt_compilation()
    test_objection_reentry()
    print("\n=== ALL FSM TESTS PASSED ✅ ===\n")
