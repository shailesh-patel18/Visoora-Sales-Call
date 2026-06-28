import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_google_key():
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        print("Google Key missing")
        return
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": "Hello, responding?"}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=body, timeout=5.0)
            if res.status_code == 200:
                print("[OK] Google API Key is VALID!")
                print("Response:", res.json()["candidates"][0]["content"]["parts"][0]["text"].strip())
            else:
                print(f"[FAIL] Google API Key is INVALID: {res.status_code} - {res.text}")
        except Exception as e:
            print("[FAIL] Google API call failed:", e)

async def test_openai_key():
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("OpenAI Key missing")
        return
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=body, headers=headers, timeout=5.0)
            if res.status_code == 200:
                print("[OK] OpenAI API Key is VALID!")
                print("Response:", res.json()["choices"][0]["message"]["content"].strip())
            else:
                print(f"[FAIL] OpenAI API Key is INVALID: {res.status_code} - {res.text}")
        except Exception as e:
            print("[FAIL] OpenAI API call failed:", e)

async def test_deepgram_key():
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")
    if not deepgram_key:
        print("Deepgram Key missing")
        return
    
    url = "https://api.deepgram.com/v1/projects"
    headers = {
        "Authorization": f"Token {deepgram_key}"
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, headers=headers, timeout=5.0)
            if res.status_code == 200:
                print("[OK] Deepgram API Key is VALID!")
            else:
                print(f"[FAIL] Deepgram API Key is INVALID: {res.status_code} - {res.text}")
        except Exception as e:
            print("[FAIL] Deepgram API call failed:", e)

async def main():
    print("Testing API Keys...")
    await test_google_key()
    await test_openai_key()
    await test_deepgram_key()

if __name__ == "__main__":
    asyncio.run(main())
