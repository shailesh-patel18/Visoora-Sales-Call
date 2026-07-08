# Visoora System Architecture

This document outlines the high-level architecture of the Visoora AI Revenue Operating System.

## System Flow

```mermaid
flowchart TD
    Client[Web Browser / Next.js] --> |REST / JWT| APIGateway(FastAPI Backend)
    
    subgraph Auth Layer
        APIGateway --> SupabaseAuth[Supabase Auth]
    end

    subgraph Data Layer
        APIGateway --> DB[(PostgreSQL / Supabase)]
        APIGateway --> Cache[(Redis)]
    end

    subgraph Mission Engine (Async Workers)
        Cache --> |Task Queue| CeleryWorker[Python Async Workers]
        CeleryWorker --> DB
        CeleryWorker --> AI[AI Providers: OpenAI/Anthropic/Google]
        CeleryWorker --> EmailAPI[Resend / Email API]
    end

    Client --> |Real-time Updates| Websocket(FastAPI WebSockets)
    CeleryWorker --> |Publish Events| Cache
    Cache --> |Subscribe| Websocket
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant NextJS as Frontend (Next.js)
    participant FastAPI as Backend
    participant Supabase as Supabase Auth
    
    User->>NextJS: Submits Signup Form
    NextJS->>Supabase: POST /auth/v1/signup
    Supabase-->>NextJS: Success (Sends Email)
    NextJS-->>User: Show "Check your email"
    
    Note over User, Supabase: User clicks link in Email
    
    Supabase->>NextJS: Redirect to /auth/callback?code=...
    NextJS->>Supabase: Exchange code for session
    Supabase-->>NextJS: Access Token + Refresh Token
    NextJS->>NextJS: Set `visoora_logged_in` & Supabase Cookies
    NextJS-->>User: Redirect to /dashboard
    
    Note over NextJS, FastAPI: API Requests
    
    NextJS->>FastAPI: GET /api/v1/tenant (Bearer Token)
    FastAPI->>Supabase: Verify JWT
    Supabase-->>FastAPI: Valid Token (UID)
    FastAPI->>DB: Fetch Tenant Data
    DB-->>FastAPI: Data
    FastAPI-->>NextJS: JSON Response
```

## Mission & AI Pipeline Flow

```mermaid
flowchart LR
    A[User Configure Mission] --> B[Save to DB]
    B --> C[Push to Redis Queue]
    C --> D(Celery Worker: Planning)
    D --> E(Celery Worker: Research)
    E --> F[AI API (OpenAI)]
    F --> E
    E --> G(Celery Worker: Copywriting)
    G --> H[Drafts saved to DB]
    H --> I[Notify User via Email/App]
    I --> J{User Approval}
    J -->|Approved| K[Send Email via Resend]
    J -->|Rejected| L[Update AI Context & Retry]
```

## Deployment Architecture

```mermaid
architecture-beta
    group frontend(cloud)[Frontend Cloud]
    service vercel(internet)[Vercel Edge] in frontend
    
    group backend(cloud)[Backend Cloud]
    service render(server)[Render / AWS ECS] in backend
    service redis(database)[Managed Redis] in backend
    
    group data(cloud)[Data Cloud]
    service supabase(database)[Supabase PostgreSQL] in data
    
    vercel:R -- L:render
    render:R -- L:redis
    render:T -- B:supabase
    vercel:T -- B:supabase
```
