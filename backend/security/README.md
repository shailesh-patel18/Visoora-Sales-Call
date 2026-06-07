# Visoora Sales Call Orchestration Backend: Security & Compliance Runbook

This document defines the deployment, operation, and architecture details of the security and compliance layer implemented inside the Visoora Sales Call Orchestration VoIP engine.

---

## 1. Security Architecture Overview

The backend enforces a zero-trust, multi-tenant isolation structure using five core components:

```
                  ┌──────────────────────────────────────────────┐
                  │            Incoming HTTP Requests            │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
      [/incoming-call, /media-stream]                 [/api/logs, /api/campaigns]
      (Twilio Webhook / WebSockets)                     (Dashboard REST / Live WS)
                 │                                               │
    ┌────────────┴────────────┐                    ┌─────────────┴─────────────┐
    │ Twilio Signature Verify │                    │    Bearer Token Verify    │
    │   (verify_twilio_auth)  │                    │   (verify_supabase_jwt)   │
    └────────────┬────────────┘                    └─────────────┬─────────────┘
                 │                                               │
                 │                                   ┌───────────┴───────────┐
                 │                                   │   Supabase Auth JWKS  │
                 │                                   │  (RSA Algorithm cache)│
                 │                                   └───────────┬───────────┘
                 │                                               │
                 │                                   ┌───────────┴───────────┐
                 │                                   │      RBAC Filter      │
                 │                                   │ (RoleChecker checker) │
                 │                                   └───────────┬───────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                           ┌───────────────────────────┐
                           │   Tenant Rate Limiter     │
                           │ (Redis sliding-window ZSet│
                           │   or Local Memory fallb.) │
                           └─────────────┬─────────────┘
                                         ▼
                           ┌───────────────────────────┐
                           │    Service Execution      │
                           └───────────────────────────┘
```

---

## 2. Environment Configurations

Define the following environment variables to activate all production security layers:

```bash
# Supabase JWT key validation
SUPABASE_URL=https://your-project-ref.supabase.co
# Optional path override for JWKS key location
SUPABASE_JWKS_URL=https://your-project-ref.supabase.co/auth/v1/jwks

# Twilio Signature validation
TWILIO_AUTH_TOKEN=your_real_twilio_auth_token_here

# Redis connection URL for rate limiting
REDIS_URL=redis://:password@your-redis-host:6379/0

# M2M keys (comma-separated list of highly secure client tokens)
SYSTEM_API_KEYS=key_system_prod_a189f3,key_analytics_engine_b981e4
```

---

## 3. RFC 7807 Problem Details Standard

All security validation, database, and rate-limiting exceptions are caught by the `rfc7807_exception_handler` and returned under standard `application/problem+json` format.

### Example: Rate Limit Exceeded (HTTP 429)
```json
{
  "type": "https://visoora.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Tenant 'WayneCorp' has reached the limit of 10 concurrent active calls.",
  "instance": "/api/campaigns/dial"
}
```

### Example: Authentication Failure (HTTP 401)
```json
{
  "type": "https://visoora.com/errors/unauthenticated",
  "title": "Authentication Failed",
  "status": 401,
  "detail": "Session expired. Please log in again.",
  "instance": "/api/logs"
}
```

---

## 4. Operational Runbook

### Key Rotations (Supabase JWKS)
- **Zero-downtime rotation**: Supabase rotates cryptographic keys dynamically. The `JWKService` automatically intercepts rotational changes by fetching updated signatures on Key ID (`kid`) cache misses. No manual server reload is required.

### Rate Limiting Overrides
- **Adjust quotas**: Daily rate limit boundaries are set to 500 requests per tenant, with concurrency capped at 10 active calls.
- **Failover behavior**: If your Redis instance drops or runs out of memory, the server logs `redis_offline_fallback` and falls back automatically to a thread-safe, in-memory sliding window manager, preserving uptime.
