# Requirements Document

## Introduction

Visoora is an AI-powered outbound sales platform that acts as a virtual sales employee for small and medium-sized businesses. The platform learns a customer's business through a conversational onboarding wizard (the "Business Brain"), then autonomously researches uploaded prospects, scores their fit, generates personalized outreach email drafts, facilitates AI-assisted voice calls, and provides a unified sales workspace with a lightweight CRM.

A real codebase exists with a working voice pipeline (FSM/VAD/STT/TTS), TCPA/DNC compliance gate, billing/Stripe integration, CRM models, and an email engine. However, the system has critical production blockers: authentication is partially client-side only, the dashboard renders mocked data, multi-tenant isolation has gaps, CSV imports previously silently discarded rows on database failure (now fixed in local fallback mode), calls and campaigns were hardcoded to fake data, and the LLM integrations reference invalid or quota-exhausted model endpoints.

This requirements document covers the full Visoora MVP: stabilization of existing critical bugs, completion of core AI feature modules (Business Brain, Lead Scoring, Company Research, AI Email Generation, AI Sales Workspace), and the production-hardening needed before commercial launch.

**Non-negotiable constraints that apply to every requirement in this document:**
- No LinkedIn scraping or LinkedIn API automation at any phase
- No algorithmic email address guessing or synthesis
- No autonomous prospect discovery — CSV/XLSX upload is the only prospect intake mechanism in MVP
- No vector database until measurable trigger conditions are met (~500+ documents per account, semantic search need, or measured retrieval degradation)
- All AI work (scoring, research, email generation) runs asynchronously via background job queue — never synchronously inside HTTP request handlers
- Every async job must reach a visible terminal state: `success`, `failed_with_reason`, or `retrying` — no silent failures
- Every AI output ships with human-readable justification; confirmed facts vs. estimated facts must be visually distinct in the UI
- All customer data tables carry `tenant_id` with Postgres RLS enforcement
- Per-account LLM token budget caps and rate limiting are enforced before any AI feature reaches production

---

## Product Philosophy and Mindset Shift

The questions running through their minds are usually:
- Can I trust this with my business?
- Will it actually understand my company?
- Will it save me time?
- Will it generate better leads than my team?
- Will it help me close more deals?
- Is my data safe?
- Can I control what the AI does?
- Can I measure the ROI?
- If something goes wrong, can I fix it?
- Why should I pay instead of using existing tools?

Your product needs to answer these questions before the customer asks them.

### Why People Pay

People don't pay for AI.
They pay because they believe:
"This will make me more money than it costs."

If your product costs $199/month but helps generate one extra $5,000 client, the decision is easy.

Your marketing should shift from:
- ❌ "AI-powered prospecting."
to
- ✅ "Find qualified buyers in minutes instead of spending 20 hours every week researching companies."

That's the value they understand.

### Can They Trust It?

Trust isn't created by saying "Trust us."
It's created through transparency and control.

For example, instead of saying:
"We found 200 leads."

Show:
- Why each company was selected.
- Which ICP criteria it matched.
- Which buying signals were detected.
- Confidence score.
- Sources used.
- Why it was rejected or accepted.

When users can inspect the AI's reasoning, trust increases dramatically.

### Should You Guarantee Business Growth?

This is where many AI startups make a mistake.
You cannot honestly guarantee:
- Revenue growth.
- More customers.
- More closed deals.

Those outcomes depend on many factors outside your control, including the user's product, pricing, sales skills, competition, and market conditions.

Instead, you can confidently guarantee improvements in the parts your software controls.

For example:
- Faster prospect research.
- Better-qualified lead lists.
- Personalized outreach drafts.
- Time saved.
- Better organization.
- Higher consistency.

Those are measurable and under your influence.

### What Users Actually Want

When someone buys software like yours, they're thinking:
"I don't want another dashboard."

They want:
"Give me my next customer."

That's a very different product philosophy.

### The "Wow" Moment

Most AI onboarding looks like this:
Question 1 -> Next -> Question 2 -> Next -> Question 3 -> Next. It's boring.

Instead, imagine this experience:
- **AI:** Hi Shailesh! I analyzed your website while you were signing up. I believe you're a software agency focused on startups and SMBs. Is that correct?
- **User:** Yes.
- **AI:** Great. I also noticed you've built healthcare and fintech projects, but your homepage emphasizes custom software more than those niches. Is healthcare one of your target industries or just part of your portfolio?
- **User:** We want more healthcare clients.
- **AI:** Excellent choice. Healthcare companies generally have longer sales cycles but higher contract values. Based on similar agencies, I'd recommend targeting:
  - HealthTech startups (50–200 employees)
  - Multi-location clinics
  - Healthcare SaaS companies

  Would you like me to build your prospecting strategy around those segments?

Now the user feels like they're talking to an experienced consultant, not filling out a form.

### The Experience You Should Aim For

Your AI should behave like a blend of:
- A top-tier sales consultant.
- A market researcher.
- A B2B growth strategist.
- A CRM expert.
- A founder advisor.

It shouldn't just ask questions. It should:
- Make educated assumptions.
- Explain its reasoning.
- Ask only for missing information.
- Offer recommendations.
- Challenge weak assumptions politely.
- Teach the user something about their market.

When the AI says something like:
"I found three underserved industries where agencies like yours close deals 27% faster. Would you like to see them?"
the user thinks:
"This AI is helping me make better business decisions."

That's the kind of experience people are willing to pay for.

### The Biggest Mindset Shift for Visoora

Don't think of Visoora as "an AI that finds leads."

Think of it as:
An AI Growth Strategist that understands a business deeply, designs the best go-to-market strategy, continuously finds the highest-probability buyers, and explains every recommendation with evidence.

---


## Glossary

