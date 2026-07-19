import asyncio
from server.onboarding_api import in_house_crawl
from server.ai_gateway import gateway

async def test():
    print("Running in_house_crawl...")
    scrape_data = await in_house_crawl("codetheorem.co")
    print(f"Scrape completed, {len(scrape_data.get('pages', []))} pages found.")
    
    print("Running extract_business_brain...")
    extraction = await gateway.extract_business_brain(
        url="codetheorem.co", 
        structured_data=scrape_data, 
        source_url="codetheorem.co"
    )
    
    print("\n--- EXTRACTION RESULTS ---")
    print(extraction.model_dump_json(indent=2))

asyncio.run(test())
