import asyncio
from typing import Any
from pipeline.states import CallStateContext

def tool(func):
    return func

@tool
async def trigger_sms_confirmation(phone_number: str, meeting_time: str) -> str:
    """
    Asynchronously fires an outbound meeting confirmation text message 
    without adding latency or blocking active playback streams.
    """
    # Emulate background execution via asyncio.create_task to keep voice streams non-blocking
    asyncio.create_task(mock_twilio_api_dispatch(phone_number, meeting_time))
    return "SMS action queued into background worker."

@tool
async def check_calendar_availability(date_str: str) -> str:
    """
    Checks the availability of calendar slots asynchronously without blocking the voice pipeline.
    """
    # Simulate a fast calendar slot lookup
    await asyncio.sleep(0.5)
    return f"Available slots found on {date_str} at 10:00 AM, 1:30 PM, and 4:00 PM."

async def mock_twilio_api_dispatch(phone: str, time: str):
    await asyncio.sleep(1.5) # Simulate Twilio API network round-trip delay
    print(f"[BG_WORKER] Twilio successfully dispatched text to {phone} for {time}")

async def handle_sub_agent_handover(session: Any, state_ctx: CallStateContext, user_utterance: str) -> str:
    """
    Triggered when state_ctx.current_state == 'OBJECTION'. 
    Extracts the conversation history, delegates the request to the 'ObjectionSpecialist' sub-agent,
    retrieves an ultra-concise voice-ready rebuttal response, and increments objection_count.
    """
    # Ensure current state context is correctly aligned
    state_ctx.state_history.append(state_ctx.current_state)
    state_ctx.current_state = "OBJECTION"
    state_ctx.objection_count += 1
    
    # Store objection into context history memory for cross-turn pattern recognition
    state_ctx.objection_history.append(user_utterance)

    # Formulate a structured payload for the sub-agent featuring conversation history
    history_str = " -> ".join(state_ctx.state_history)
    all_objections = ", ".join(f"'{obj}'" for obj in state_ctx.objection_history)
    
    sub_agent_prompt = (
        f"You are the ObjectionSpecialist sub-agent. The current conversation flow is: {history_str}. "
        f"This is a list of ALL objections raised in this call so far for context: [{all_objections}]. "
        f"The prospect just raised this new objection: '{user_utterance}'. "
        f"Inspect previous objections to avoid repetitive phrasing and build a highly relevant, customized rebuttal. "
        f"Respond in exactly one or two highly natural, professional sentences defusing the concern "
        f"and pivoting back to qualifying the lead."
    )

    # Establish robust interface compatibility for the Google Antigravity SDK
    rebuttal = "Right, I understand completely. Budget is always a primary consideration. Many of our current clients started right where you are before seeing their returns scale."
    
    try:
        if hasattr(session, "get_sub_agent"):
            sub_agent = session.get_sub_agent("ObjectionSpecialist")
            response = await sub_agent.generate_content(sub_agent_prompt)
            rebuttal = response.text if hasattr(response, "text") else str(response)
        elif hasattr(session, "delegate"):
            response = await session.delegate("ObjectionSpecialist", sub_agent_prompt)
            rebuttal = response.text if hasattr(response, "text") else str(response)
        elif hasattr(session, "sub_agents") and "ObjectionSpecialist" in session.sub_agents:
            sub_agent = session.sub_agents["ObjectionSpecialist"]
            response = await sub_agent.generate_content(sub_agent_prompt)
            rebuttal = response.text if hasattr(response, "text") else str(response)
        elif hasattr(session, "chat_with_sub_agent"):
            rebuttal = await session.chat_with_sub_agent("ObjectionSpecialist", sub_agent_prompt)
    except Exception as e:
        print(f"[HANDOVER_ERROR] Sub-agent delegation failed: {e}. Falling back to default guardrail rebuttal.")

    return rebuttal
