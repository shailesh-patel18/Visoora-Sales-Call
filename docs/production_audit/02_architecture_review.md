# Architecture Review

## Current State
The system is built as a monolithic FastAPI backend serving a Next.js (App Router) frontend. It utilizes Supabase for PostgreSQL and Auth. 

### Strengths
- **FastAPI:** Excellent choice for async Python operations, critical for AI workloads.
- **Supabase:** Strong choice for quick MVP iteration with built-in Postgres and Auth.
- **Next.js:** Solid frontend foundation with React Server Components.

### Critical Weaknesses
- **Synchronous AI Processing:** `mission_api.py` and AI provider calls are not properly queued. A long-running OpenAI request will hold open the HTTP connection, leading to 504 Gateway Timeouts.
- **Tight Coupling:** The AI logic directly invokes specific provider SDKs instead of utilizing a unified `LLMProvider` factory pattern.
- **State Management:** The frontend `dashboard` mocks state transitions rather than utilizing Server-Sent Events (SSE) or WebSockets to reflect true background worker progress.
- **Lack of Event-Driven Architecture:** The system polls or expects synchronous returns rather than publishing events to a broker (like Redis/Celery) and reacting.

## Recommendations
1. **Decouple the Mission Engine:** Move all AI processing to Celery/BullMQ workers. The FastAPI server should only ever *enqueue* a mission and return `202 Accepted`.
2. **Abstract AI Providers:** Create a `BaseLLMProvider` interface. All AI agents must depend on this interface, allowing the system to hot-swap between Claude 3.5 Sonnet and GPT-4o based on cost, latency, or rate limits.
3. **Implement Pub/Sub:** Use Redis Pub/Sub to push mission state updates to the FastAPI WebSocket manager, which then streams to the Next.js frontend for a truly reactive dashboard.