- **Visoora**: The AI outbound sales platform described in this document.
- **Platform**: Visoora's full software system including frontend, backend, database, and AI services.
- **Tenant**: A single paying customer account (company) using Visoora. All data is partitioned by `tenant_id`.
- **User**: An authenticated human operator belonging to a Tenant (role: `admin`, `agent`, or `viewer`).
- **Business_Brain**: The structured knowledge store derived from onboarding, capturing company description, value proposition, ICP definition, buyer personas, objections, and competitive intelligence for a Tenant.
- **ICP**: Ideal Customer Profile — the set of industry, company size, region, and decision-maker title attributes that define the best-fit prospect type for a Tenant.
- **Prospect**: A contact record imported via CSV/XLSX, representing a potential customer to be researched, scored, and contacted.
- **Lead_Score**: An integer from 0 to 100 representing how well a Prospect matches the Tenant's ICP and Business Brain, produced by the Lead_Scorer.
- **Lead_Scorer**: The background job that applies rule-based pre-filtering plus a Claude LLM qualitative pass to produce a Lead_Score for each Prospect.
- **Company_Researcher**: The background job that fetches publicly available information about a Prospect's employer domain (respecting robots.txt) and uses Claude to extract confirmed facts and estimates.
- **Email_Generator**: The background job that produces a personalized outreach email draft for a Prospect, grounded in Business Brain context and Company Research output.
- **AI_Workspace**: The conversational chat interface where a User can ask questions about a Prospect or request sales coaching, backed by Business Brain context and Company Research data.
- **Job_Queue**: The persistent asynchronous job execution system (currently a polling loop backed by the `background_jobs` Postgres table; future: BullMQ on Redis).
- **Background_Job**: A unit of asynchronous work with a type, payload, `tenant_id`, and a terminal status of `queued`, `running`, `success`, `failed`, or `retrying`.
- **Mission_Control**: The real-time dashboard view showing live call metrics, pipeline funnel, campaign health, and background job status.
- **CRM**: The lightweight contact, deal, pipeline stage, and activity management system embedded in Visoora.
- **DNC**: Do Not Call registry — a per-tenant list of phone numbers that must not be dialed.
- **TCPA**: Telephone Consumer Protection Act — US federal law governing outbound calling and consent requirements.
- **Compliance_Gate**: The pre-call verification pipeline that checks DNC membership, TCPA calling-hours windows, and consent token validity before any outbound call is placed.
- **LLM**: Large Language Model — specifically the Anthropic Claude API (primary) used for scoring, research, email generation, and workspace responses.
- **RLS**: Row-Level Security — Postgres/Supabase policy mechanism that restricts table row access to the owning Tenant.
- **Token_Budget**: A per-tenant cap on total LLM tokens consumed per rolling billing period, enforced before dispatching any LLM API call.
- **Supabase**: The managed Postgres + auth + storage service used as the primary database and file store.
- **Auth_Service**: The Supabase Auth integration providing JWT issuance, verification, password reset, and session management.
- **FSM**: Finite State Machine — the voice call state controller managing transitions between call phases (greeting, qualification, objection handling, booking, close).
- **VAD**: Voice Activity Detection — the audio energy threshold monitor that detects prospect speech and interruption events.
- **STT**: Speech-to-Text — the Deepgram Nova-2 transcription service that converts prospect audio to text.
- **TTS**: Text-to-Speech — the ElevenLabs voice synthesis service (with PCM fallback) that vocalizes agent responses.
- **Onboarding_Wizard**: The multi-step frontend wizard (steps 1–11) that collects business information and populates the Business Brain.
- **Persona**: The serialized agent configuration blob stored in `agent_configs.persona`, containing tone, FAQs, objections, calling hours, product details, and ICP parameters.
- **Sourced_Fact**: A piece of company research information directly grounded in scraped or provided data (e.g., website copy, domain name), displayed with a source URL.
- **AI_Estimate**: A piece of company research information inferred or projected by the LLM without direct source grounding, displayed with a confidence label.
- **Unsubscribe_Token**: A unique, single-use token embedded in outbound emails that allows a Prospect to opt out of further email outreach.
- **Sentry**: The error monitoring and alerting service integrated for production exception tracking.
- **Redis**: The in-memory data store used for caching analytics responses and (future) BullMQ job queue backing.
- **Stripe**: The payment processing platform integrated for subscription billing and usage metering.


---

## Requirements

---

### Requirement 1: Authentication — Real JWT-Based Login and Signup

**User Story:** As a User, I want to sign up and log in with real credentials, so that my account is securely isolated from other tenants and my session is cryptographically verified.

#### Acceptance Criteria

1. WHEN a visitor submits a valid email address and password to the signup endpoint, THE Auth_Service SHALL create a new Supabase Auth user, issue a JWT access token, and return `{ "success": true, "access_token": "<token>", "user": { "id", "email", "role", "tenant_id" } }` within 3 seconds.
2. WHEN a visitor submits an email address that does not contain an `@` character to the signup endpoint, THE Auth_Service SHALL return HTTP 422 with a descriptive validation error and SHALL NOT create any user record.
3. WHEN a visitor submits a valid email and password to the login endpoint, THE Auth_Service SHALL verify the credentials against Supabase Auth, issue a JWT, and return the same response shape as signup within 3 seconds.
4. WHEN a visitor submits an incorrect password to the login endpoint, THE Auth_Service SHALL return HTTP 401 with the message `"Invalid email or password."` and SHALL NOT issue a token.
5. THE Auth_Service SHALL enforce a minimum password length of 8 characters; WHEN a password shorter than 8 characters is submitted, THE Auth_Service SHALL return HTTP 422.
6. WHEN a frontend page that requires authentication receives an HTTP request without a valid `Authorization: Bearer <JWT>` header or without a valid `visoora_session_token` cookie, THE Platform SHALL redirect the User to `/login`.
7. THE Platform SHALL NOT grant access to any protected route when `visoora_logged_in=true` is set as a cookie but no valid JWT token is present — the middleware MUST verify the JWT, not the cookie value alone.
8. WHEN a logged-in User's JWT expires, THE Platform SHALL automatically attempt a silent token refresh using the Supabase refresh token; IF the refresh fails, THE Platform SHALL redirect the User to `/login` and clear all session cookies.
9. WHEN a User submits a password-reset request for a registered email, THE Auth_Service SHALL send a password-reset email via Supabase Auth within 30 seconds.
10. IF a User submits a password-reset request for an email address that does not exist in Supabase Auth, THEN THE Auth_Service SHALL return HTTP 200 with the message `"If this email is registered, a reset link has been sent."` — the response SHALL NOT reveal whether the email exists.
11. WHEN a User logs out, THE Platform SHALL invalidate the session token server-side, clear the `visoora_session_token` and `visoora_logged_in` cookies, and redirect the User to `/login`.
12. THE Auth_Service SHALL NOT bypass authentication for any request originating from a public ngrok domain or any non-localhost host, regardless of the `APP_ENV` setting.
13. THE local development fallback principal (role: `admin`, tenant: `default_shared_tenant`) SHALL only be granted WHEN `APP_ENV=development` AND the request Host is `localhost` or `127.0.0.1`.

---

### Requirement 2: Multi-Tenant Data Isolation

**User Story:** As a Tenant, I want all my data to be strictly isolated from other tenants, so that I can trust that my prospects, calls, and AI outputs are never visible to or mixed with another customer's data.

#### Acceptance Criteria

