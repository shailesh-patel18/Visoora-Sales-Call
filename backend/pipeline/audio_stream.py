import asyncio
from google.antigravity import AgentSession

class VoicePipelineManager:
    def __init__(self, session: AgentSession):
        self.session = session
        self.inbound_queue = asyncio.Queue()
        self.outbound_queue = asyncio.Queue()
        self.is_streaming = False

    async def register_transport_handlers(self, pipecat_transport):
        """
        Bind inbound WebRTC/telephony audio frames directly to populate self.inbound_queue.
        Bind self.outbound_queue to push chunks down to the physical playback/telephony channel.
        """
        # Callback to handle inbound frames from WebRTC/telephony
        async def on_inbound_audio(frame: bytes):
            if self.is_streaming:
                await self.inbound_queue.put(frame)

        # Robustly register the audio callback based on supported Pipecat transport interfaces
        if hasattr(pipecat_transport, "register_audio_in_callback"):
            await pipecat_transport.register_audio_in_callback(on_inbound_audio)
        elif hasattr(pipecat_transport, "on_audio_frame"):
            pipecat_transport.on_audio_frame = on_inbound_audio
        elif hasattr(pipecat_transport, "set_audio_in_handler"):
            await pipecat_transport.set_audio_in_handler(on_inbound_audio)

        # Dispatch outbound audio frames to transport in the background
        async def outbound_dispatcher():
            while self.is_streaming:
                frame = await self.outbound_queue.get()
                try:
                    if hasattr(pipecat_transport, "write_audio_frame"):
                        await pipecat_transport.write_audio_frame(frame)
                    elif hasattr(pipecat_transport, "send_audio"):
                        await pipecat_transport.send_audio(frame)
                    elif hasattr(pipecat_transport, "output"):
                        await pipecat_transport.output(frame)
                except Exception:
                    pass
                finally:
                    self.outbound_queue.task_done()

        asyncio.create_task(outbound_dispatcher())

    async def stream_ingress_loop(self):
        """
        Continuously pulls raw 640-byte chunks from self.inbound_queue 
        and forwards them immediately into the active Antigravity session audio channel.
        """
        while self.is_streaming:
            try:
                chunk = await self.inbound_queue.get()
                
                # Ensure the frame chunk size is precisely 640 bytes (20ms interval)
                if len(chunk) != 640:
                    if len(chunk) < 640:
                        chunk = chunk.ljust(640, b'\x00')
                    else:
                        chunk = chunk[:640]

                # Robustly forward audio to Antigravity session depending on API version
                if hasattr(self.session, "write_audio"):
                    await self.session.write_audio(chunk)
                elif hasattr(self.session, "send_audio"):
                    await self.session.send_audio(chunk)
                elif hasattr(self.session, "audio_channel") and hasattr(self.session.audio_channel, "write"):
                    await self.session.audio_channel.write(chunk)
                else:
                    await self.session.send(chunk)
            except Exception:
                pass
            finally:
                self.inbound_queue.task_done()

    async def stream_egress_loop(self):
        """
        Listens to the Antigravity SDK session's raw audio response output stream,
        slices it into 640-byte chunks, and appends them to self.outbound_queue.
        """
        buffer = bytearray()
        
        # Determine the appropriate raw audio streaming generator on the session object
        if hasattr(self.session, "receive_audio"):
            audio_generator = self.session.receive_audio()
        elif hasattr(self.session, "audio_responses"):
            audio_generator = self.session.audio_responses()
        elif hasattr(self.session, "read_audio"):
            audio_generator = self.session.read_audio()
        else:
            audio_generator = self.session

        try:
            async for response_chunk in audio_generator:
                if not self.is_streaming:
                    break
                
                # Extract bytes robustly
                if isinstance(response_chunk, (bytes, bytearray)):
                    buffer.extend(response_chunk)
                elif hasattr(response_chunk, "data"):
                    buffer.extend(response_chunk.data)

                # Slice audio into precise 640-byte chunks (20ms intervals at 16000Hz, 16-bit Mono)
                while len(buffer) >= 640:
                    chunk = bytes(buffer[:640])
                    del buffer[:640]
                    await self.outbound_queue.put(chunk)
        except Exception:
            pass

    async def execute_pipeline(self, pipecat_transport):
        self.is_streaming = True
        await self.register_transport_handlers(pipecat_transport)
        await asyncio.gather(
            self.stream_ingress_loop(),
            self.stream_egress_loop()
        )
