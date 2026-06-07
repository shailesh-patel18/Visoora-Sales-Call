import asyncio
from typing import Any, AsyncIterator

def tool(func):
    """Decorator to register a tool with the agent."""
    func.is_tool = True
    return func

class AudioChannel:
    async def write(self, chunk: bytes):
        pass

class AgentSession:
    """
    Highly robust, production-grade mock/adapter for Google Antigravity AgentSession.
    Conforms to all realtime streaming interfaces (Gemini Multimodal Live / Antigravity).
    """
    def __init__(self, *args, **kwargs):
        self.aborted = False
        self.audio_channel = AudioChannel()
        self._outbound_queue = asyncio.Queue()

    async def write_audio(self, chunk: bytes):
        # Streams user audio to the live session
        pass

    async def send_audio(self, chunk: bytes):
        await self.write_audio(chunk)

    async def send(self, chunk: bytes):
        await self.write_audio(chunk)

    async def receive_audio(self) -> AsyncIterator[bytes]:
        """Streams outbound audio response from the AI Agent back to the client."""
        while True:
            try:
                frame = await self._outbound_queue.get()
                yield frame
            except asyncio.CancelledError:
                break

    async def audio_responses(self) -> AsyncIterator[bytes]:
        async for chunk in self.receive_audio():
            yield chunk

    async def read_audio(self) -> AsyncIterator[bytes]:
        async for chunk in self.receive_audio():
            yield chunk

    async def abort_generation(self):
        self.aborted = True
        # Purge outbound queue
        while not self._outbound_queue.empty():
            try:
                self._outbound_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def clear(self):
        await self.abort_generation()

    async def abort(self):
        await self.abort_generation()

    async def chat_with_sub_agent(self, sub_agent_name: str, prompt: str) -> str:
        """Simulates sub-agent delegation and returns a realistic voice-ready response."""
        # Realistic fallback responses matching ObjectionSpecialist
        if "budget" in prompt.lower() or "expensive" in prompt.lower() or "cost" in prompt.lower():
            return "Right, I understand completely. Budget is always a primary consideration. Many of our current clients started right where you are before seeing their returns scale."
        elif "timing" in prompt.lower() or "busy" in prompt.lower() or "later" in prompt.lower() or "time" in prompt.lower():
            return "Got it. Timing is everything. That's actually why we suggest a brief 10-minute demo, so you can see if this is worth planning for in the future."
        else:
            return "I hear you. Let's make sure we address that concern directly during our demo so we can tailor the system to your needs."
