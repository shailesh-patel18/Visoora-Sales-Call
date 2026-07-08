# Quick Wins (High Impact, Low Effort)

These items can be fixed in less than 4 hours total and will drastically improve the system's readiness.

1. **Fix Supabase Redirect URLs (5 mins)**
   - Log into Supabase -> Auth -> URL Configuration.
   - Set Site URL to the production domain. Add localhost to Additional URLs.
   
2. **Remove Localhost RBAC Backdoor (5 mins)**
   - Delete the `is_local_host` fallback block in `backend/security/rbac.py`.
   - Enforce JWT validation for all environments.

3. **Remove Domain Splitting Tenant Fallback (10 mins)**
   - In `rbac.py`, remove the `email.split("@")[1]` logic. If a token lacks a valid `tenant_id` claim, raise a `403 Forbidden`.

4. **Integrate Resend (1 hour)**
   - Swap the Supabase default SMTP for Resend.
   - Paste the custom HTML templates into the Supabase auth templates UI.

5. **Fix Frontend CORS/API URLs (15 mins)**
   - Ensure `NEXT_PUBLIC_API_URL` is used universally in the frontend instead of hardcoded `http://localhost:8000`.

6. **Add Rate Limiter Middleware (1 hour)**
   - Implement FastAPIs `SlowApi` or a simple Redis sliding window to cap `/launch` endpoints to 5 requests per hour per tenant.
