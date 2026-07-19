import httpx
import asyncio
import json

async def test():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/api/onboarding/analyze-domain", 
                json={"domain": "codetheorem.co"},
                headers={"Authorization": "Bearer SYSTEM_MOCK_TOKEN", "x-tenant-id": "system"},
                timeout=60.0
            )
            print(f"Status: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
