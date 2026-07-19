import httpx
import asyncio

async def test():
    key = "AIzaSyD95zPOtzsDZwkWLjj2j3V5uSplclQ8ph0"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "gemini-2.0-flash", "messages": [{"role": "user", "content": "say ok"}]}
            )
            print(f"Status: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
