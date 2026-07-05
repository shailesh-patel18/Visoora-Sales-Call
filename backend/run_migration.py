import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("SUPABASE credentials not found.")
    exit(1)

supabase = create_client(url, key)

with open("db/migrations/02_phase3_missions.sql", "r") as f:
    sql = f.read()

print("Please run db/migrations/02_phase3_missions.sql in the Supabase SQL Editor manually.")
