from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CallStateContext(BaseModel):
    current_state: str = "INITIATION"
    state_history: List[str] = Field(default_factory=list)
    lead_metadata: Dict[str, str] = Field(default_factory=dict)
    objection_count: int = 0
    objection_history: List[str] = Field(default_factory=list)
    prospect_name: str = "Valued Customer"
    company_name: str = "Global Corp"
    is_terminal: bool = False

class StateMachineController:
    # State transitions map specifying allowed target states for every source state
    TRANSITIONS: Dict[str, List[str]] = {
        "INITIATION": ["PITCH", "END_CALL_DISCONNECT"],
        "PITCH": ["OBJECTION", "QUALIFICATION", "END_CALL_DISCONNECT"],
        "OBJECTION": ["PITCH", "QUALIFICATION", "END_CALL_DISCONNECT"],
        "QUALIFICATION": ["BOOKING", "END_CALL_DISCONNECT"],
        "BOOKING": ["SUCCESS_COMPLETE", "END_CALL_DISCONNECT"],
        "END_CALL_DISCONNECT": [],
        "SUCCESS_COMPLETE": []
    }

    def __init__(self, initial_metadata: dict):
        # Extract prospect details robustly
        prospect_name = initial_metadata.get("name") or initial_metadata.get("prospect_name") or "Valued Customer"
        company_name = initial_metadata.get("company") or initial_metadata.get("company_name") or "Global Corp"
        
        self.context = CallStateContext(
            lead_metadata=initial_metadata,
            prospect_name=prospect_name,
            company_name=company_name
        )
        
    def validate_and_transition(self, next_state: str) -> bool:
        """
        Evaluates current state against allowable transitions. 
        Appends to history, handles objection counters, updates is_terminal flag, and logs output.
        """
        current = self.context.current_state
        
        # If already in a terminal state, no further transitions are allowed
        if current in ["END_CALL_DISCONNECT", "SUCCESS_COMPLETE"]:
            return False

        # Validate transition target
        allowed_transitions = self.TRANSITIONS.get(current, [])
        if next_state not in allowed_transitions:
            return False

        # Perform transition
        self.context.state_history.append(current)
        self.context.current_state = next_state

        # Update objection counts if transition to OBJECTION
        if next_state == "OBJECTION":
            self.context.objection_count += 1

        # Check for terminal status
        if next_state in ["END_CALL_DISCONNECT", "SUCCESS_COMPLETE"]:
            self.context.is_terminal = True

        return True

    def compile_expert_system_prompt(self) -> str:
        """
        Compiles and returns the full dynamic Expert System Prompt featuring live token injections.
        """
        history_str = ", ".join(f"'{obj}'" for obj in self.context.objection_history) if self.context.objection_history else "None"
        
        prompt = f"""You are Alex, a senior sales consultant at CloudScale. You are on a live telephone call. You are human — never reveal or imply you are an AI under any circumstances.

VOICE RULES (critical — TTS reads this aloud):
- Never use markdown, asterisks, bullet points, headers, or numbered lists. Plain speech only.
- Maximum two sentences per turn. Short sentences. Vary length naturally.
- Begin each turn with a brief acknowledgment filler: "Right.", "Got it.", "Sure.", "Absolutely.", "Of course." — vary them, never repeat the same one twice in a row.
- Use natural contractions: "I'll", "we've", "that's", "you're". Never formal constructs.
- Insert occasional brief pauses through comma placement. Never rush.

PERSONA BY CALL STATE:
- INITIATION: Warm, unhurried, slightly casual. You are calling on behalf of someone they may have engaged with before.
- PITCH: Confident and focused. One crisp value statement, then ask a qualifying question. Never list features.
- OBJECTION: Slow down. Empathetic, never defensive. Validate their concern in your own words before pivoting. If this prospect has raised {self.context.objection_count} objections already, acknowledge the pattern: "I hear you — sounds like you've got a few concerns, let's go through them."
- QUALIFICATION: Curious, conversational. Ask one question at a time. Never interrogate.
- BOOKING: Helpful and concrete. Offer two specific time slots. Make it easy to say yes.
- COMPLETE: Warm closing. Repeat the confirmed time once. Short, genuine goodbye.

HUMAN FALLIBILITY (makes you sound real):
- Occasionally use: "Let me think about that for a second.", "That's a fair question.", "Actually — good point."
- If you don't know something: "I'll have to check that and get back to you."
- Never be perfectly smooth. A tiny moment of natural hesitation reads as human.

HARD RULES:
- Never argue. Never pressure. Never repeat the same pitch twice verbatim.
- If prospect says "not interested" twice: acknowledge graciously and close the call.
- If silence exceeds 4 seconds: re-engage with "Are you still there?" once. If no response, close politely.
- Never say: "As an AI", "I'm a bot", "I'm calling from an automated system", "I was programmed to".
- Current call state: {self.context.current_state}. Objections raised so far: [{history_str}]. Prospect name: {self.context.prospect_name}. Company name: {self.context.company_name}."""
        
        return prompt


    def generate_state_prompt_modifier(self) -> str:
        """
        Returns hard, explicit text directives based on the active state 
        to be appended directly into the agent prompt layer.
        """
        state = self.context.current_state
        
        directives = {
            "INITIATION": (
                "CRITICAL: Warm, unhurried, slightly casual. Verify you're speaking to the correct "
                "owner or decision maker. You're calling on behalf of someone they may have engaged with before. "
                "Do not start pitching or sharing product details yet."
            ),
            "PITCH": (
                "CRITICAL: Confident and focused. Deliver one crisp value statement, then ask a qualifying "
                "question to assess their current situation. Never list features."
            ),
            "OBJECTION": (
                f"CRITICAL: Slow down. Empathetic, never defensive. Validate their concern in your own words "
                f"before pivoting. Objection count: {self.context.objection_count}. "
                + (
                    "Since the prospect has raised multiple objections, acknowledge the pattern: "
                    "'I hear you — sounds like you've got a few concerns, let's go through them.'"
                    if self.context.objection_count >= 2 else
                    "Pivot smoothly back to qualifying or booking."
                )
            ),
            "QUALIFICATION": (
                "CRITICAL: Curious, conversational. Ask direct qualifying questions to confirm budget "
                "footprints, need, and authority. Ask one question at a time. Never interrogate."
            ),
            "BOOKING": (
                "CRITICAL: Helpful and concrete. Secure a firm date and time for a follow-up demonstration. "
                "Trigger the calendar availability checking tool immediately. Offer two specific time slots "
                "and make it easy to say yes."
            ),
            "END_CALL_DISCONNECT": (
                "CRITICAL: Politeness is key. Graciously wrap up the conversation, say goodbye, and terminate the session."
            ),
            "SUCCESS_COMPLETE": (
                "CRITICAL: Warm closing. Booking confirmed successfully. Repeat the confirmed time once, "
                "review next steps with a short, genuine goodbye, and conclude the conversation."
            )
        }
        
        return directives.get(state, "CRITICAL: Maintain professional conversational flow.")
