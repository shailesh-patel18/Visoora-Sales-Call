import asyncio
import httpx

async def main():
    headers = {
        "X-Tenant-ID": "test_verification_tenant"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        print("1. Creating Agent...")
        agent_payload = {
            "name": "Maya",
            "persona_config": {
                "agent_name": "Maya",
                "company_name": "Visoora",
                "tone": "direct",
                "value_proposition": "reduce response time"
            }
        }
        res = await client.post("http://localhost:8000/api/v1/sales-employee/agents", json=agent_payload, headers=headers)
        print("Agent Create Response:", res.status_code, res.json())
        agent_id = res.json()["id"]
        
        print("\n2. Ingesting Knowledge Chunk...")
        kb_payload = {
            "source_file": "pricing.txt",
            "text": "Visoora offers premium onboarding and a compliance-first outbound engine for regulated sales teams."
        }
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/agents/{agent_id}/knowledge/text", json=kb_payload, headers=headers)
        print("Knowledge Ingestion Response:", res.status_code, res.json())
        
        print("\n3. Creating Lead & Triggering Research...")
        lead_payload = {
            "agent_id": agent_id,
            "name": "Dana",
            "company_name": "Example Corp",
            "website": "example.com",
            "email": "dana@example.com",
            "phone": "+15005550111"
        }
        res = await client.post("http://localhost:8000/api/v1/sales-employee/leads", json=lead_payload, headers=headers)
        print("Lead Ingestion & Research Response:", res.status_code, res.json())
        lead_id = res.json()["id"]
        
        print("\n4. Running Strategy Engine Decision...")
        res = await client.post(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/decide", headers=headers)
        print("Strategy Decision Response:", res.status_code, res.json())
        
        print("\n5. Fetching Lead Timeline...")
        res = await client.get(f"http://localhost:8000/api/v1/sales-employee/leads/{lead_id}/timeline", headers=headers)
        print("Lead Timeline Response:", res.status_code, res.json())

if __name__ == "__main__":
    asyncio.run(main())
