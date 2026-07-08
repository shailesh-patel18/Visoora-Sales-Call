# Launch Checklist (Pre-Pilot)

Before onboarding the first 20 pilot customers, ALL boxes below must be checked.

## Security & Auth
- [ ] Next.js middleware refactored to use `@supabase/ssr`.
- [ ] Localhost dev fallbacks removed from `rbac.py`.
- [ ] Email domain tenant fallback removed; strict UUIDs enforced.
- [ ] Supabase RLS policies enabled and verified on all tables.
- [ ] Rate limits applied to `/launch` and `/generate` endpoints.

## Infrastructure & Routing
- [ ] All `localhost:3000` URLs removed from Supabase Auth settings.
- [ ] `NEXT_PUBLIC_API_URL` properly configured in Vercel.
- [ ] `NEXT_PUBLIC_SITE_URL` properly configured in Vercel.
- [ ] Custom domain verified with Resend for SMTP.

## Architecture
- [ ] Synchronous AI calls removed from FastAPI endpoints.
- [ ] Celery/BullMQ workers implemented for Mission Engine.
- [ ] Redis configured for task queue and rate limiting.

## UX & Trust
- [ ] Branded HTML templates active in Supabase (Welcome, Verification, Reset).
- [ ] Approval Cockpit built (Diff, Edit, Mass Approve).
- [ ] Mock `setTimeout` progress bars replaced with WebSocket/SSE polling.
- [ ] Mission Replay data (AI reasoning) visible to users.
