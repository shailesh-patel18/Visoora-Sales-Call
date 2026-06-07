import time
import json
import base64
import uuid
from locust import task, HttpUser, between
import websocket

# A baseline silent G.711 u-law frame payload (20ms packet: 160 bytes)
# Base64 encoded payload: 160 bytes of 0xFF (standard silent byte)
SILENT_ULAW_BASE64 = base64.b64encode(b'\xff' * 160).decode("utf-8")

class VisooraVoIPUser(HttpUser):
    """
    Simulates high-concurrency real-time outbound callers.
    Generates background HTTP health telemetry scrapes and bridges to persistent real-time WebSockets
    streaming simulated conversation voice payloads.
    """
    # Simulate a rest period of 1 to 5 seconds between user actions
    wait_time = between(1, 5)

    @task(3)
    def test_http_health_probes(self):
        """Scrapes standard infrastructure health probes periodically."""
        self.client.get("/health/live", name="GET /health/live")
        self.client.get("/health/ready", name="GET /health/ready")
        self.client.get("/health/metrics", name="GET /health/metrics")

    @task(1)
    def simulate_realtime_voip_call(self):
        """
        Bridges an active outbound cold call session, establishing a bi-directional
        real-time WebSocket audio link, and streaming base64 voice packets sequentially.
        """
        # Resolve target host (e.g. localhost:8000 -> ws://localhost:8000/media-stream)
        http_host = self.host.replace("http://", "").replace("https://", "")
        ws_url = f"ws://{http_host}/media-stream?phone=%2b15017122661&name=LocustTest&company=LoadTest&tenant_id=acme_tenant"
        
        start_time = time.time()
        stream_sid = f"MZlocust_{str(uuid.uuid4())[:8]}"
        call_sid = f"CAlocust_{str(uuid.uuid4())[:8]}"

        try:
            # 1. Open WebSocket connection
            ws = websocket.create_connection(ws_url, timeout=5)
            
            # 2. Transmit handshakes
            ws.send(json.dumps({"event": "connected"}))
            ws.send(json.dumps({
                "event": "start",
                "start": {
                    "streamSid": stream_sid,
                    "callSid": call_sid,
                    "customParameters": {
                        "phone": "+15017122661",
                        "name": "LocustTest",
                        "company": "LoadTest"
                    }
                }
            }))
            
            # 3. Stream sequential audio packets representing a 10-second active dialogue conversation
            for packet_index in range(500): # 500 packets * 20ms = 10.0 seconds of dialogue speech
                # Check socket open state
                if not ws.connected:
                    break
                    
                payload = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": SILENT_ULAW_BASE64,
                        "timestamp": str(packet_index * 20)
                    }
                }
                ws.send(json.dumps(payload))
                
                # Enforce low-latency 20ms G.711 stream interval
                time.sleep(0.02)
                
                # Check for return announcements from the AI Voice agent periodically
                if packet_index % 25 == 0:
                    ws.settimeout(0.001) # Non-blocking check
                    try:
                        resp = ws.recv()
                        # Successfully received audio return stream from AI agent!
                    except websocket.WebSocketTimeoutException:
                        pass # No packet waiting in queue buffer
                        
            # 4. Transmit tear-down disconnect event
            if ws.connected:
                ws.send(json.dumps({"event": "stop", "streamSid": stream_sid}))
                ws.close()
                
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="VoIP Audio Call Stream",
                response_time=int((time.time() - start_time) * 1000),
                response_length=0,
                exception=None
            )
            
        except Exception as exc:
            self.environment.events.request.fire(
                request_type="WebSocket",
                name="VoIP Audio Call Stream Failed",
                response_time=int((time.time() - start_time) * 1000),
                response_length=0,
                exception=exc
            )
