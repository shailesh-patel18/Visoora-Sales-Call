import asyncio
from server.job_handlers import prospecting_agent_handler
import uuid
import server.job_handlers as jh

jh.tenant_id_var.set("00000000-0000-0000-0000-000000000000")

async def test():
    try:
        job_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        res = await prospecting_agent_handler({"task_id": task_id, "icp_segment": "SaaS Companies"}, job_id)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
