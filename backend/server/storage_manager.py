import os
import io
import wave
import uuid
import datetime
import struct
import asyncio
import json
from typing import Dict, Tuple, Optional, List
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

# ----------------------------------------------------
# SUPABASE CLIENT SETUP & CREDENTIAL LOAD
# ----------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Initialize client only if variables are loaded to avoid startup crashes
supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("[Storage Manager] Supabase Client Initialized Successfully.")
    except Exception as e:
        print(f"[Storage Manager] Error initializing Supabase: {e}")
else:
    print("[Storage Manager] Supabase credentials not found. Local recording storage active.")

# ----------------------------------------------------
# THREAD-SAFE STEREO CALL RECORDER SYSTEM
# ----------------------------------------------------
class CallSessionTracker:
    """
    Manages active call recordings in-memory using concurrent thread-safe locks.
    Interleaves Left (Prospect) and Right (AI Agent) audio channels to build stereo WAV files.
    """
    def __init__(self):
        # Maps stream_sid -> (left_buffer, right_buffer)
        self.buffers: Dict[str, Tuple[bytearray, bytearray]] = {}
        self.lock = asyncio.Lock()
        
        # Ensure a local directory exists for fallback recording persistence
        os.makedirs("recordings", exist_ok=True)
        self.local_registry_path = "recordings/local_call_logs.json"
        if not os.path.exists(self.local_registry_path):
            with open(self.local_registry_path, "w") as f:
                json.dump([], f)

    async def append_left(self, stream_sid: str, pcm_chunk: bytes):
        """Appends Prospect voice to the Left Channel and fills the Right Channel with silence."""
        async with self.lock:
            if stream_sid not in self.buffers:
                self.buffers[stream_sid] = (bytearray(), bytearray())
            
            left, right = self.buffers[stream_sid]
            left.extend(pcm_chunk)
            # Fill the right channel (AI) with equal length silence bytes (0x00)
            right.extend(b'\x00' * len(pcm_chunk))

    async def append_right(self, stream_sid: str, pcm_chunk: bytes):
        """Appends AI agent voice to the Right Channel and fills the Left Channel with silence."""
        async with self.lock:
            if stream_sid not in self.buffers:
                self.buffers[stream_sid] = (bytearray(), bytearray())
                
            left, right = self.buffers[stream_sid]
            right.extend(pcm_chunk)
            # Fill the left channel (Prospect) with equal length silence bytes (0x00)
            left.extend(b'\x00' * len(pcm_chunk))

    async def upload_recording(self, stream_sid: str, phone_number: str, final_state: str, tenant_id: str = "default_tenant", transcript: Optional[List[dict]] = None) -> str:
        """
        Compiles the call recording into a stereo WAV, uploads it to Supabase Storage (or local folder),
        and records structured call logs into Postgres (or a local registry) along with complete transcripts.
        """
        async with self.lock:
            buffer_pair = self.buffers.pop(stream_sid, None)
            
        if not buffer_pair:
            print(f"[Storage Manager] No call recording buffers found for SID: {stream_sid}")
            return ""

        left_bytes, right_bytes = buffer_pair
        if len(left_bytes) == 0 or len(right_bytes) == 0:
            print(f"[Storage Manager] Call buffer is empty for SID: {stream_sid}")
            return ""

        # Calculate exact duration (16000Hz, 16-bit Mono is 32000 bytes per second)
        duration_sec = int(len(left_bytes) / 32000)
        
        # 1. Compile left and right channels into a stereo WAV byte stream
        print(f"[Storage Manager] Compiling Stereo WAV for SID: {stream_sid} ({duration_sec}s)...")
        wav_data = self._compile_stereo_wav(bytes(left_bytes), bytes(right_bytes))
        
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"call_{stream_sid}_{timestamp}.wav"
        
        # Safe serializable transcript representation
        safe_transcript = transcript or []
        
        # 2. Resilient DB & Bucket uploads
        if supabase_client:
            try:
                # Upload .wav bytes asynchronously to the Supabase Storage Bucket
                bucket_name = f"recordings-{tenant_id}"
                res = supabase_client.storage.from_(bucket_name).upload(
                    path=filename,
                    file=wav_data,
                    file_options={"content-type": "audio/wav"}
                )
                
                # Fetch public bucket URL
                public_url = supabase_client.storage.from_(bucket_name).get_public_url(filename)
                
                # Insert telemetry row into call_logs table
                log_data = {
                    "id": str(uuid.uuid4()),
                    "phone_number": phone_number,
                    "duration_seconds": duration_sec,
                    "final_state": final_state,
                    "recording_url": public_url,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                    "transcript": safe_transcript
                }
                
                db_res = supabase_client.table("call_logs").insert(log_data).execute()
                print(f"[Storage Manager] Supabase upload & DB insertion success. Public URL: {public_url}")
                return public_url
                
            except Exception as e:
                print(f"[Storage Manager] Supabase storage upload failed: {e}. Cascading to local fallback.")
                
        # 3. Local Fallback Operations
        local_path = f"recordings/{filename}"
        with open(local_path, "wb") as f:
            f.write(wav_data)
            
        local_url = f"/recordings/{filename}"
        
        # Write to JSON registry
        log_entry = {
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "duration_seconds": duration_sec,
            "final_state": final_state,
            "recording_url": local_url,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "transcript": safe_transcript
        }
        
        try:
            with open(self.local_registry_path, "r+") as f:
                logs = json.load(f)
                logs.append(log_entry)
                f.seek(0)
                json.dump(logs, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"[Storage Manager] Error writing local log registry: {e}")
            
        print(f"[Storage Manager] Saved call to Local Storage: {local_path}")
        return local_url

    def _compile_stereo_wav(self, left_pcm: bytes, right_pcm: bytes) -> bytes:
        """Interleaves left and right linear PCM buffers to construct a valid 16-bit Stereo WAV."""
        min_len = min(len(left_pcm), len(right_pcm))
        
        # Unpack signed 16-bit short integers
        left_samples = struct.unpack(f"<{min_len // 2}h", left_pcm[:min_len])
        right_samples = struct.unpack(f"<{min_len // 2}h", right_pcm[:min_len])
        
        # Interleave: Left sample, Right sample, Left sample, Right sample...
        stereo_samples = []
        for l_sample, r_sample in zip(left_samples, right_samples):
            stereo_samples.append(l_sample)
            stereo_samples.append(r_sample)
            
        # Pack interleaved samples back into 16-bit signed shorts
        stereo_pcm = struct.pack(f"<{len(stereo_samples)}h", *stereo_samples)
        
        # Build WAV wrapper strictly in-memory
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(2) # Stereo!
            wav_file.setsampwidth(2) # 16-bit (2 bytes per sample)
            wav_file.setframerate(16000) # 16kHz
            wav_file.writeframes(stereo_pcm)
            
        return wav_io.getvalue()

# Singleton tracker instance
call_session_tracker = CallSessionTracker()
