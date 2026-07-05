import asyncio
import time
import pytest
from fastapi.testclient import TestClient
from server.twilio_handler import app
from sales_employee.mailbox_manager import connect_mailbox
from sales_employee.services import store

@pytest.mark.asyncio
async def test_concurrent_sends_keep_loop_responsive():
    client = TestClient(app)
    
    tenant_id = "test_tenant_async_bench"
    email = "bench@acme.com"
    
    # Register a lead
    lead = {
        "id": "lead_bench_1",
        "tenant_id": tenant_id,
        "name": "Benchmark Lead",
        "company_name": "Benchmark",
        "email": "bench_target@acme.com",
        "agent_id": "agent_123"
    }
    store.insert("leads", lead)
    
    # Connect a mailbox
    connect_mailbox(tenant_id, email, "smtp", {"host": "mock_smtp"}, is_default=True)
    
    # Define an async task to call health check
    async def call_health():
        loop = asyncio.get_running_loop()
        start = time.time()
        # TestClient is synchronous, run it in a thread so it doesn't block the loop
        response = await loop.run_in_executor(None, lambda: client.get("/health"))
        elapsed = time.time() - start
        assert response.status_code == 200
        return elapsed

    # Define an async task to trigger email send
    async def trigger_send():
        # Setup headers
        headers = {"X-Tenant-ID": tenant_id, "Authorization": "Bearer mock_token"}
        loop = asyncio.get_running_loop()
        # Trigger send
        response = await loop.run_in_executor(
            None, 
            lambda: client.post(f"/api/v1/sales-employee/leads/{lead['id']}/emails/send", headers=headers)
        )
        return response.status_code

    # Measure health baseline
    baseline_time = await call_health()
    
    # Trigger 20 concurrent email sends and health checks interleaved
    tasks = []
    for _ in range(20):
        tasks.append(trigger_send())
    tasks.append(call_health())
    
    results = await asyncio.gather(*tasks)
    
    health_elapsed = results[-1]
    # Health checks should be extremely responsive (sub-50ms) as the loops are not blocked by synchronous SMTP
    assert health_elapsed < 0.200 # Under 200ms in testing environments
    logger_str = f"Baseline latency: {baseline_time:.4f}s, Concurrency burst health check latency: {health_elapsed:.4f}s"
    print(logger_str)
