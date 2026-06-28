# Visoora Deployment Guide

## Runtime Shape

V1 should run as one FastAPI service plus Redis. The current codebase contains one deployable backend process (`server.twilio_handler:app`) that owns HTTP APIs, Twilio webhooks, dashboard WebSockets, and Twilio Media Streams. Redis is used for rate limiting and session routing; without Redis, the app falls back to local memory for development only.

## Required Production Environment

Set these variables for every production deployment:

- `APP_ENV=production`
- `SERVER_PUBLIC_DOMAIN=<public https host without path>`
- `ALLOWED_ORIGINS=<frontend origin list>`
- `TWILIO_ACCOUNT_SID=<real account sid>`
- `TWILIO_AUTH_TOKEN=<real auth token>`
- `TWILIO_TRIAL_NUMBER=<Twilio voice-capable number>`
- `REDIS_URL=<managed Redis URL>`
- `SUPABASE_URL=<Supabase project URL>`
- `SUPABASE_SERVICE_ROLE_KEY=<service role key>`
- `SYSTEM_API_KEYS=<comma separated machine keys>`
- `WEB_CONCURRENCY=1` for free/small tiers

## Health Checks

- Liveness: `GET /health/live`
- Readiness: `GET /health/ready`
- Basic health: `GET /health`
- Prometheus metrics: `GET /metrics`

Readiness rejects traffic while shutting down, when node call capacity is full, or when Redis is unreachable in configured deployments.

## Twilio Configuration

Outbound calls are created by `POST /make-call` and point Twilio to:

- Voice webhook: `https://<SERVER_PUBLIC_DOMAIN>/incoming-call`
- Status callback: `https://<SERVER_PUBLIC_DOMAIN>/api/twilio-status-callback`
- Media Stream: generated as `wss://<SERVER_PUBLIC_DOMAIN>/media-stream`

Inbound tenant numbers should point to:

- Voice webhook: `https://<SERVER_PUBLIC_DOMAIN>/inbound-call`
- Media Stream: generated as `wss://<SERVER_PUBLIC_DOMAIN>/media-stream/inbound/{tenant_id}`

Do not use plain HTTP for Twilio Media Streams outside local testing.

## Render Free Tier

Use the backend Dockerfile as a Web Service.

Recommended settings:

- Instance type: Free
- Docker context: `backend`
- Health check path: `/health/live`
- `WEB_CONCURRENCY=1`
- Use external managed Redis if available. Render free plans may not include Redis in all accounts; without Redis, only development/demo traffic is appropriate.

The frontend should deploy as a separate static/Node service with `NEXT_PUBLIC_API_URL=https://<backend-host>`.

## Railway

Create one service from `backend/Dockerfile` and one Redis plugin/service.

Recommended settings:

- `PORT` provided by Railway
- `WEB_CONCURRENCY=1` initially
- `SERVER_PUBLIC_DOMAIN=<railway public domain>`
- `REDIS_URL=${{Redis.REDIS_URL}}`

Railway is the cleanest low-cost option for this repo because Redis and public HTTPS service discovery are straightforward.

## AWS EC2 Free Tier

Use a `t2.micro` or `t3.micro` Ubuntu host with Docker Compose:

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

Put Caddy, nginx, or an AWS load balancer in front for TLS. Set `SERVER_PUBLIC_DOMAIN` to the HTTPS domain. Keep `WEB_CONCURRENCY=1` on free-tier EC2.

## Scaling Notes

Move beyond one backend instance only after Redis is mandatory and sticky WebSocket routing is configured at the ingress/load balancer. Multiple workers or instances with local transcript/recording fallbacks can split call state unless Redis/Supabase are the source of truth.
