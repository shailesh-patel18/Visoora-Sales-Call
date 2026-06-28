import asyncio
import httpx

async def main():
    headers = {
        # Note: Do not provide authorization headers to let the endpoint fall back to local_dev_user sandbox mode.
    }
    
    payload = {
        "phone": "+919824457565",
        "name": "Shailesh Patel",
        "company": "Visoora"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== STEP 1: Triggering Outbound Call via Twilio ===")
        try:
            res = await client.post("http://localhost:8000/make-call", json=payload, headers=headers)
            print("Make Call Response Status Code:", res.status_code)
            print("Make Call Response JSON:", res.json())
        except Exception as e:
            print("Make Call API call failed:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
