import asyncio
from server.job_handlers import voice_agent_handler
from contextvars import ContextVar
import server.job_handlers as jh

jh.tenant_id_var.set("system_tenant")

async def test():
    try:
        res = await voice_agent_handler({"task_id": "test_123", "name": "John Doe"}, "job_test")
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