1. THE Platform SHALL enforce Postgres Row-Level Security policies on all data tables (`contacts`, `companies`, `deals`, `pipeline_stages`, `activities`, `call_logs`, `call_consents`, `dnc_numbers`, `agent_configs`, `background_jobs`, `icp_segments`, `buyer_personas`, `lead_feedback`, `email_sends`) so that each row is accessible only to the tenant whose `tenant_id` matches the JWT claim.
2. WHEN a background job writes any record to any database table, THE Job_Queue SHALL include the resolved `tenant_id` UUID (not a default placeholder) in every insert payload.
3. IF `upload_recording` is called with a `tenant_id` value in `{ "default_tenant", "default_shared_tenant", "" }` while Supabase is configured, THEN THE Platform SHALL route the recording to a `recordings-uncategorized` quarantine bucket and emit a `CRITICAL` log entry identifying the stream SID — THE Platform SHALL NOT mix this recording with real tenant buckets.
4. THE Platform SHALL verify that every API endpoint that accepts a resource identifier (contact ID, deal ID, job ID, etc.) performs a `tenant_id` equality check before returning or mutating the resource; IF the resource belongs to a different tenant, THE Platform SHALL return HTTP 404.
5. WHEN a CSV import job writes contacts to Supabase, THE Job_Queue SHALL include the authenticated User's resolved `tenant_id` UUID in every `contacts` row insert — THE Platform SHALL NOT use a string literal like `"default_shared_tenant"` as the `tenant_id` for production inserts.
6. THE Platform SHALL apply the same tenant isolation rules to local JSON file fallback storage, filtering all read operations by `tenant_id` before returning results.

---

### Requirement 3: Dashboard — Real Data Connectivity

**User Story:** As a User, I want the dashboard to display my actual call metrics, pipeline funnel, and job statuses, so that I can make real sales decisions based on accurate information.

#### Acceptance Criteria

1. WHEN a User navigates to `/dashboard`, THE Platform SHALL fetch live metrics from `GET /api/analytics/dashboard` using the authenticated User's JWT, and SHALL render the returned `total_calls`, `success_rate_percent`, `total_duration_seconds`, `trend_data`, and `success_calls` values — THE Platform SHALL NOT display hardcoded or randomly generated numbers.
2. WHEN a User navigates to `/calls`, THE Platform SHALL fetch paginated call history from `GET /api/analytics/calls` and render the returned records — THE Platform SHALL NOT populate the call list with static mock arrays.
3. WHEN a User navigates to `/calls/[id]`, THE Platform SHALL fetch the specific call record from `GET /api/analytics/calls/{call_id}` and render the real transcript, duration, final state, and recording playback URL — THE Platform SHALL NOT display the "Sarah Connor" hardcoded mock data.
4. WHEN a User navigates to `/pipeline`, THE Platform SHALL fetch the deal funnel distribution from `GET /api/analytics/funnel` and render real stage counts and values.
5. WHEN the Supabase database is unreachable in a `development` or `test` environment, THE Platform SHALL fall back to computing metrics from `recordings/local_call_logs.json` and SHALL display a `source: "local_fallback"` indicator in the UI.
6. IF the Supabase database is unreachable in a `production` environment, THEN THE Platform SHALL display an error state component (not a 500 page crash) and SHALL log the failure to Sentry.
7. THE analytics API router SHALL be registered on the main FastAPI application instance so that all `/api/analytics/*` endpoints return valid responses (not HTTP 404).
8. WHEN dashboard metrics are successfully fetched from Supabase, THE Platform SHALL cache the result in Redis with a TTL of 300 seconds; subsequent requests within that window SHALL be served from cache without querying the database.

---

### Requirement 4: Prospect Import — CSV/XLSX Upload

**User Story:** As a User, I want to upload a CSV or XLSX file of prospects, so that the platform can import and enrich them for AI-driven outreach without me having to enter contacts manually.

#### Acceptance Criteria

1. WHEN a User submits a CSV or XLSX file to `POST /api/contacts/import`, THE Platform SHALL parse the file, validate each row, persist valid contacts to the database (or local JSON fallback when offline), and return a `job_id` within 2 seconds — THE Platform SHALL NOT process the file synchronously in the HTTP handler.
2. THE Platform SHALL accept CSV files with any of the following column name spellings (case-insensitive): `phone`, `phone_number`, `phone_e164` for the phone field; `name`, `full_name` for the name field; `email` for email; `title`, `job_title` for title; `company`, `company_name` for company.
3. WHEN a CSV row is missing a phone number value, THE Platform SHALL classify that row as `skipped` with reason `"Missing phone number"` and SHALL continue processing remaining rows — THE Platform SHALL NOT abort the entire import.
4. WHEN a CSV row contains a phone number that already exists for the same tenant, THE Platform SHALL classify that row as `skipped` with reason `"Duplicate prospect"` and SHALL NOT create a second record.
5. WHEN the Supabase client is unavailable during import, THE Platform SHALL persist all valid contacts to `recordings/local_contacts_{tenant_id}.json` with the resolved `tenant_id` UUID — THE Platform SHALL NOT silently discard contacts.
6. WHEN the import job completes, THE Platform SHALL emit a Server-Sent Event on `GET /api/contacts/import/{job_id}` with `{ "progress": 100, "status": "...", "completed": true, "summary": { "imported", "skipped", "errored" }, "details": [...] }`.
7. WHEN import SSE progress events are streamed, each event's `details` array SHALL contain a row-level outcome object `{ "row", "name", "phone", "outcome": "imported"|"skipped"|"errored", "reason" }` for every processed row.
8. WHEN a database write fails for a single row (non-network error), THE Platform SHALL classify that row as `errored` with the error message as the reason and SHALL continue processing remaining rows.
9. WHEN a network or connection-level database error occurs during import, THE Platform SHALL abort the database path and fall back to local JSON persistence for all remaining rows.
10. AFTER a successful import (one or more contacts written), THE Job_Queue SHALL automatically enqueue a `lead_scoring` job for all newly created contact IDs.
11. THE Platform SHALL enforce a maximum of 10,000 rows per single import file; WHEN a file exceeds this limit, THE Platform SHALL return HTTP 422 with the message `"Import file exceeds the 10,000 row limit."`.
12. THE Platform SHALL scan CSV column headers before processing and SHALL surface a validation error to the User for any file that contains no recognizable phone column — THE Platform SHALL NOT silently import a file with zero phone data.

---

### Requirement 5: Business Brain — Conversational Onboarding and Knowledge Store

**User Story:** As a business owner, I want to teach the AI about my company through a guided wizard, so that every AI action (scoring, research, email, voice calls) is grounded in accurate knowledge about my business and my ideal customers.

#### Acceptance Criteria

