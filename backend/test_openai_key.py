import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    key = os.getenv("OPENAI_API_KEY")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "say ok"}]}
            )
            print(f"Status: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
