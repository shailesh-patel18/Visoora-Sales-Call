# Visoora: Granular End-to-End System Architecture

This document breaks down every single micro-interaction a user has with the platform, focusing on the AI Revenue Operating System model, transparent AI, and deep enterprise infrastructure.

---

## Phase 1: Acquisition & The Living Business Brain

### 1.1 Authentication & CRM Integration
* **User Action:** Lands on `visoora.ai`, signs up, and connects their CRM.
* **UI State:** Standard OAuth flows for Supabase Auth, followed by mandatory "Connect Salesforce / HubSpot" integration cards.
* **Backend Architecture:** 
  * Provisions `tenant_id` in Supabase for strict data isolation.
  * Initiates background job to securely pull historical CRM data (Won Opportunities, Existing Accounts, Contacts) to prevent the AI from prospecting active clients.

### 1.2 The Persistent Business Brain Setup
* **User Action:** Enters their Company URL and reviews AI-generated positioning.
* **UI State:** A rich, editable dashboard showing extracted Value Propositions, ICPs, and Tone of Voice.
* **Backend Architecture:**
  * **Scraper API:** Scrapes the provided website.
  * **Synthesis (LLM):** Structures the data into a JSON profile.
  * **Persistent Memory:** Saves to the `business_brains` PostgreSQL table and a Vector DB. This is a *living* document that will automatically update as the system learns from CRM wins and user email edits.

---

## Phase 2: Command Center & Revenue Operations

### 2.1 The ROI Dashboard (`/dashboard`)
* **User Action:** Lands on the central hub.
* **UI State:** Displays Revenue Operations metrics: Live Pipeline Value, Meetings Booked, Domain Health Scores, and Deliverability Status.
* **Backend Architecture:** Aggregates real-time data from Redis Cache and the CRM integration webhooks.

### 2.2 Launching an Explainable Mission (`/missions/new`)
* **User Action:** Creates a new outbound or inbound mission.
* **UI State:** Defines target audience and objective. Clicks "Launch."
* **Backend Architecture:** Enqueues a task in the **Redis Task Queue**. API gateway returns a 202 Accepted, allowing the UI to immediately transition to the "Mission Replay" view.

---

## Phase 3: Transparent AI Agent Swarm & Infrastructure

This is the orchestration layer where the AI acts, but with full transparency back to the user.

### 3.1 Planning & CRM Memory Agent
* **Function:** Cross-references the requested target audience with the CRM to ensure we don't contact existing customers or active opportunities. Decides which external databases to query (Apollo, ZoomInfo).

### 3.2 Prospecting & Research Agent
* **Function:** Pulls raw leads and performs deep web research (LinkedIn, news, SEC filings via Perplexity/Tavily).
* **Action:** Compiles structured "Evidence" for why a lead is a good fit.

### 3.3 The Deliverability & Compliance Check
* **Function:** Before any draft is made, the lead is run through the **Compliance Layer**.
* **Action:** Checks suppression lists, GDPR consent requirements, and CAN-SPAM opt-outs. It also queries the **Deliverability Center** to ensure the sending domains are warm and healthy enough to accept new volume.

### 3.4 Email Generator (Drafting & Confidence Scoring)
* **Function:** Writes the highly-personalized email based on the research.
* **Action:** The LLM generates the email AND an "Evidence Log" detailing exactly which data points influenced each sentence. It also assigns a "Confidence Score".
* **Output:** Saves draft to DB with status `WAITING_APPROVAL`.

---

## Phase 4: Human Governance (The Trust Layer)

### 4.1 The Approval Cockpit & Mission Replay (`/cockpit`)
* **User Action:** Receives notification of pending drafts. Enters the Cockpit.
* **UI State:** Split-screen view.
  * **Left side:** The drafted email text.
  * **Right side (Mission Replay):** Step-by-step reasoning, Confidence Score (e.g., "92% match"), and the Evidence Log (e.g., "Mentioned Q2 earnings based on [this article]").
* **User Action:** Approves, rejects, or manually edits the text.

### 4.2 The Data Flywheel (Self-Learning)
* **Backend Architecture:** 
  * Any manual edits are captured, diffed, and sent to the **Vector Database (RAG)**.
  * *Result:* The Business Brain learns the user's specific stylistic preferences and objection handling, ensuring the system never makes the same mistake twice.

---

## Phase 5: Enterprise Deliverability & Dispatch

### 5.1 The Deliverability Center (Sending)
* **Backend Architecture:** 
  * Jobs picked up with status `QUEUED`.
  * **Domain Rotation Engine:** Intelligently rotates the outbound email across multiple secondary sending domains to protect the primary domain's reputation.
  * **Throttling:** Ensures sending limits (e.g., max 40 emails/day per inbox) are strictly respected.
  * Dispatches via Nylas or SMTP.

### 5.2 CRM Sync & Follow-up Engine
* **Backend Architecture:** System listens for webhooks (Opens, Clicks, Replies, Bounces).
* **Bounce Monitoring:** Immediately pauses campaigns on a domain if bounce rates exceed safety thresholds.
* **Bi-directional Sync:** Logs all activities (emails sent, replies received) directly into the connected CRM (Salesforce/HubSpot).
* **Smart Follow-up:** If ignored, the Follow-up Agent generates contextual bumps based on any *new* information acquired since the first email.