1. WHEN a User completes the Onboarding_Wizard and submits `POST /api/onboarding/complete`, THE Platform SHALL persist all structured business knowledge to the `agent_configs` table under the authenticated Tenant's `tenant_id` within 5 seconds.
2. THE Business_Brain knowledge store SHALL capture and persist: company name, website, industry, team size, estimated annual revenue, target region, company description, value proposition, product name, product price, product features, target audience, knowledge base FAQs, objections and rebuttals, ICP industries, ICP company sizes, ICP regions, decision-maker titles, avoid list (companies/domains to skip), competitor names, brand voice/tone, agent name, calling hours start/end, and timezone.
3. WHEN any AI job (Lead_Scorer, Company_Researcher, Email_Generator) executes for a Tenant, THE Platform SHALL load that Tenant's Business_Brain from `agent_configs` before constructing any LLM prompt — no AI job SHALL use hardcoded or placeholder business knowledge.
4. WHEN a User updates any Business_Brain field through the Settings page, THE Platform SHALL persist the change to `agent_configs` within 3 seconds and SHALL use the updated values for all subsequent AI jobs.
5. THE Onboarding_Wizard SHALL validate that the `website` field contains a string beginning with `http://` or `https://` or a bare domain that can be prepended with `https://`; IF the website domain cannot be reached via HTTP HEAD within 3 seconds, THE Platform SHALL display a warning but SHALL allow the User to proceed.
6. IF a User has not yet completed the Onboarding_Wizard, THEN THE Platform SHALL redirect the User to the Onboarding_Wizard when the User attempts to access the AI Scoring, Research, Email, or Workspace features.
7. THE Business_Brain SHALL store ICP segments and buyer personas in dedicated `icp_segments` and `buyer_personas` tables (one-to-many per tenant), not flattened into the `agent_configs.persona` JSON blob, to allow independent updates without replacing the full persona object.
8. WHEN the Business_Brain is successfully saved for the first time for a Tenant, THE Platform SHALL enqueue a `business_brain_analysis` background job that generates an initial ICP scoring rubric from the structured inputs using the LLM.
9. WHERE a Tenant has not defined any ICP industries, THE Lead_Scorer SHALL use the full base score (no industry deduction) rather than marking all contacts as non-matching.

---

### Requirement 6: Lead Scoring — Hybrid Rule-Based + LLM Scoring

**User Story:** As a sales manager, I want every imported prospect automatically scored for ICP fit, so that my team can prioritize the highest-value leads without manually reviewing hundreds of rows.

#### Acceptance Criteria

1. WHEN a `lead_scoring` job is dequeued, THE Lead_Scorer SHALL load the Tenant's Business_Brain, fetch the specified contact records from the database (or local fallback), compute a Lead_Score for each contact, and persist the scores — all without blocking any HTTP request handler.
2. THE Lead_Scorer SHALL apply rule-based pre-filtering first: IF a contact's email domain or company name matches any entry in the Tenant's `avoid_list`, THEN THE Lead_Scorer SHALL assign a score of 0, tag the contact with `"objection-avoid-list"`, and store the reason `"Matched avoid-list pattern: '<pattern>'"` — THE Lead_Scorer SHALL NOT call the LLM for disqualified contacts.
3. THE Lead_Scorer SHALL compute a heuristic base score starting at 20 and applying the following additive bonuses before the LLM pass: +25 for a decision-maker title match, +15 for an ICP industry match, +10 for an ICP region match — the total heuristic score before LLM adjustment SHALL be capped at 100.
4. WHEN the Anthropic Claude API key is valid and the Token_Budget for the Tenant has not been exhausted, THE Lead_Scorer SHALL call Claude to produce a score adjustment in the range [-30, +30] and a 1–2 sentence reasoning string.
5. WHEN the Claude API call succeeds, THE Lead_Scorer SHALL produce the final score as `max(0, min(100, heuristic_score + llm_adjustment))` and SHALL store: the final score, the full explanation string (heuristic reasons + LLM rationale), and updated tags on the contact record.
6. IF the Claude API call fails or times out (>6 seconds), THEN THE Lead_Scorer SHALL complete scoring using the heuristic score only and SHALL append `"AI evaluation bypassed: <reason>"` to the explanation — THE Lead_Scorer SHALL NOT fail the job due to an LLM timeout.
7. THE Lead_Scorer SHALL tag contacts with `"hot-lead"` when the final score is ≥ 80, and with `"cold-lead"` when the final score is < 40 — existing tags SHALL be preserved and new tags SHALL be appended without duplication.
8. WHEN a `lead_scoring` job completes (success or failure), THE Job_Queue SHALL update the job's terminal status with a result payload containing per-contact outcomes `[{ "contact_id", "score", "status": "success"|"failed", "error"? }]`.
9. THE Lead_Scorer explanation stored on the contact SHALL be displayed in the UI adjacent to the Lead_Score, visually distinguishing heuristic reasons from the AI rationale.
10. WHEN a User opens a contact's detail view and a lead score exists, THE Platform SHALL display the Lead_Score as a numeric value (0–100) alongside the full explanation text — THE Platform SHALL NOT display the score without the explanation.
11. WHERE a Tenant has consumed 90% of their Token_Budget in the current billing period, THE Platform SHALL send a notification to the Tenant's admin email and SHALL display a usage warning banner in the UI.
12. WHEN the Tenant's Token_Budget is fully exhausted, THE Lead_Scorer SHALL complete heuristic scoring only and SHALL NOT call the LLM — THE Platform SHALL display a clear "AI scoring paused — token budget exhausted" message in the UI.

---

### Requirement 7: Company Research — Public Web Research with Source Attribution

**User Story:** As a salesperson, I want the AI to automatically research each prospect's company from public sources, so that I can send more personalized outreach without spending hours on manual research.

#### Acceptance Criteria

1. WHEN a `company_research` job is dequeued for a contact, THE Company_Researcher SHALL check `robots.txt` of the contact's company domain within 3 seconds; IF the domain disallows crawling, THE Company_Researcher SHALL record this fact and SHALL NOT attempt to fetch any page from that domain.
2. WHEN robots.txt permits or does not exist (HTTP 404), THE Company_Researcher SHALL perform a single HTTP GET to the company's root domain (not subpages), with a 4-second timeout, and extract the first 2,000 characters of response text for LLM analysis.
3. THE Company_Researcher SHALL NOT attempt to scrape LinkedIn, Crunchbase, Hunter.io, Apollo, or any paid enrichment service — these are prohibited data sources.
4. WHEN the Claude API key is valid, THE Company_Researcher SHALL prompt Claude to separate the research output into two distinct lists: `sourced_facts` (each with `fact`, `source`, and `url`) and `estimates` (each with `estimate` and `confidence: "High"|"Medium"|"Low"`).
5. THE Company_Researcher SHALL NOT fabricate specific figures (e.g., "$23.4M revenue", named client references) as `sourced_facts` — the LLM prompt SHALL explicitly instruct Claude to anchor facts only to information present in the scraped text snippet.
6. WHEN the Company_Researcher produces a research report, THE Platform SHALL store the `{ sourced_facts, estimates, metadata_facts }` object in the contact's `custom_fields.research_data` field in the database (or local fallback).
7. WHEN a User views a contact that has research data, THE Platform SHALL render `sourced_facts` with a visible source tag (e.g., a link icon + domain label) and SHALL render `estimates` with a confidence badge (`High` / `Medium` / `Low`) — the two categories SHALL be visually distinct.
8. IF the Claude API call fails or times out, THEN THE Company_Researcher SHALL store a partial research report containing CRM-sourced facts only (`company name`, `email domain`) with all estimates marked as `"confidence": "Low"` and an explanation of the failure — THE Company_Researcher SHALL NOT fail the job silently.
9. WHEN a contact has no valid company domain (no email with custom domain, no website field), THE Company_Researcher SHALL record `"No valid company domain available"` as a metadata fact and SHALL complete the job without an error status.
10. AFTER a `company_research` job completes successfully, THE Job_Queue SHALL automatically enqueue an `email_generation` job for the same contact.

