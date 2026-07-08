# Scalability Score

**Score: 30 / 100**

## Will this support 10 users?
**Yes.** 10 users generating a few emails a day will run fine on the current synchronous FastAPI architecture, though they will occasionally experience 504 Gateway Timeouts if OpenAI latency spikes.

## Will this support 100 users?
**No.** 100 concurrent users launching missions will immediately exhaust the Uvicorn worker pool. The API will lock up. Database connections will max out because connections are held open while waiting for LLM generation.

## Will this support 1,000+ users?
**Absolutely not.** The architecture fundamentally breaks down at scale because of synchronous AI task execution.

## The Scalability Fixes
1. **Asynchronous Worker Queue:** 
   Move all logic currently residing in `mission_api.py` into a robust queue system (Celery with Redis broker). The FastAPI endpoint should look like this:
   `POST /mission -> return {"status": "queued", "job_id": 123}`
2. **Database Connection Pooling:**
   Ensure SQLAlchemy is configured with PgBouncer or Supabase connection pooling (using the IPv4 connection pooler string, not the direct IPv6 string).
3. **WebSockets via Redis Pub/Sub:**
   A single FastAPI instance cannot hold 10,000 active WebSockets easily without a Pub/Sub backplane. If the backend scales horizontally to 3 nodes, a mission executing on Node A must be able to push a WebSocket event to the user connected to Node B via Redis.
