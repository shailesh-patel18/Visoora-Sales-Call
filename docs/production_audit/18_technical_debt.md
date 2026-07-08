# Technical Debt

## 1. The "Fake It Till You Make It" Frontend
The frontend heavily relies on mocked data and simulated delays (e.g., `setTimeout` for progress bars). This was great for raising money or showing a demo, but it is crippling technical debt for production.
**Interest Payment:** Every time the backend changes, the frontend mock breaks or falls out of sync.

## 2. Tight LLM Coupling
Calling `OpenAI(api_key=...)` directly in business logic.
**Interest Payment:** If OpenAI goes down, the entire system halts. We cannot easily fall back to Anthropic. It also makes unit testing extremely difficult.

## 3. Naive Tenant Isolation
Using string splitting (`email.split("@")[1]`) as a fallback for tenant isolation.
**Interest Payment:** Massive security risk. Requires a complete database migration to enforce strict UUID-based `tenant_id` foreign keys on every table.

## 4. Lack of Event-Driven Architecture
Services call each other synchronously.
**Interest Payment:** High latency and cascading failures. If the email service is down, the mission engine fails, rather than just queuing the email for later.
