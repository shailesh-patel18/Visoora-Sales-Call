import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

sql = """
CREATE TABLE IF NOT EXISTS public.ai_cache (
    url_hash text PRIMARY KEY,
    url text NOT NULL,
    brain_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);
"""
# Try to run it via rpc if there is an exec_sql function
try:
    res = supabase.rpc("exec_sql", {"query": sql}).execute()
    print("Execution via RPC succeeded.")
except Exception as e:
    print(f"RPC failed: {e}")
