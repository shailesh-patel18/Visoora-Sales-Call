# Top Prioritized Issues

This is a distilled list of the most critical issues blocking production readiness.

## [P0] Release Blockers (Must Fix Now)
1. **Insecure Frontend Middleware:** Next.js `middleware.ts` uses client-side boolean cookies instead of validating Supabase JWTs.
2. **Localhost Redirects:** Supabase confirmation emails redirect to `localhost:3000`.
3. **Generic Supabase Emails:** Lack of branded HTML templates via Resend.
4. **Tenant Isolation Flaw:** `rbac.py` uses email domain splitting (`@gmail.com`) as a fallback for tenant ID, exposing cross-tenant data.
5. **Localhost Auth Backdoor:** `rbac.py` grants admin rights to localhost requests when `APP_ENV=development`.

## [P1] Scalability & Security Hardening
6. **Synchronous AI Processing:** LLM calls block the Uvicorn worker pool. Must move to Celery/BullMQ.
7. **Fake Frontend State:** Dashboard uses `setTimeout` to mock mission progress instead of WebSockets.
8. **Missing Rate Limiting:** No per-tenant caps on the `/launch` endpoint, risking LLM budget exhaustion.
9. **Missing LLM Provider Abstraction:** Tight coupling to specific AI SDKs; no fallback logic.
10. **Lack of Explainability (No Mission Replay):** AI decisions are not logged with evidence and reasoning.

## [P2] UX & PMF Improvements
11. **Approval Cockpit:** Missing Diff/Inline edit UI for reviewing drafts before sending.
12. **Revenue-First Dashboard:** Metrics are currently arbitrary/mocked instead of pulling real Pipeline values.
13. **Hardcoded Secrets Check:** Server doesn't fail fast on boot if `OPENAI_API_KEY` is missing.
14. **Notification Service:** No abstracted provider to handle in-app, email, and SMS notifications unifiedly.
15. **Mission Configuration History:** Cannot pause, resume, or view history of missions.

## [P3] Tech Debt
16. **Missing Loading States:** Frontend lacks skeleton loaders and graceful error boundaries.
17. **Dead Code:** Unused endpoints and mock data scattered in `dashboard/page.tsx`.
18. **Strict Supabase Only:** Remove all JSON fallback logic and enforce strict Pydantic schemas.
19. **Unit Testing:** Missing end-to-end tests for the mission pipeline.
20. **Audit Logs:** No robust tracking of which user inside a tenant launched or approved a mission.
