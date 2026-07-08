# Production Readiness Score

**Score: 35 / 100 (Not Ready)**

## Why?
Visoora is currently a highly functional prototype. It demonstrates the value proposition perfectly in a controlled environment, but it lacks the non-functional requirements (NFRs) necessary for a public, unmonitored launch.

## Deficit Breakdown

### 1. Resilience (10/25)
The system lacks robust worker queues. A temporary failure from OpenAI will result in a lost mission. No dead-letter queues. No exponential backoff.

### 2. Security (5/25)
Localhost backdoors in RBAC, naive email-domain tenant isolation, and client-side cookie middleware checks make the system extremely vulnerable to horizontal privilege escalation.

### 3. Observability (5/25)
We lack tracing for AI decisions. If a user asks "Why did the AI send this email?", we have no logs to prove the AI's intent. `structlog` and Sentry are required.

### 4. Scalability (15/25)
FastAPI and Supabase are highly scalable by default, giving Visoora a strong foundation. However, the synchronous execution of LLM tasks completely negates this advantage.

## Path to 80/100
1. Remove all mock transitions.
2. Implement strict RLS and `@supabase/ssr`.
3. Offload all AI workloads to a Celery/Redis worker cluster.
