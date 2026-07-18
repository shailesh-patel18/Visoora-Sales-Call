import asyncio
import uuid
import json
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from httpx import AsyncClient, ASGITransport

async def verify_pipeline():
    print("==================================================")
    print(" Visoora Phase 0: End-to-End Pipeline Verification")
    print("==================================================")
    
    from server.twilio_handler import app
    from server.storage_manager import supabase_admin_client
    
    if not supabase_admin_client:
        print("❌ Supabase Admin Client not configured. Ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set.")
        return

    tenant_id = "00000000-0000-0000-0000-000000000000"
    
    artifact_id = str(uuid.uuid4())
    sg_msg_id = f"mock-sg-{uuid.uuid4().hex[:8]}"
    
    # 1. Setup DB state (Simulate Sent Email)
    artifact = {
        "id": artifact_id,
        "tenant_id": tenant_id,
        "status": "SENT",
        "type": "email_draft",
        "artifact_type": "email_draft",
        "content": {"to_email": "e2e@example.com"},
        "metadata": {
            "sendgrid_message_id": sg_msg_id,
            "human_edited": True
        }
    }
    
    print(f"\n[*] STEP 1: Seeding mission_artifacts with artifact_id={artifact_id}")
    print(f"    - Assigned sendgrid_message_id={sg_msg_id}")
    supabase_admin_client.table("mission_artifacts").insert(artifact).execute()
    
    # 2. Trigger SendGrid Webhook
    print(f"\n[*] STEP 2: Triggering /api/public/webhooks/sendgrid")
    print(f"    - Simulating SendGrid sending batched OPEN and CLICK events...")
    webhook_payload = [
        {
            "event": "open",
            "sg_message_id": f"{sg_msg_id}.filterxyz"
        },
        {
            "event": "click",
            "sg_message_id": f"{sg_msg_id}.filterxyz",
            "url": "https://visoora.com/book-demo"
        }
    ]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/public/webhooks/sendgrid", json=webhook_payload)
        print("    - Webhook response:", res.status_code, res.json())
        
    # 3. Verify Tracking Metrics in DB
    print("\n[*] STEP 3: Verifying State Attribution in Supabase...")
    res = supabase_admin_client.table("mission_artifacts").select("metadata").eq("id", artifact_id).execute()
    metadata = res.data[0].get("metadata", {})
    tracking = metadata.get("tracking", {})
    
    print("    - Extracted Tracking Object:")
    print("      " + json.dumps(tracking, indent=6).replace('\n', '\n      '))
    
    if tracking.get("opens") == 1 and tracking.get("clicks") == 1:
        print("\n✅ Verification PASSED: State attribution correctly linked SendGrid events to artifact.")
    else:
        print("\n❌ Verification FAILED: Metrics did not update correctly.")
        
    # Cleanup
    supabase_admin_client.table("mission_artifacts").delete().eq("id", artifact_id).execute()

if __name__ == "__main__":
    asyncio.run(verify_pipeline())
