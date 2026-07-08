# Frontend Review (Next.js)

## General Assessment
The frontend utilizes modern React (Next.js App Router, Tailwind, Framer Motion) but suffers from "MVP Syndrome" — it looks good but the underlying logic is brittle, mocked, and insecure.

## Critical Issues

### 1. Insecure Route Protection
**File:** `frontend/middleware.ts`
The middleware checks for a client-side boolean cookie: `request.cookies.get("visoora_logged_in") === "true"`. 
**Risk:** An attacker can manually set this cookie and access protected routes. While API calls might fail, they can map the entire internal UI and potentially exploit client-side logic.
**Fix:** Implement `@supabase/ssr` to securely decode and validate the JWT on the edge before rendering.

### 2. Mocked State Transitions
**File:** `frontend/app/dashboard/page.tsx`
The mission state transitions from "LAUNCHING" to "RUNNING" using a `setTimeout` of 4.5 seconds.
**Risk:** If the backend fails, the frontend still shows success. If the backend takes 10 seconds, the frontend is out of sync.
**Fix:** The frontend must consume real-time events (WebSocket or SSE) from the backend to update state.

### 3. Missing Loading/Error Boundaries
Next.js `loading.tsx` and `error.tsx` are underutilized. API failures result in silent console errors rather than graceful UI recovery.

### 4. Hardcoded URLs
The codebase likely contains direct references to `http://localhost:8000`. This must be completely replaced with `NEXT_PUBLIC_API_URL` environment variables.
