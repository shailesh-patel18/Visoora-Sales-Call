import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    key = os.getenv("APOLLO_API_KEY")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.apollo.io/v1/contacts/search",
            headers={"Cache-Control": "no-cache", "Content-Type": "application/json", "X-Api-Key": key},
            json={
                "q_keywords": "SaaS Companies",
                "per_page": 5
            }
        )
        print(f"Status: {resp.status_code}")
        print(resp.text)

asyncio.run(test())
