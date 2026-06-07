import pytest
import uuid
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Adjust path context
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from server.twilio_handler import app
from server.session_registry import session_registry, SessionRegistry

client = TestClient(app)

# ----------------------------------------------------
# TEST GROUP 1: HEALTH AND TELEMETRY PROBES
# ----------------------------------------------------
def test_liveness_check():
    """Asserts that /health/live returns a 200 and simple health flags."""
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["live"] is True

def test_readiness_check_success():
    """Asserts that /health/ready returns ready status under normal capacity."""
    # We patch ping check and twilio ping connection to return 200
    with patch("server.session_registry.redis_client") as mock_redis:
        mock_redis.ping.return_value = True
        
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock Twilio reachability check
            mock_get.return_value = MagicMock(status_code=200)
            
            res = client.get("/health/ready")
            assert res.status_code == 200
            assert res.json()["status"] == "ready"

def test_readiness_check_shutdown_drops_traffic():
    """Asserts /health/ready immediately fails with 503 during graceful SIGTERM drains."""
    with patch("server.twilio_handler.is_shutting_down", True):
        res = client.get("/health/ready")
        assert res.status_code == 503
        assert res.json()["status"] == "unready"
        assert res.json()["reason"] == "shutting_down"

def test_readiness_check_capacity_overload():
    """Asserts that /health/ready drops out of Ingress rotation (503) when exceeding 50 calls."""
    with patch("server.twilio_handler.active_calls_count", 55):
        res = client.get("/health/ready")
        assert res.status_code == 503
        assert res.json()["status"] == "unready"
        assert res.json()["reason"] == "capacity_full"

def test_prometheus_metrics_export():
    """Asserts that /health/metrics returns custom formatted Prometheus gauges."""
    res = client.get("/health/metrics")
    assert res.status_code == 200
    metrics_text = res.text
    
    assert "active_calls" in metrics_text
    assert "cluster_active_calls" in metrics_text
    assert "avg_call_latency_ms" in metrics_text
    assert "vad_interruptions_total" in metrics_text

# ----------------------------------------------------
# TEST GROUP 2: REDIS SESSION REGISTRY & STATE STORE
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_session_registry_registration_lifecycle():
    """Validates session registration, lookup, and cluster count calculations."""
    registry = SessionRegistry()
    stream_sid = f"MZtest_{str(uuid.uuid4())[:8]}"
    pod_id = "test-pod-abc"
    
    # 1. New registration
    await registry.register_session(stream_sid, pod_id)
    assert await registry.get_session_pod(stream_sid) == pod_id
    assert await registry.get_active_streams_count() == 1
    
    # 2. Deregistration
    await registry.deregister_session(stream_sid)
    assert await registry.get_session_pod(stream_sid) is None
    assert await registry.get_active_streams_count() == 0

@pytest.mark.asyncio
async def test_fsm_state_persistence_and_failover_recovery():
    """Validates FSM state hashes store, recover, and delete dynamically."""
    registry = SessionRegistry()
    stream_sid = f"MZtest_{str(uuid.uuid4())[:8]}"
    
    call_state = {
        "current_state": "ENGAGEMENT",
        "objection_count": 2,
        "interrupted": True,
        "caller_name": "Bruce Wayne"
    }
    
    # 1. Persist state
    await registry.persist_call_state(stream_sid, call_state)
    
    # 2. Reconstitute state (Failover recovery simulation)
    recovered_state = await registry.load_call_state(stream_sid)
    assert recovered_state == call_state
    
    # 3. Clear state
    await registry.clear_call_state(stream_sid)
    assert await registry.load_call_state(stream_sid) is None

# ----------------------------------------------------
# TEST GROUP 3: WEBSOCKET ROUTING INTERCEPT FOR TRANSPARENT PROXY
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_websocket_intercepts_wrong_node_routing():
    """
    Asserts that if a websocket session lands on a node different from its
    registered owner, the socket intercepts the call to establish transparent proxying.
    """
    stream_sid = "MZproxy_999"
    wrong_pod = "pod-B"
    right_pod = "pod-A"
    
    # Set the registered owner to pod-A
    await session_registry.register_session(stream_sid, right_pod)
    
    with patch("os.getenv", return_value=wrong_pod): # Current node is pod-B
        # We mock websockets.connect to simulate transparent forwarding
        with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            # Use websocket_connect inside TestClient to test routing intercept
            with client.websocket_connect(f"/media-stream?phone=%2b123&name=Alice&company=Acme") as ws:
                ws.send_json({"event": "connected"})
                # Send the 'start' frame which resolves stream_sid and triggers the proxy check
                ws.send_json({
                    "event": "start",
                    "start": {
                        "streamSid": stream_sid,
                        "callSid": "CAproxy_999"
                    }
                })
                
                # Sleep briefly for async loops to execute forwarding trigger
                ws.send_json({"event": "stop"})
                
            # Verify that the websocket client connected to the internal GKE DNS of the correct pod!
            assert mock_connect.call_count == 1
            call_url = mock_connect.call_args[0][0]
            assert f"ws://{right_pod}.audio-processor-service.default.svc.cluster.local:8000/media-stream" in call_url
            
    # Cleanup
    await session_registry.deregister_session(stream_sid)
