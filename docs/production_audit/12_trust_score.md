# Trust Score

**Score: 20 / 100**

## Why Trust is the Only Metric that Matters
Visoora is asking a CEO to connect their email domain and send messages on their behalf. If the system hallucinates, the CEO's reputation is destroyed. Trust is paramount.

## Trust Destroyers in Current Build
1. **Generic Emails:** "Confirm your email address" from `noreply@mail.app.supabase.io` screams "weekend project."
2. **Localhost Redirects:** If a user gets trapped on `localhost` during onboarding, they will churn immediately.
3. **Black Box AI:** When a draft is generated, the user does not see *why*. They have to blindly trust that the AI did good research.
4. **Faked UI:** Mocking progress bars breaks the illusion of control.

## Building Trust
1. **Premium Branding:** Implement Resend custom templates. Ensure SPF, DKIM, and DMARC are properly configured.
2. **Mission Replay (Explainable AI):** For every draft generated, log the thought process. 
   - *Example:* "I wrote 'Loved your post on Series A funding' because I found this LinkedIn post from 2 days ago: [Link]."
3. **Cockpit Control:** The user must have a massive, clear "APPROVE" or "REJECT" button. They must feel like the pilot, not a passenger.
