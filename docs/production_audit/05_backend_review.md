# Backend Review (FastAPI)

## General Assessment
The FastAPI backend is structured reasonably well but lacks the defensive programming required for an enterprise system. 

## Critical Issues

### 1. The Localhost Backdoor
**File:** `backend/security/rbac.py`
The authentication logic contains a "Development Fallback" that grants Admin privileges if `APP_ENV=development` and the request comes from localhost.
**Risk:** If environment variables leak or are misconfigured in production, this is a catastrophic privilege escalation vulnerability.
**Fix:** Remove this backdoor. Development environments should use real (test) JWTs.

### 2. Blocking I/O
If AI provider calls (OpenAI/Anthropic) are made synchronously within the API request lifecycle (e.g., `await client.chat.completions.create(...)`), a sudden spike in latency from OpenAI will exhaust the Uvicorn worker pool, bringing down the entire API.
**Fix:** All LLM generation must happen in a separate Celery/BullMQ worker pool, totally detached from the API HTTP lifecycle.

### 3. Tenant ID Extraction
**File:** `backend/security/rbac.py`
If a token lacks a `tenant_id`, the system splits the user's email domain to generate one (`email.split("@")[1]`). 
**Risk:** This means `john@gmail.com` and `sarah@gmail.com` share the `gmail.com` tenant and can see each other's data. 
**Fix:** Strict UUID linkage. If a user is not bound to a `public.tenants` UUID in the database, they are unauthorized. Domain splitting is unacceptable for B2B.

### 4. Lack of Notification Abstraction
Notifications (SMS, Email) are hardcoded into endpoints or specific services.
**Fix:** Implement an event-driven `NotificationService` that listens for `DRAFT_APPROVED` or `MISSION_COMPLETED` events and handles the delivery via abstract providers (ResendProvider, TwilioProvider).
