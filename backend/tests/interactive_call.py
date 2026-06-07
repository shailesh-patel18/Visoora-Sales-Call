import sys
import os
import asyncio
import struct
import math

# Force UTF-8 encoding on Windows console to support emojis and unicode checkmarks
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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

from pipeline.states import StateMachineController
from pipeline.vad import VoiceActivityDetector
from pipeline.tools import handle_sub_agent_handover, trigger_sms_confirmation, check_calendar_availability
from pipeline.states import CallStateContext

# ANSI colors for styling
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
WHITE_ON_BLUE = "\033[37;44m"
DARK_GRAY = "\033[90m"

class MockAgentSession:
    def __init__(self):
        self.aborted = False

    async def abort_generation(self):
        self.aborted = True

# A helper to simulate speech playout with character delays
async def agent_speak(text: str):
    print(f"\n{BOLD}{CYAN}📞 Voice Agent:{RESET} ", end="", flush=True)
    # Start with a clean verbal stream (following voice guardrails: no markdown, concise)
    clean_text = text.replace("**", "").replace("*", "").replace("`", "")
    for char in clean_text:
        print(char, end="", flush=True)
        await asyncio.sleep(0.015)
    print("\n")

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{BOLD}{WHITE_ON_BLUE}                                                      {RESET}")
    print(f"{BOLD}{WHITE_ON_BLUE}    OUTBOUND VOICE AGENT INTERACTIVE CONSOLE HARNESS  {RESET}")
    print(f"{BOLD}{WHITE_ON_BLUE}                                                      {RESET}\n")
    print(f"{DARK_GRAY}This harness lets you roleplay as the prospect in real time.")
    print(f"Watch the FSM state machine transitions, tool calls, and VAD engine respond.{RESET}\n")
    
    # 1. Collect lead metadata to populate state context
    print(f"{BOLD}{YELLOW}--- STEP 1: INITIALIZE LEAD CONTEXT ---{RESET}")
    name = input(f"{BOLD}Enter Prospect's Name {RESET}[default: Alice Smith]: ").strip() or "Alice Smith"
    company = input(f"{BOLD}Enter Company Name {RESET}[default: Acme Corp]: ").strip() or "Acme Corp"
    phone = input(f"{BOLD}Enter Phone Number {RESET}[default: +1 555-0199]: ").strip() or "+1 555-0199"
    
    lead_metadata = {"name": name, "company": company, "phone": phone}
    fsm = StateMachineController(initial_metadata=lead_metadata)
    vad = VoiceActivityDetector(threshold=300.0)
    session = MockAgentSession()
    
    print(f"\n{GREEN}✔ Call established with {name} at {company} ({phone}).{RESET}")
    print(f"{DARK_GRAY}Starting state: {BOLD}{fsm.context.current_state}{RESET}\n")

    # 2. Interactive Loop
    # INITIATION state greeting
    await agent_speak(f"Hello, is this {name} from {company}? My name is Alex, and I'm calling from CloudScale.")

    while not fsm.context.is_terminal:
        # Print FSM State details & helper instructions
        print(f"{DARK_GRAY}[FSM State: {BOLD}{fsm.context.current_state}{DARK_GRAY}] Objection Count: {fsm.context.objection_count}{RESET}")
        print(f"{DARK_GRAY}Prompt Directive: {fsm.generate_state_prompt_modifier()}{RESET}")
        
        # Display helpful commands based on active state
        options = []
        if fsm.context.current_state == "INITIATION":
            options.append(f"'{GREEN}yes{RESET}' (confirm owner) | '{RED}no{RESET}' (wrong person)")
        elif fsm.context.current_state == "PITCH":
            options.append(f"'{GREEN}interested{RESET}' (hear pitch) | '{YELLOW}objection{RESET}' (raise budget concern)")
        elif fsm.context.current_state == "QUALIFICATION":
            options.append(f"'{GREEN}looks good{RESET}' (qualify) | '{YELLOW}objection{RESET}' (raise timing concern)")
        elif fsm.context.current_state == "OBJECTION":
            options.append(f"'{GREEN}makes sense{RESET}' (accept rebuttal) | '{YELLOW}objection{RESET}' (raise another objection)")
        elif fsm.context.current_state == "BOOKING":
            options.append(f"'{GREEN}schedule{RESET}' (book slot) | '{RED}disconnect{RESET}' (hang up)")
            
        options.append(f"'{RED}exit{RESET}' (hang up) | '{BOLD}type [interrupt]{RESET}' (simulate VAD interruption)")
        print(f"{BOLD}Options:{RESET} {', '.join(options)}")
        
        # User input prompt
        try:
            user_input = input(f"{BOLD}{GREEN}👤 You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            user_input = "exit"

        if not user_input:
            continue

        # Check for simulated interruption (VAD trigger)
        if "[interrupt]" in user_input.lower() or user_input.isupper() and len(user_input) > 5:
            print(f"\n{RED}⚡ [VAD] Interruption Detected! Simulated high-energy speech detected (RMS > 300.0).{RESET}")
            print(f"{DARK_GRAY}→ Purging active playout queue and calling session.abort_generation()...{RESET}")
            await session.abort_generation()
            
            # Transition immediately to OBJECTION
            if fsm.context.current_state in ["PITCH", "QUALIFICATION", "BOOKING", "INITIATION"]:
                fsm.validate_and_transition("OBJECTION")
                print(f"{YELLOW}→ State machine forced from state to: {BOLD}OBJECTION{RESET}")
                
            # Perform sub-agent handover
            rebuttal = await handle_sub_agent_handover(session, fsm.context, "Hey, stop talking, listen to me!")
            await agent_speak(rebuttal)
            continue

        if user_input.lower() in ["exit", "no", "disconnect"]:
            fsm.validate_and_transition("END_CALL_DISCONNECT")
            await agent_speak("I understand. Thank you for your time, and hope you have a great rest of your day. Goodbye!")
            print(f"\n{RED}🔌 Call disconnected. State: {fsm.context.current_state} (Terminal){RESET}")
            break

        # Flow Routing based on input keywords
        current = fsm.context.current_state

        if current == "INITIATION":
            if "yes" in user_input.lower() or "speaking" in user_input.lower():
                fsm.validate_and_transition("PITCH")
                await agent_speak(
                    "Wonderful! The reason I'm reaching out is that we help fast-growing teams like yours "
                    "automate their scheduling and scale outbound operations by over 40% while cutting costs in half. "
                    "Does scaling outbound operations sound like something you are currently focusing on?"
                )
            else:
                await agent_speak("Ah, I apologize. Could you connect me with the decision maker, or should I call back later?")
                fsm.validate_and_transition("END_CALL_DISCONNECT")
                print(f"\n{RED}🔌 Call disconnected. State: {fsm.context.current_state} (Terminal){RESET}")

        elif current == "PITCH":
            if "objection" in user_input.lower() or any(w in user_input.lower() for w in ["budget", "expensive", "money", "cost"]):
                fsm.validate_and_transition("OBJECTION")
                print(f"\n{MAGENTA}🤖 [HANDOVER] Activating 'ObjectionSpecialist' sub-agent...{RESET}")
                rebuttal = await handle_sub_agent_handover(session, fsm.context, user_input)
                await agent_speak(rebuttal)
            else:
                fsm.validate_and_transition("QUALIFICATION")
                await agent_speak(
                    "Great! To make sure this is a perfect fit, may I ask: how many calls is your team "
                    "making per week, and are you currently using an automated platform?"
                )

        elif current == "QUALIFICATION":
            if "objection" in user_input.lower() or any(w in user_input.lower() for w in ["timing", "busy", "later", "time"]):
                fsm.validate_and_transition("OBJECTION")
                print(f"\n{MAGENTA}🤖 [HANDOVER] Activating 'ObjectionSpecialist' sub-agent...{RESET}")
                rebuttal = await handle_sub_agent_handover(session, fsm.context, user_input)
                await agent_speak(rebuttal)
            else:
                fsm.validate_and_transition("BOOKING")
                await agent_speak(
                    "Got it. It sounds like you are the perfect candidate for our custom platform. "
                    "I'd love to show you a quick 10-minute demo. Let me check my calendar availability real quick."
                )
                print(f"\n{CYAN}⚙ [TOOL] Invoking 'check_calendar_availability' asynchronously...{RESET}")
                slots = await check_calendar_availability("next Monday")
                print(f"{GREEN}✔ Tool returned: {slots}{RESET}")
                await agent_speak("I have open slots next Monday at 10:00 AM or 1:30 PM. Which of those works best for you?")

        elif current == "OBJECTION":
            if "objection" in user_input.lower() or any(w in user_input.lower() for w in ["budget", "timing", "not interested"]):
                print(f"\n{MAGENTA}🤖 [HANDOVER] Activating 'ObjectionSpecialist' sub-agent...{RESET}")
                rebuttal = await handle_sub_agent_handover(session, fsm.context, user_input)
                await agent_speak(rebuttal)
            else:
                # Pivot back to pitch or qualification
                fsm.validate_and_transition("QUALIFICATION")
                await agent_speak(
                    "I'm glad that makes sense! Moving forward, do you have 5 to 10 minutes next week "
                    "for a quick demo so you can see how the platform works visually?"
                )

        elif current == "BOOKING":
            if "schedule" in user_input.lower() or any(w in user_input.lower() for w in ["10", "1:30", "monday", "ok", "yes", "sure", "book"]):
                # Complete the booking
                print(f"\n{CYAN}⚙ [TOOL] Invoking 'trigger_sms_confirmation' in background...{RESET}")
                sms_res = await trigger_sms_confirmation(phone, "next Monday at 10:00 AM")
                print(f"{GREEN}✔ Tool returned: {sms_res}{RESET}")
                
                fsm.validate_and_transition("SUCCESS_COMPLETE")
                await agent_speak(
                    "Fantastic! I've booked you in for next Monday at 10:00 AM, and I just sent a confirmation "
                    "text message to your phone. It was wonderful speaking with you. Have a great day!"
                )
                
                # Yield to let the SMS background worker complete printing its message
                await asyncio.sleep(2.0)
                print(f"\n{GREEN}🏆 Booking successfully completed! State: {fsm.context.current_state} (Terminal){RESET}")
            else:
                fsm.validate_and_transition("END_CALL_DISCONNECT")
                await agent_speak("No problem at all. If anything changes, feel free to reach out. Have a wonderful day!")
                print(f"\n{RED}🔌 Call disconnected. State: {fsm.context.current_state} (Terminal){RESET}")

    print(f"\n{BOLD}{WHITE_ON_BLUE}               SIMULATION RUN COMPLETED               {RESET}\n")

if __name__ == "__main__":
    asyncio.run(main())
