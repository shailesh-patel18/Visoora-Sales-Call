import asyncio
from dotenv import load_dotenv
load_dotenv()
from server.ai_gateway import gateway

async def test():
    print("Running generate_icps_from_brain...")
    try:
        extraction = await gateway.generate_icps_from_brain(
            {"url": "codetheorem.co"}
        )
        print("\n--- ICP GENERATION RESULTS ---")
        print(extraction.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