---

### Requirement 8: AI Email Generation — Personalized, Human-in-the-Loop Outreach

**User Story:** As a salesperson, I want the AI to draft personalized outreach emails for each prospect grounded in their research and my business context, so that I can review and send high-quality emails in seconds instead of hours.

#### Acceptance Criteria

1. WHEN an `email_generation` job is dequeued for a contact, THE Email_Generator SHALL load the Tenant's Business_Brain, the contact's research data, and the contact's interaction history before constructing any LLM prompt.
2. THE Email_Generator SHALL produce a draft containing: a subject line, a personalized opening referencing a specific company detail from the research data, a concise value proposition paragraph aligned with the Tenant's `brand_voice_tone`, a clear call-to-action, the agent's name as the sign-off, and an unsubscribe link using the format `/api/v1/sales-employee/leads/unsubscribe?lead_id={contact_id}`.
3. THE Email_Generator SHALL vary email content based on outreach sequence position: first contact (no prior emails), first follow-up (one prior email), and subsequent follow-up (two or more prior emails) — each sequence position SHALL produce a structurally distinct message that avoids repeating content from previous emails.
4. WHEN a prior call exists in the contact's interaction history with status `"no-answer"` or `"voicemail"`, THE Email_Generator SHALL reference the attempted call in the opening line of the email.
5. THE Email_Generator SHALL NOT generate email content that makes specific unverified numerical claims (e.g., "increase revenue by 47%") unless that figure appears in the Tenant's Business_Brain `value_proposition` field.
6. WHEN the Email_Generator completes a draft, THE Platform SHALL store the draft with status `"pending_review"` — THE Platform SHALL NOT send any email without explicit User approval.
7. WHEN a User views the draft email in the AI Workspace or contacts page, THE Platform SHALL display the full subject line, body, and the source personalization hooks (the specific research facts used) alongside the draft.
8. WHEN a User clicks "Approve and Send" on a draft, THE Platform SHALL deliver the email via the configured email provider and SHALL update the draft status to `"sent"` and record the activity in the CRM.
9. WHEN a User clicks "Edit" on a draft, THE Platform SHALL present an editable form pre-filled with the draft content; WHEN the User saves edits, THE Platform SHALL update the draft body without regenerating from the LLM.
10. IF the Claude API call fails during email generation, THEN THE Email_Generator SHALL store a partial draft containing the subject line and a template body with unfilled personalization placeholders, mark the job status as `"failed_with_reason"`, and surface the failure reason to the User in the UI.
11. THE Email_Generator SHALL respect the Tenant's Token_Budget; WHEN the budget is exhausted, THE Email_Generator SHALL queue the job and display a `"paused: token budget exhausted"` status to the User.
12. WHERE a contact has an unsubscribe record in the database, THE Email_Generator SHALL skip email generation for that contact and mark the job status as `"skipped_unsubscribed"`.

---

### Requirement 9: AI Sales Workspace — Conversational Chat Interface

**User Story:** As a salesperson, I want to chat with an AI assistant that knows my business and each prospect's research, so that I can get quick answers, talking points, and sales coaching without leaving the platform.

#### Acceptance Criteria

1. WHEN a User opens the AI Workspace for a specific contact, THE AI_Workspace SHALL load the Tenant's Business_Brain and the contact's research data as context before the User sends the first message.
2. WHEN a User sends a message in the AI Workspace, THE AI_Workspace SHALL stream the Claude response token-by-token to the frontend within 500ms of the first token, using HTTP Server-Sent Events or WebSocket streaming.
3. THE AI_Workspace SHALL maintain conversation history for the duration of the session; each subsequent message SHALL include all prior turns as context in the LLM prompt (up to the last 20 turns or 4,000 tokens of history, whichever is smaller).
4. WHEN a User asks about a specific prospect (e.g., "What do I know about their company?"), THE AI_Workspace SHALL answer using the stored `sourced_facts` and `estimates` from the contact's research data and SHALL cite the source for any fact it references.
5. THE AI_Workspace SHALL NOT reveal internal system prompt content, LLM provider names, or API key information to the User — WHEN a User asks about the AI's underlying technology, THE AI_Workspace SHALL respond with a generic helpful statement.
6. IF the Claude API call fails, THEN THE AI_Workspace SHALL display an inline error message `"The AI assistant is temporarily unavailable. Please try again in a moment."` and SHALL NOT crash the workspace page.
7. THE AI_Workspace SHALL enforce the Tenant's Token_Budget; WHEN the budget is exhausted, THE AI_Workspace SHALL display a `"AI workspace paused — token budget exhausted. Please upgrade your plan."` message and SHALL NOT call the LLM.
8. WHEN a User requests a suggested email subject line or talking point in the AI Workspace, THE AI_Workspace SHALL generate the suggestion using the Tenant's `brand_voice_tone` from Business_Brain.

---

### Requirement 10: Background Job Queue — Async Execution with Visible Terminal States

**User Story:** As a developer and as a User, I want every AI background job to always reach a visible terminal state with a clear outcome, so that no work is ever silently lost or stuck.

#### Acceptance Criteria

1. THE Job_Queue SHALL persist all jobs in the `background_jobs` Postgres table (with local JSON fallback when Supabase is offline) with the fields: `id`, `tenant_id`, `job_type`, `status`, `payload`, `result`, `error`, `created_at`, `updated_at`.
2. EVERY job enqueued by the Job_Queue SHALL reach exactly one of these terminal statuses: `"success"`, `"failed"`, or `"retrying"` — a job SHALL NOT remain in `"running"` status permanently (maximum running duration: 5 minutes before being re-queued as `"retrying"`).
3. WHEN a job handler raises an unhandled exception, THE Job_Queue SHALL catch the exception, set the job status to `"failed"`, store the full exception message in the `error` field, and log the failure to Sentry.
4. THE Job_Queue SHALL support at least these job types: `"lead_scoring"`, `"company_research"`, `"email_generation"`, `"business_brain_analysis"`.
5. WHEN a User navigates to the Mission_Control dashboard, THE Platform SHALL display a background job status panel listing the most recent 20 jobs for the Tenant, showing `job_type`, `status`, `created_at`, and `error` (if failed).
6. THE Job_Queue worker loop SHALL poll for queued jobs at an interval of 1 second and SHALL use optimistic locking (claim via status transition from `"queued"` to `"running"` in a single UPDATE with `WHERE status = 'queued'`) to prevent double-processing by concurrent workers.
7. WHEN the Supabase client is unavailable, THE Job_Queue SHALL fall back to the local JSON file `local_background_jobs.json` for all job persistence operations, using a mutex lock to prevent concurrent file corruption.
8. THE Job_Queue SHALL enforce a per-tenant concurrency limit of 5 simultaneously running jobs; WHEN the limit is reached, newly enqueued jobs SHALL remain in `"queued"` status until a running slot opens.
9. WHEN a `lead_scoring` job completes successfully, THE Job_Queue SHALL automatically enqueue a `company_research` job for each contact that has a valid company domain and does not already have a completed research record.

