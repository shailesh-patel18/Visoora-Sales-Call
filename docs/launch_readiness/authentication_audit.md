# Authentication & Security Audit Report
**Scope:** Visoora Supabase Auth & Session Management

## Current Architecture
- **Provider:** Supabase Auth
- **Frontend Framework:** Next.js (App Router)
- **Backend Framework:** FastAPI
- **Session Strategy:** JWT tokens stored in cookies (`visoora_logged_in`).
- **Middleware:** Next.js `middleware.ts` for route protection.

## Weaknesses & Production Risks

### 1. Hardcoded Redirect URLs (Release Blocker)
**Issue:** The confirmation email redirects users to `http://localhost:3000/...` instead of the production domain.
**Impact:** Users cannot verify their accounts or log in on the production instance.
**Fix Required:** 
- In Supabase Dashboard: Navigate to **Authentication > URL Configuration**.
- Set the **Site URL** to the production domain (e.g., `https://visoora.com`).
- Add development and preview URLs (e.g., `http://localhost:3000`) to the **Additional Redirect URLs**.
- Ensure the frontend uses `NEXT_PUBLIC_SITE_URL` for any programmatic redirects.

### 2. Default Supabase Email Templates (Brand Risk)
**Issue:** Users receive a generic "Confirm your email address" email from `noreply@mail.app.supabase.io`.
**Impact:** Looks unprofessional, reduces trust, hurts conversion.
**Fix Required:** 
- Integrate a custom SMTP provider (like Resend).
- Configure Supabase to use the custom SMTP.
- Replace all default templates with Visoora-branded HTML emails (Welcome, Verify, Reset Password).

### 3. Middleware Session Validation
**Issue:** `middleware.ts` currently checks for a generic `visoora_logged_in` boolean cookie.
**Impact:** This is insecure. A user can manually set this cookie to `true` and bypass frontend protection (though API calls might still fail if JWT is checked).
**Fix Required:**
- Use the official `@supabase/ssr` package.
- Update `middleware.ts` to actually validate the Supabase session via `supabase.auth.getUser()`. This ensures the JWT is valid and unexpired before rendering private routes.

### 4. Supabase RLS (Row Level Security)
**Issue:** If RLS is not properly configured, JWTs alone don't prevent users from accessing other tenants' data.
**Impact:** Multi-tenant data leak.
**Fix Required:**
- Audit `auth.users` linkages to `public.tenants` or `public.users`.
- Ensure policies look like: `(auth.uid() = user_id)` or `(tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()))`.

### 5. Password Reset Flow
**Issue:** If redirect URLs are misconfigured, password reset emails will also trap users on localhost.
**Fix Required:** Same as the redirect fix. Needs end-to-end testing in a staging environment.

## Priority Action Items
1. **Fix Supabase Redirect URLs** (P0)
2. **Implement Resend SMTP & Custom Emails** (P0)
3. **Refactor Next.js Middleware to use `@supabase/ssr`** (P1)
4. **Audit and enforce Database RLS Policies** (P1)
