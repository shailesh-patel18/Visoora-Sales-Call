# Visoora: Granular End-to-End System Architecture

This document breaks down every single micro-interaction a user has with the platform, what the UI displays, and exactly what happens in the backend architecture at every step.

---

## Phase 1: Acquisition & Onboarding

### 1.1 Landing & Authentication
* **User Action:** Lands on `visoora.ai`, views the demo, and clicks "Start Free Trial".
* **UI State:** Redirected to `/signup`. User enters email and password, or clicks "Sign in with Google".
* **Backend Architecture:** 
  * Uses **Supabase SSR (Server-Side Rendering) Auth**.
  * Validates credentials securely.
  * If Google OAuth, handles callback and provisions a new `tenant_id` in the database to ensure strict data isolation.
  * Issues an HTTP-only JWT secure cookie.

### 1.2 The "Business Brain" Setup
* **User Action:** User is redirected to `/onboarding`. They are asked for their Company Name and Website URL.
* **UI State:** A progress spinner appears saying "Analyzing your business..."
* **Backend Architecture:**
  * The backend triggers a **Firecrawl / Scraper API**.
  * It scrapes the user's website, extracting their core Value Proposition, Pricing, and Target Market.
  * Passes the scraped text to an LLM (Claude 3.5) to synthesize into a structured JSON profile.
* **User Action:** User reviews the AI-generated Value Proposition. They can edit the text, add common sales objections (e.g., "We are too expensive"), and select a "Tone of Voice" (e.g., Consultative, Aggressive, Casual).
* **Backend Architecture:** Saves this foundational context to the `business_brains` PostgreSQL table. This acts as the "Memory" for all future AI agents.

---

## Phase 2: The Command Center & Launch

### 2.1 The Dashboard (`/dashboard`)
* **User Action:** User lands on the main dashboard.
* **UI State:** Displays Live Pipeline Value, Active Missions, Leads Researched, and a Funnel metrics chart.
* **Backend Architecture:** 
  * Calls `/api/analytics/dashboard`.
  * Fetches aggregated data from Redis Cache (for speed) or queries Supabase directly.

### 2.2 Creating a Custom Mission (`/campaigns/new`)
* **User Action:** User clicks the glowing "Create Mission" button.
* **UI State:** A 3-step Framer Motion animated form appears.
  1. **Objective:** User selects "Cold Outbound" or "Inbound Follow-up".
  2. **Audience (ICP):** User types: *"SaaS Founders in Healthcare with 50-200 employees."*
  3. **Launch:** User clicks "Deploy Mission".
* **Backend Architecture:** 
  * Calls `POST /api/analytics/missions/launch`.
  * Enqueues a heavy background job into the **Redis Task Queue**. The UI immediately transitions to "Running" so the user isn't stuck waiting for HTTP timeouts.

---

## Phase 3: The Autonomous Agent Swarm (Invisible Backend)

While the user watches the "Mission Replay" UI on the frontend, the backend orchestrates a complex Directed Acyclic Graph (DAG) of AI agents.

### 3.1 Planning Agent
* **Function:** Reads the user's audience description. Decides exactly which data sources to query (LinkedIn, Apollo, Crunchbase).

### 3.2 Prospecting Agent
* **Function:** Connects to third-party APIs (like Apollo.io or ZoomInfo) to pull a list of 100 raw leads matching "Healthcare SaaS Founders".

### 3.3 Research Agent (The Deep Dive)
* **Function:** For each lead, it runs concurrent web searches (via Perplexity/Tavily API).
* **Action:** It reads the founder's recent LinkedIn posts, company news (e.g., "Recently raised Series B"), and 10K SEC filings.

### 3.4 Lead Scoring Engine
* **Function:** Cross-references the scraped lead data against the user's "Business Brain".
* **Action:** Assigns a score from 0 to 100. If a lead scores below 60, the AI silently rejects them and drops them from the pipeline to protect the user's domain reputation.

### 3.5 Email Generator Agent
* **Function:** Takes the highly-qualified lead, the deep research, and the Business Brain's tone of voice.
* **Action:** Prompts an LLM (Claude 3.5 Sonnet) to write a hyper-personalized email. (e.g., *"Saw you just raised a Series B to expand your healthcare app. Our dev agency helps scale HIPAA-compliant architectures..."*).
* **Output:** Saves the draft to the database with status `WAITING_APPROVAL`.

---

## Phase 4: The Approval Cockpit (Human-in-the-Loop)

### 4.1 Reviewing Drafts (`/cockpit`)
* **User Action:** User sees a yellow notification banner: *"Drafts await your approval"*. They click it.
* **UI State:** The screen splits in two. 
  * **Left side:** The drafted email text.
  * **Right side:** The **Evidence Log**. This explains exactly *why* the AI wrote what it did (e.g., "I included a sentence about SOC2 compliance because I found an article saying they are expanding to enterprise").
* **User Action:** User can manually edit the text, or click "Approve".

### 4.2 The Feedback Loop (Self-Learning)
* **Backend Architecture:** 
  * If the user edits the email, the system calculates a text diff.
  * It sends this correction to a **Vector Database (RAG - Retrieval-Augmented Generation)**.
  * *Result:* The next time the AI drafts an email for a similar prospect, it pulls from this memory to mimic the user's exact writing style. The system gets smarter every day.

---

## Phase 5: Dispatch & Follow-up Engine

### 5.1 Sending the Email
* **Backend Architecture:** Once approved, the status changes to `QUEUED`. A cron job picks it up and connects to the user's email provider (Gmail/Outlook via Nylas or SMTP).
* **Action:** Sends the email at an optimized time (e.g., Tuesday at 9:00 AM local time for the prospect).

### 5.2 The Reaction Webhooks
* **Backend Architecture:** System listens for webhooks (Opens, Clicks, Replies).
* **If Prospect Replies Positively:** The AI halts any future automated follow-ups. It sends an immediate push notification/email to the human SDR: *"Hot Lead! John Doe replied. Take over manually."*
* **If Prospect Ignores:** After 3 days, the **Follow-up Agent** wakes up. It reads the first email, checks if any *new* news happened for that company in the last 3 days, and writes a contextual, non-annoying bump email.

---

## Summary of the Technical Stack
- **Frontend:** Next.js (React), Tailwind CSS, Framer Motion (for premium UI animations).
- **Backend:** Python (FastAPI) for high-performance concurrent agent processing.
- **Database:** Supabase (PostgreSQL) for relational data, Redis for task queueing and caching.
- **AI Models:** Claude 3.5 Sonnet (for complex reasoning and writing), OpenAI embeddings (for the Memory Vector DB).