---

### Requirement 11: LLM Integration — Anthropic Claude as Primary Provider

**User Story:** As a developer, I want the platform to use the Anthropic Claude API as its primary and only supported LLM provider in MVP, with broken integrations to Google Gemini and OpenAI removed or clearly disabled, so that the system is stable and predictable.

#### Acceptance Criteria

1. THE Platform SHALL use only the Anthropic Claude API (`claude-3-5-sonnet-20241022` or newer) as the LLM provider for all AI features (lead scoring, company research, email generation, AI workspace, FSM voice prompts).
2. THE Platform SHALL remove or permanently disable all HTTP calls to the Google Gemini API endpoints — no code path in production SHALL attempt to call `api.generativeai.google.com` or any `v1beta` Gemini URL.
3. THE Platform SHALL remove or permanently disable all HTTP calls to the OpenAI API endpoints — no code path in production SHALL attempt to call `api.openai.com`.
4. WHEN the `ANTHROPIC_API_KEY` environment variable is absent or does not begin with `"sk-ant"`, THE Platform SHALL log a `CRITICAL` warning at startup and SHALL disable all LLM-dependent features, returning graceful degraded responses rather than crashing.
5. THE Platform SHALL enforce a per-tenant LLM Token_Budget defined in the Tenant's billing plan; WHEN a job would exceed the remaining budget, THE Platform SHALL abort the LLM call, record a `"token_budget_exceeded"` reason on the job, and notify the Tenant's admin.
6. ALL LLM prompts used for lead scoring, company research, and email generation SHALL be structured with: a system instruction section, a business context section populated from Business_Brain, a prospect data section populated from the contact record, and an output format specification requesting valid JSON responses.
7. WHEN an LLM API call returns a response that cannot be parsed as the expected JSON schema, THE Platform SHALL log the raw response, record the job as `"failed_with_reason: invalid_llm_response"`, and SHALL NOT propagate malformed data to the contact record.
8. THE Platform SHALL implement a 6-second hard timeout on all LLM API calls in background jobs and a 10-second timeout for AI Workspace streaming — WHEN a timeout occurs, THE Platform SHALL log it and apply the graceful fallback defined per feature.

---

### Requirement 12: Voice Call Pipeline — FSM, VAD, STT, TTS

**User Story:** As a sales manager, I want the AI voice agent to conduct outbound calls with a realistic persona, full compliance checking, and accurate transcription, so that prospects receive a professional experience and I have complete call records.

#### Acceptance Criteria

1. WHEN an outbound call is initiated, THE Compliance_Gate SHALL execute the full verification pipeline (DNC check, TCPA calling hours check, consent token check) before Twilio dials the PSTN leg — IF any check fails, THE Compliance_Gate SHALL block the call and return a `ComplianceException` with the specific violation reason.
2. THE FSM SHALL manage call state transitions through these phases in order: `CONNECTING` → `GREETING` → `QUALIFICATION` → `PITCH` → `OBJECTION_HANDLING` → `BOOKING` (or `REJECTION_CLOSE`) — each transition SHALL be logged with a timestamp.
3. THE VAD SHALL detect prospect speech interruptions using audio energy thresholds and SHALL interrupt the AI's TTS playback within 300ms of detecting a human voice above the configured energy threshold.
4. WHEN Deepgram STT produces a transcript segment, THE FSM SHALL use the Claude API to generate the AI agent's next response — THE FSM SHALL NOT call Google Gemini or OpenAI.
5. WHEN the Claude API call for a voice response exceeds 800ms, THE FSM SHALL inject a latency-masking audio filler phrase (e.g., "Let me just pull that up for you...") to prevent dead air — THE FSM SHALL NOT play raw silence bytes (`b'\x00' * 32000`) as a filler.
6. THE LLM safety guard SHALL produce human-sounding recovery phrases (e.g., "Let me make sure I have the right details for you — I'll follow up on that.") when a prompt fails safety or grounding validation — THE safety guard SHALL NOT respond with `"I am an AI assistant and cannot assist with that."` during a live call.
7. WHEN a call concludes, THE Platform SHALL compile the left (prospect) and right (AI agent) audio channels into a stereo WAV file and persist it to the Tenant's Supabase Storage bucket using the resolved `tenant_id`.
8. WHEN the call recording is uploaded, THE Platform SHALL insert a `call_logs` record including `tenant_id`, `phone_number`, `duration_seconds`, `final_state`, `recording_url`, and `transcript` array.
9. THE TTS provider (ElevenLabs) SHALL be called with the agent's configured voice ID from Business_Brain; IF ElevenLabs is unavailable, THE Platform SHALL fall back to a pre-recorded PCM audio buffer (not silent bytes) to maintain call continuity.
10. WHEN a call completes for a known contact (by phone number match), THE Platform SHALL create an `activities` CRM record with `type: "call"`, `duration_seconds`, `outcome`, `ai_summary`, and `created_by_ai: true`.

---

### Requirement 13: TCPA/DNC Compliance Gate

**User Story:** As a compliance officer, I want every outbound call to pass a full compliance gate before dialing, so that Visoora never places a call that violates TCPA regulations or our internal DNC list.

#### Acceptance Criteria

1. WHEN the Compliance_Gate runs, THE Platform SHALL check the target phone number against the Tenant's DNC registry in Supabase (or local JSON fallback); IF the number is found, THE Platform SHALL raise a `DNCBlockedException` with HTTP 403 and reason `"DNC_BLOCKED"`.
2. THE Platform SHALL infer the recipient's local timezone from the E.164 phone number area code using the `phonenumbers` library; WHEN the inferred local time is outside 8:00 AM–8:59 PM, THE Platform SHALL raise an `OutsideCallingHoursException` with HTTP 403 and reason `"OUTSIDE_CALLING_HOURS"`, including the next available calling window.
3. WHEN a consent token is missing from the call request, THE Platform SHALL raise a `ConsentRequiredException` with HTTP 403 and reason `"CONSENT_REQUIRED"`.
4. WHEN a consent token is provided, THE Platform SHALL verify: the token is a valid UUID format, the token matches the target phone number, the token belongs to the Tenant, and the token has not expired (expiry date in the future) — IF any check fails, THE Platform SHALL raise a `ConsentRequiredException` with the specific failure reason.
5. THE Compliance_Gate SHALL check the Tenant's billing status before allowing any call; WHEN the Tenant's calling minute balance is zero or the subscription is suspended, THE Platform SHALL raise a `ComplianceException` with HTTP 402 and reason `"BILLING_SUSPENDED_NO_MINUTES"`.
6. WHEN a User adds a phone number to the DNC registry via `POST /compliance/dnc/add`, THE Platform SHALL persist the record to both Supabase and the local JSON fallback and SHALL return `{ "success": true }` within 2 seconds.
7. THE Compliance_Gate SHALL be fully bypassed ONLY for onboarding test calls where the User has explicitly initiated the call from the Onboarding_Wizard — this bypass SHALL be limited to numbers provided by the authenticated User and SHALL be logged with reason `"onboarding_test_call"`.

