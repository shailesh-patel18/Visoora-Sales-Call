# Missing Features (Critical for V1)

While Visoora has the core AI generation capabilities, it is missing features that enterprise users consider table-stakes for a B2B SaaS product.

## 1. Approval Cockpit
**Why it's needed:** Users will not trust an AI to blindly email their prospects. 
**Details:** An interface where users can view the generated draft, see the AI's reasoning (Mission Replay), edit the draft inline, and click "Approve" to send it to the queue.

## 2. Notification Center
**Why it's needed:** Asynchronous missions mean users won't be staring at the screen when tasks finish.
**Details:** An in-app bell icon and email digests (e.g., "You have 15 drafts awaiting approval"). Requires an abstracted `NotificationService`.

## 3. Mission Replay / AI Explainability
**Why it's needed:** "Why did the AI say this?"
**Details:** The system must log its intermediate reasoning steps. When a draft is presented, the user should be able to click "View Reasoning" and see the evidence (e.g., LinkedIn post snippet) that led to the draft.

## 4. Revenue-First Dashboard
**Why it's needed:** CEOs need to see ROI in 5 seconds.
**Details:** Replace vanity metrics with "Meetings Booked" and "Pipeline Generated ($)".

## 5. Mission Pause / Resume
**Why it's needed:** If a user spots a recurring mistake in the first 5 drafts, they need to halt the mission to tweak the prompt.
**Details:** A global "Kill Switch" or "Pause" button on active missions.
