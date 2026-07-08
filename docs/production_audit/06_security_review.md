# Security Review

## Authentication
- **Finding:** The Next.js middleware relies on `visoora_logged_in=true`.
- **Severity:** CRITICAL
- **Risk:** Complete bypass of frontend routing protection.
- **Remediation:** Implement `@supabase/ssr` to securely decode and validate the JWT from `sb-access-token` cookies.

## Authorization & RBAC
- **Finding:** The `get_current_user` dependency in FastAPI has a development backdoor granting `admin` to any request on `localhost` when `APP_ENV=development`.
- **Severity:** HIGH
- **Risk:** If `APP_ENV` leaks in production, an attacker could spoof localhost headers or leverage SSRF to gain admin rights.
- **Remediation:** Remove local dev fallbacks. Always validate real JWTs or M2M API keys.

## Tenant Isolation (Row Level Security)
- **Finding:** Currently, if a JWT lacks a `tenant_id` claim, the system falls back to splitting the email domain (`tenant_id = email.split("@")[1]`).
- **Severity:** CRITICAL
- **Risk:** Cross-tenant data exposure. Users sharing a domain (e.g., `@gmail.com`) instantly share a tenant workspace.
- **Remediation:** Remove domain splitting entirely. A user without a valid `tenant_id` mapping in a `user_tenants` lookup table must be denied access (`403 Forbidden`). Enforce strict Postgres RLS policies: `tenant_id = auth.jwt()->>'tenant_id'`.

## API Abuse & Rate Limiting
- **Finding:** `api_rate_limiter.py` exists but needs to enforce hard daily limits on AI generation endpoints (`/api/v1/missions/launch`).
- **Severity:** HIGH
- **Risk:** A malicious user or runaway loop can exhaust OpenAI credits, costing thousands of dollars.
- **Remediation:** Bind rate limits to `tenant_id` using Redis sliding windows. Cap LLM calls per tenant per day.

## Secrets Management
- **Finding:** Hardcoded `.env.example` keys or loose checking.
- **Severity:** MEDIUM
- **Remediation:** Enforce Pydantic BaseSettings strict validation on startup. If `OPENAI_API_KEY` is missing in production, the server should crash on boot, not during a user request.