---

### Requirement 14: Lightweight CRM — Contacts, Deals, Pipeline, and Activities

**User Story:** As a sales manager, I want a built-in CRM that tracks my prospects' contact details, deal stages, and interaction history, so that I don't need a separate CRM tool for the prospects I'm working in Visoora.

#### Acceptance Criteria

1. THE CRM SHALL provide CRUD operations for Contacts, Companies, Deals, Pipeline Stages, and Activities, with all records scoped by `tenant_id`.
2. WHEN a User creates a Contact, THE Platform SHALL validate that `phone_e164` is in E.164 format (starts with `"+"`, length between 8 and 18 characters); IF validation fails, THE Platform SHALL return HTTP 422.
3. WHEN a User creates a Contact with an email address, THE Platform SHALL validate that the email contains `"@"` and `"."` and has a minimum length of 5 characters; IF validation fails, THE Platform SHALL return HTTP 422.
4. THE CRM SHALL support a `lead_score` field (integer 0–100) and a `tags` field (array of strings) on Contact records, both updatable by both human Users and AI background jobs.
5. THE CRM SHALL maintain a `deal_stage_history` table recording every stage transition for a Deal, including `from_stage_id`, `to_stage_id`, `changed_at`, `changed_by`, and `reason`.
6. WHEN the AI auto-advances a Deal to a new pipeline stage based on call outcome, THE Platform SHALL record the transition in `deal_stage_history` with `changed_by: "ai"` and a reason string derived from the call's `final_state`.
7. WHEN a User views the pipeline board at `/pipeline`, THE Platform SHALL fetch all Deals grouped by stage from the authenticated Tenant and display stage names, deal counts, and total values — THE Platform SHALL NOT display deals belonging to other tenants.
8. THE CRM SHALL support `custom_fields` (key-value JSONB) on Contact and Deal records, allowing AI jobs to write enrichment data (research results, score explanations) without requiring schema migrations.
9. WHEN a contact's `lead_score` is updated by the Lead_Scorer, THE CRM SHALL immediately reflect the new score and explanation on the contact's detail view without requiring a page refresh.

---

### Requirement 15: Billing and Subscription Management

**User Story:** As a business owner, I want to manage my subscription plan and see my usage clearly, so that I know what I'm paying for and can upgrade when I need more capacity.

#### Acceptance Criteria

1. THE Platform SHALL integrate with Stripe for subscription plan management; WHEN a Tenant upgrades or downgrades their plan, THE Platform SHALL reflect the new plan limits (calling minutes, LLM tokens, contact seats) within 60 seconds.
2. WHEN Stripe sends a webhook event (`invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`), THE Platform SHALL process it within 10 seconds and update the Tenant's billing status in the database.
3. THE Platform SHALL expose a `GET /billing/usage` endpoint returning the Tenant's current period usage: minutes consumed, tokens consumed, contacts imported, and percentage of each limit used.
4. WHEN the Tenant reaches 80% of any usage limit, THE Platform SHALL send a notification email to the Tenant's admin and display a warning banner in the UI.
5. WHEN the Tenant reaches 100% of their calling minute limit, THE Compliance_Gate SHALL block all new outbound calls with HTTP 402 reason `"BILLING_SUSPENDED_NO_MINUTES"` until the plan is upgraded or the period resets.
6. THE Stripe webhook handler SHALL verify the Stripe-Signature header using the configured webhook secret before processing any event; IF signature verification fails, THE Platform SHALL return HTTP 400 and log the failure.

---

### Requirement 16: Observability, Error Monitoring, and Logging

**User Story:** As an operator, I want every error, slow query, and failed job to be automatically captured and reported, so that I can diagnose and fix production issues quickly without relying on user-reported bug reports.

#### Acceptance Criteria

1. THE Platform SHALL integrate Sentry for exception tracking; WHEN any unhandled exception propagates to a FastAPI exception handler, THE Platform SHALL capture it to Sentry with the tenant_id, user_id, and request path as context tags.
2. ALL structured log entries SHALL use `structlog` with the following standard fields: `event`, `timestamp`, `tenant_id`, `correlation_id`, `level` — log entries SHALL NOT contain raw JWT tokens, API keys, or passwords.
3. WHEN a background job fails, THE Platform SHALL send the failure event to Sentry including the `job_id`, `job_type`, `tenant_id`, and full exception traceback.
4. THE Platform SHALL emit Prometheus metrics for: total API request count by endpoint and status code, job queue depth by job type, LLM API call latency (p50/p90/p99) per tenant, and call pipeline stage durations.
5. WHEN the LLM API call latency for any single request exceeds 3,000ms, THE Platform SHALL log a `WARN` event with `event: "llm_latency_exceeded"` and the actual latency value.
6. THE Platform SHALL configure Sentry to capture at least 10% of successful request traces (performance tracing) and 100% of error events.
7. THE observability stack (Prometheus, Grafana, Alertmanager) SHALL be deployable via the existing `docker-compose.observability.yml` configuration and SHALL include pre-built dashboard panels for call volume, job queue health, and LLM latency.

---

### Requirement 17: Production Hardening and Security

**User Story:** As a CTO, I want the platform to be hardened against common web security vulnerabilities and misconfiguration risks before launch, so that customer data is protected and regulatory obligations are met.

#### Acceptance Criteria

