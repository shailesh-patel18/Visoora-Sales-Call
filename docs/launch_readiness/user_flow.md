# End-to-End User Flow
**Product:** Visoora AI Revenue Operating System

This document maps the complete journey for a new user, documenting interactions between the user, frontend, backend, database, and AI agents.

---

### 1. Landing & Signup
* **Purpose:** Introduce Visoora and convert visitor to user.
* **Frontend:** `/signup` (Next.js)
* **Backend Endpoint:** Supabase Auth (`/auth/v1/signup`)
* **Database:** `auth.users`
* **User Emotion:** Curious, hopeful.
* **Trust Indicators:** Clean UI, SSL, fast load time.
* **Failure States:** Email already in use, weak password.

### 2. Email Verification
* **Purpose:** Validate identity and prevent spam.
* **Event:** Supabase sends confirmation email via Resend.
* **Frontend:** Magic link redirects to `/auth/callback` -> `/dashboard`
* **Email Template:** `verify_email.html` (Branded)
* **Failure States:** Email goes to spam, link expires, local redirect issue.
* **Recovery:** "Resend verification email" button.

### 3. Onboarding / Business Brain Configuration
* **Purpose:** Provide the AI with context about the user's business.
* **Frontend:** `/onboarding` or `/business-map`
* **Backend Endpoint:** `POST /api/v1/tenant/business-brain`
* **Database:** `tenants`, `business_context`
* **AI Agents:** Context Analyzer (extracts key value props from user input).
* **User Emotion:** Engaged but potentially overwhelmed if too long.
* **Trust Indicators:** AI auto-completion, helpful tooltips.

### 4. Mission Configuration
* **Purpose:** Define the goal, target audience, and constraints for the AI.
* **Frontend:** `/campaigns/new` or `/command-center`
* **Backend Endpoint:** `POST /api/v1/missions`
* **Database:** `missions`
* **AI Agents:** Planning Agent (reviews parameters and suggests improvements).
* **Expected Time:** 2-5 minutes.

### 5. Launch Mission (Queue)
* **Purpose:** Dispatch the mission to background workers.
* **Event:** Mission status changes to `QUEUED`.
* **Backend:** Redis + Celery/BullMQ task created.
* **Notification:** In-app toast "Mission Launched".
* **User Emotion:** Anticipation, excitement.

### 6. AI Research & Execution
* **Purpose:** AI acts autonomously to find leads and generate drafts.
* **Backend:** Async Python Workers.
* **AI Agents:** 
  - **Research Agent:** Scrapes data, qualifies leads.
  - **Copywriting Agent:** Drafts personalized emails.
* **Database:** `leads`, `email_drafts`
* **Expected Time:** 5-15 minutes (background).

### 7. Approval Inbox (CEO Review)
* **Purpose:** Human-in-the-loop validation before sending emails.
* **Event:** Email sent to user (`approval_required.html`).
* **Frontend:** `/inbox` or `/approval`
* **Backend Endpoint:** `GET /api/v1/drafts/pending` -> `POST /api/v1/drafts/{id}/approve`
* **User Emotion:** Control, satisfaction seeing AI's work.
* **Trust Indicators:** Explainability (showing *why* the AI wrote what it wrote).

### 8. Email Sending & Reply Detection
* **Purpose:** Dispatch approved emails and monitor for responses.
* **Backend:** SMTP/API integration (e.g., SendGrid/Resend) and IMAP polling.
* **Database:** `communications`, `replies`
* **AI Agents:** Intent Classification Agent (Positive, Negative, Meeting Request).

### 9. Meeting Booked
* **Purpose:** Convert positive replies into calendar events.
* **Event:** Positive reply detected.
* **Notification:** Email (`meeting_booked.html`) + In-app.
* **Frontend:** `/pipeline` or `/calls`

### 10. Mission Results & Learning Loop
* **Purpose:** Report ROI and improve future missions.
* **Frontend:** `/report`
* **Backend Endpoint:** `GET /api/v1/missions/{id}/analytics`
* **Database:** `mission_stats`
* **User Emotion:** Validation, high retention trigger.
* **Event:** System updates the "Business Brain" based on what messaging worked best.
