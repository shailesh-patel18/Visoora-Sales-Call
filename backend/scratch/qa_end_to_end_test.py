import asyncio
import httpx

async def main():
    headers = {
        "X-Tenant-ID": "acme_tenant"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== STEP 1: Creating AI Agent configured to sell Website Design & Development ===")
        agent_payload = {
            "name": "Visoora Design Consultant",
            "persona_config": {
                "agent_name": "Maya",
                "company_name": "Visoora Developers",
                "tone": "consultative",
                "value_proposition": "premium website design and development services to scale businesses"
            }
        }
        res = await client.post("http://localhost:8000/api/v1/sales-employee/agents", json=agent_payload, headers=headers)
        print("Agent Create Response:", res.status_code, res.json())
        agent_id = res.json()["id"]
        
        print("\n=== STEP 2: Ingesting Product Knowledge ===")
        kb_payload = {
            "source_file": "services_offered.txt",
            "text": "We build highly responsive, premium custom web designs, Next.js applications, SEO services, and fast loading web portals to maximize customer acquisition and business growth."
        }
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/agents/{agent_id}/knowledge/text", json=kb_payload, headers=headers)
        print("Knowledge Ingestion Response:", res.status_code, res.json())
        
        print("\n=== STEP 3: Creating Lead Shailesh Patel & Running Research ===")
        lead_payload = {
            "agent_id": agent_id,
            "name": "Shailesh Patel",
            "company_name": "Visoora",
            "website": "visoora.com",
            "email": "sp1862004@gmail.com",
            "phone": "+919824457565"
        }
        res = await client.post("http://localhost:8000/api/v1/sales-employee/leads", json=lead_payload, headers=headers)
        print("Lead Ingestion & Research Response:", res.status_code, res.json())
        lead_id = res.json()["id"]
        
        print("\n=== STEP 4: Strategy Decision 1 (Should decide to send a personalized email) ===")
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/decide", headers=headers)
        print("First Decision:", res.status_code, res.json())
        
        print("\n=== STEP 5: Generating Custom Drafted Email ===")
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/emails/draft", headers=headers)
        print("Generated Email Draft:", res.status_code)
        draft = res.json()
        print("Subject:", draft.get("subject"))
        print("Body:\n", draft.get("body"))
        
        print("\n=== STEP 6: Attempting to Send Email ===")
        # Note: If SENDGRID_API_KEY is not set, this will fall back or fail. Let's see what happens.
        try:
            res = await client.post(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/emails/send", headers=headers)
            print("Send Email Response:", res.status_code, res.json())
        except Exception as e:
            print("Send Email error:", str(e))
            
        print("\n=== STEP 7: Strategy Decision 2 (After touch 1) ===")
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/decide", headers=headers)
        print("Second Decision:", res.status_code, res.json())

        print("\n=== STEP 8: Timeline History ===")
        res = await client.get(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/timeline", headers=headers)
        print("Timeline:", res.status_code, res.json())

if __name__ == "__main__":
    asyncio.run(main())
