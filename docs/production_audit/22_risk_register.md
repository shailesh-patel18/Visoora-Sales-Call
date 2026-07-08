# Risk Register

## 1. Compliance Risk (GDPR / CAN-SPAM)
- **Risk:** Visoora sends cold emails on behalf of users. If the system enters a runaway loop or ignores "Unsubscribe" replies, the user's domain could be blacklisted, and legal fines could apply.
- **Mitigation:** Hardcoded volume limits per day in Redis. NLP parsing on all inbound replies to auto-detect opt-outs and add them to a global tenant blocklist.

## 2. Platform Dependency Risk
- **Risk:** Relying solely on OpenAI. If OpenAI alters its pricing, deprecates a model, or experiences a prolonged outage, Visoora dies.
- **Mitigation:** Implement the `BaseLLMProvider` abstraction. Ensure prompts are compatible (or mapped) to Claude 3.5 Sonnet.

## 3. Data Leakage Risk (Multi-Tenancy)
- **Risk:** Missing `WHERE tenant_id = x` clauses in SQLAlchemy ORM queries or bypassing RLS.
- **Mitigation:** Enforce Supabase RLS at the database layer. Even if the FastAPI backend makes a flawed query, Postgres will reject it based on the JWT context.

## 4. Brand Reputation Risk
- **Risk:** A pilot user launches a mission and it emails their top investor with hallucinated gibberish.
- **Mitigation:** The Approval Cockpit is mandatory. No emails send automatically until the user has built up a "Confidence Score" over time, and even then, safeguards must remain.
