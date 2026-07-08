# Production Readiness Audit Report
**Date:** July 2026
**Scope:** Visoora SaaS Platform

This document assesses the production readiness of Visoora, identifying release blockers and areas needing fortification before pilot onboarding.

## 1. Authentication & Tenant Isolation
| Issue | Severity | Risk | Recommendation / Fix | Priority | Estimated Effort |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Email redirects point to `localhost` | **CRITICAL** | Users cannot log in or verify email on production. Complete auth flow failure. | Update Supabase redirect URLs and `NEXT_PUBLIC_SITE_URL` env variable in production. | P0 | 1 Hour |
| Generic Supabase Email Templates | **HIGH** | Reduces brand trust. Looks like an unfinished project. | Integrate Resend. Swap Supabase default templates for custom-branded HTML templates. | P0 | 4 Hours |
| Supabase RLS Policies | **HIGH** | Missing or overly permissive Row Level Security can lead to cross-tenant data leaks. | Audit all tables (e.g., `missions`, `contacts`). Enforce RLS matching `auth.uid()`. | P0 | 3 Hours |
| Session Expiry & Refresh | **MEDIUM** | Users might get silently logged out. | Verify Next.js middleware token refresh logic properly handles expired Supabase tokens. | P1 | 2 Hours |

## 2. Infrastructure & Environment
| Issue | Severity | Risk | Recommendation / Fix | Priority | Estimated Effort |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Hardcoded localhost in APIs | **CRITICAL** | Frontend will try to fetch backend on `localhost:8000` in production. | Replace with `NEXT_PUBLIC_API_URL` env variable. | P0 | 1 Hour |
| Secrets Management | **HIGH** | Hardcoded secrets or `.env` files in source control. | Ensure Vercel (Frontend) and Render/AWS (Backend) use managed environment variables. Remove `.env` from repo. | P0 | 1 Hour |
| CORS Configuration | **HIGH** | Backend restricts or overly permits origins. | Update FastAPI `ALLOWED_ORIGINS` to include production domains strictly. | P0 | 30 Mins |

## 3. Mission Engine & Workers
| Issue | Severity | Risk | Recommendation / Fix | Priority | Estimated Effort |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Missing Worker Queues | **HIGH** | Long-running AI missions block API threads, causing timeouts (504s). | Introduce Celery/Redis or BullMQ for async processing of AI tasks. | P1 | 1-2 Days |
| Rate Limiting (LLMs & Emails) | **HIGH** | API abuse or runaway loops can drain OpenAI credits and get email accounts suspended. | Add rate limiting via Redis per tenant. Add hard caps on daily AI requests. | P0 | 4 Hours |
| Retry Logic | **MEDIUM** | Transient errors (e.g., OpenAI API timeout) fail entire missions. | Implement exponential backoff for external API calls using `tenacity`. | P1 | 2 Hours |

## 4. Observability & Analytics
| Issue | Severity | Risk | Recommendation / Fix | Priority | Estimated Effort |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Missing Error Tracking | **HIGH** | Silent failures during pilot onboarding. | Ensure Sentry is fully configured in both Next.js and FastAPI. | P0 | 2 Hours |
| No Structured Logging | **MEDIUM** | Hard to trace asynchronous AI agent reasoning. | Use `structlog` in Python backend to attach `tenant_id` and `mission_id` to all logs. | P1 | 3 Hours |

## Summary of Action Plan
To unblock the pilot launch, **Authentication, Environment Variables, CORS, and Branded Emails (P0 items)** must be resolved immediately. Worker queues and observability are fast-follows for scale.