1. THE Platform SHALL implement rate limiting on all public endpoints: authentication endpoints SHALL be rate-limited to 10 requests per minute per IP address; AI workspace endpoints SHALL be rate-limited to 60 requests per minute per tenant.
2. THE Platform SHALL set the following HTTP security headers on all API responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Content-Security-Policy` with a restrictive policy.
3. THE Platform SHALL sanitize all user-supplied string inputs before including them in LLM prompts to prevent prompt injection — control characters, HTML tags, and strings exceeding 5,000 characters SHALL be stripped or truncated before prompt construction.
4. THE Platform SHALL store all API keys, database credentials, and Stripe secrets exclusively in environment variables — no secret value SHALL be committed to the source repository or logged.
5. WHEN a CSV file is uploaded, THE Platform SHALL validate that the file MIME type is `text/csv`, `application/vnd.ms-excel`, or `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and that the file size is ≤ 10MB; IF either check fails, THE Platform SHALL return HTTP 422.
6. THE Platform SHALL enforce HTTPS for all production traffic; HTTP requests to the production domain SHALL be redirected to HTTPS with a 301 status code.
7. THE Platform SHALL use the Supabase service role key exclusively for server-side operations — the frontend SHALL never receive or store the service role key and SHALL use only Supabase anon or user-scoped keys.
8. THE Platform SHALL implement CSRF protection for all state-mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) by verifying that the `Origin` or `Referer` header matches the expected application domain.

---

### Requirement 18: Onboarding Test Call

**User Story:** As a new customer completing setup, I want to place a test call to my own phone from the wizard, so that I can verify the AI agent's voice, persona, and script before activating it for real prospects.

#### Acceptance Criteria

1. WHEN a User submits a test call request from the Onboarding_Wizard, THE Platform SHALL pre-enroll a temporary consent token for the User's own phone number with a 24-hour expiry before initiating the Twilio dial.
2. THE test call SHALL use the Tenant's configured agent name, voice, tone, greeting script, and product knowledge from the Business_Brain that has been saved up to that point.
3. THE test call SHALL bypass DNC and TCPA calling-hours checks, since the User is explicitly calling their own number during setup — this bypass SHALL be logged with reason `"onboarding_test_call"`.
4. WHEN a test call completes, THE Platform SHALL display a call summary in the wizard (duration, transcript preview) to confirm the agent is configured correctly.
5. IF the Twilio credentials are not configured (sandbox mode), THEN THE Platform SHALL simulate the test call using the local mock FSM and display a simulated transcript — THE Platform SHALL NOT fail the onboarding flow due to missing Twilio credentials.

---

### Requirement 19: Settings — Business Brain Updates, Compliance, and Email Configuration

**User Story:** As a business owner, I want to update my business settings after onboarding without having to restart the wizard, so that the AI stays accurate as my business evolves.

#### Acceptance Criteria

1. WHEN a User navigates to `/settings`, THE Platform SHALL load the current Business_Brain values from `agent_configs` and pre-fill all form fields — THE Platform SHALL NOT display a blank form.
2. WHEN a User saves updated Business_Brain settings, THE Platform SHALL persist the changes to `agent_configs` within 3 seconds and SHALL use the new values for all jobs enqueued after the save.
3. WHEN a User navigates to `/settings/compliance`, THE Platform SHALL display the current `recording_disclosure_enabled`, `recording_disclosure_text`, `ai_disclosure_enabled`, and `ai_disclosure_text` settings and allow the User to update them.
4. WHEN a User navigates to `/settings/email`, THE Platform SHALL allow the User to configure the outbound email sender name, reply-to address, and daily send limit.
5. WHEN a User updates compliance settings, THE Platform SHALL persist the changes to `tenant_compliance_settings` within 3 seconds and SHALL apply the new disclosure texts to all calls placed after the save.

---

### Requirement 20: Knowledge Base, FAQs, and Objections Management

**User Story:** As a sales manager, I want to maintain a library of FAQs and objection rebuttals that the AI uses during calls and email generation, so that the AI always handles common objections the way I want.

#### Acceptance Criteria

1. WHEN a User navigates to `/knowledge`, THE Platform SHALL display the current FAQ entries and objection-rebuttal pairs loaded from the Tenant's Business_Brain.
2. WHEN a User adds a new FAQ entry (question + answer), THE Platform SHALL append it to the `kb_faqs` array in `agent_configs.persona` within 3 seconds.
3. WHEN a User adds a new objection-rebuttal pair, THE Platform SHALL append it to the `objections_list` array in `agent_configs.persona` within 3 seconds.
4. THE FSM voice pipeline SHALL inject the Tenant's FAQ and objections library into the system prompt for every Claude call during live calls, so the agent can reference them when prospects raise matching objections.
5. WHEN the total FAQ and objections text exceeds 3,000 tokens, THE Platform SHALL truncate to the 3,000 token limit by prioritizing the most recently updated entries — THE Platform SHALL display a `"Knowledge base truncated to fit context window"` warning in the settings UI.

---

### Requirement 21: Frontend API Client and Loading States

**User Story:** As a User, I want all pages to display real data with proper loading and error states, so that I always know whether data is being fetched, failed, or ready to view.

#### Acceptance Criteria

1. EVERY frontend page that fetches data from the backend SHALL display a loading skeleton or spinner while the request is in flight — THE Platform SHALL NOT render empty lists or zero-value metrics as the initial state.
2. WHEN a backend API call returns an error (4xx or 5xx), THE Platform SHALL display a user-readable error message inline on the page (not an unhandled JavaScript exception) and SHALL log the error to Sentry.
3. ALL frontend API calls that require authentication SHALL include the `Authorization: Bearer <JWT>` header constructed from the `visoora_session_token` cookie using the `getAuthHeaders()` utility.
4. WHEN a frontend API call returns HTTP 401 or 403, THE Platform SHALL clear the session cookies and redirect the User to `/login` — THE Platform SHALL NOT display a blank or broken page.
5. THE frontend SHALL not make more than one concurrent request to the same analytics endpoint per page load; duplicate in-flight requests SHALL be deduplicated using a request cache or React Query `staleTime` configuration.

---

### Requirement 22: Parser and Serializer Correctness for Business Brain and Job Payloads

**User Story:** As a developer, I want all structured data round-tripping through JSON (Business Brain config, job payloads, research data) to survive serialize-parse cycles without data loss or corruption, so that AI features never operate on stale or malformed context.

#### Acceptance Criteria

1. THE Platform SHALL serialize and deserialize the Business_Brain `persona` JSON blob such that FOR ALL valid Persona objects, serializing to JSON and then deserializing SHALL produce an object equal to the original.
2. THE Job_Queue SHALL serialize and deserialize job payloads such that FOR ALL valid job payload objects (for all supported job types), a round-trip through JSON serialization SHALL produce a payload structurally and value-identical to the original.
3. THE Platform SHALL serialize and deserialize company research data (`sourced_facts`, `estimates`) such that FOR ALL valid Research objects, a round-trip through JSON SHALL preserve all fact entries, all estimate entries, and all source URLs without truncation.
4. WHEN the LLM returns a JSON response that fails schema validation, THE Platform SHALL log the raw response body before discarding it — no schema-invalid LLM output SHALL be silently swallowed.
5. THE Platform SHALL reject any contact import row where the parsed phone number cannot be re-serialized to the same canonical E.164 string — rows where `normalize(parse(phone)) != original_phone_column` SHALL be flagged as `"invalid format"` in the import detail report.
