import math
import struct
import asyncio

class VoiceActivityDetector:
    def __init__(self, threshold: float = 300.0):
        self.threshold = threshold

    def calculate_frame_energy(self, pcm_frame: bytes) -> float:
        """Computes the numerical RMS energy value of an explicit 16-bit PCM chunk."""
        if not pcm_frame:
            return 0.0
        
        # Verify signed 16-bit PCM chunk (2 bytes per sample)
        count = len(pcm_frame) // 2
        if count == 0:
            return 0.0
        
        # Unpack signed 16-bit little-endian samples
        samples = struct.unpack(f"<{count}h", pcm_frame[:count*2])
        
        # Calculate Root Mean Square energy
        sum_squares = sum(float(sample) ** 2 for sample in samples)
        rms = math.sqrt(sum_squares / count)
        return rms

    async def monitor_and_interrupt(self, pcm_frame: bytes, voice_manager_instance):
        """
        Evaluates energy against threshold. 
        If crossed and agent is currently speaking, flushes queues and signals an active abort.
        """
        energy = self.calculate_frame_energy(pcm_frame)
        if energy > self.threshold:
            # Check if agent is currently speaking/streaming outbound frames
            is_speaking = False
            if hasattr(voice_manager_instance, "is_speaking") and voice_manager_instance.is_speaking:
                is_speaking = True
            elif not voice_manager_instance.outbound_queue.empty():
                is_speaking = True

            if is_speaking:
                print(f"[VAD] Interruption detected! RMS Energy: {energy:.2f} > Threshold: {self.threshold}")
                
                # 1. Purge all items currently held inside the voice player's outbound_queue
                while not voice_manager_instance.outbound_queue.empty():
                    try:
                        voice_manager_instance.outbound_queue.get_nowait()
                        voice_manager_instance.outbound_queue.task_done()
                    except (asyncio.QueueEmpty, ValueError):
                        break
                
                # 2. Invoke the Antigravity SDK session's explicit clear/abort function (session.abort_generation())
                session = voice_manager_instance.session
                try:
                    if hasattr(session, "abort_generation"):
                        await session.abort_generation()
                    elif hasattr(session, "clear"):
                        await session.clear()
                    elif hasattr(session, "abort"):
                        await session.abort()
                except Exception as e:
                    print(f"[VAD] Failed to abort active agent generation: {e}")

                # 3. Change the active conversational state machine tracker immediately to target state OBJECTION.
                if hasattr(voice_manager_instance, "state_controller"):
                    voice_manager_instance.state_controller.validate_and_transition("OBJECTION")
                elif hasattr(session, "state_controller"):
                    session.state_controller.validate_and_transition("OBJECTION")
