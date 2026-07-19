import asyncio
import uuid
from server.job_handlers import email_agent_handler

async def test():
    try:
        # Mock tenant_id_var since email_agent_handler uses tenant_id_var.get()
        import contextvars
        from server.job_handlers import tenant_id_var
        tenant_id_var.set("00000000-0000-0000-0000-000000000000")
        
        job_id = str(uuid.uuid4())
        result = await email_agent_handler({"task_id": str(uuid.uuid4()), "goal": "sell Visoora SaaS"}, job_id)
        print("\n--- EMAIL DRAFT RESULTS ---")
        print(result)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
