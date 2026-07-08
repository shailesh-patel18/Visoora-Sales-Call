# Pilot Readiness Score

**Score: 45 / 100 (Hold Onboarding)**

## What does a "Pilot" mean?
A pilot customer knows the software might have bugs, but they expect their data to be safe, and they expect the core value proposition (AI outbound) to work reliably without burning their brand reputation.

## Why it's not ready
If we onboard 20 users today:
1. They will get stuck in a localhost redirect loop during email verification.
2. They will see generic Supabase emails, diminishing trust immediately.
3. If two pilot users use `@gmail.com` accounts, they will see each other's data due to the `email.split("@")[1]` tenant fallback.
4. If they launch a mission and navigate away from the dashboard, they might lose state because the frontend fakes the progress bar.

## The Pilot Launch Criteria
We will flip the switch to "Ready" ONLY when:
- [ ] Email verification redirects to the production domain.
- [ ] Resend is integrated with Visoora-branded HTML emails.
- [ ] Tenant ID is strictly enforced via DB UUIDs, never email domains.
- [ ] The "Approval Cockpit" is live, so users can edit AI drafts before sending.
