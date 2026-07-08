# Recommended Architecture Diagrams

## 1. System Architecture

```mermaid
flowchart TD
    Client[Next.js Client] --> API(FastAPI Gateway)
    
    API --> Supabase[(Supabase DB & Auth)]
    API --> Redis[(Redis)]
    
    Redis --> |Queue| CeleryWorker[Celery Mission Workers]
    
    CeleryWorker --> AI[AI Gateway (BaseLLMProvider)]
    AI --> OpenAI[OpenAI API]
    AI --> Anthropic[Anthropic API]
    
    CeleryWorker --> Notifier[NotificationProvider]
    Notifier --> Resend[Resend Email]
    
    CeleryWorker --> |Status Updates| Redis
    Redis --> |PubSub| Websocket(FastAPI WS Manager)
    Websocket --> |SSE/WS| Client
```

## 2. Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant NextJS as Frontend
    participant FastAPI as Backend
    participant Supabase as Supabase Auth
    
    User->>NextJS: Login Request
    NextJS->>Supabase: Authenticate
    Supabase-->>NextJS: JWT (Access + Refresh)
    NextJS->>NextJS: Store in Secure HTTP-Only Cookie
    
    User->>NextJS: Navigate to /dashboard
    NextJS->>NextJS: @supabase/ssr validate JWT
    NextJS-->>User: Render Dashboard
    
    NextJS->>FastAPI: GET /api/data (Bearer JWT)
    FastAPI->>FastAPI: verify_supabase_jwt()
    FastAPI->>FastAPI: Extract tenant_id from claims
    FastAPI->>DB: Query WHERE tenant_id = X
```

## 3. Worker Queue Architecture

```mermaid
flowchart LR
    API[FastAPI] --> |task.delay()| RedisQueue[(Redis Queue)]
    
    subgraph Celery Cluster
        Worker1[Worker Node 1]
        Worker2[Worker Node 2]
    end
    
    RedisQueue --> Worker1
    RedisQueue --> Worker2
    
    Worker1 --> |Success| DB[(PostgreSQL)]
    Worker1 --> |Transient Failure| RedisQueue
    Worker1 --> |Hard Failure| DeadLetter[(DLQ)]
```

## 4. AI Pipeline (Abstracted)

```mermaid
classDiagram
    class BaseLLMProvider {
        <<interface>>
        +generate(prompt, schema)
    }
    class OpenAIProvider {
        +generate(prompt, schema)
    }
    class ClaudeProvider {
        +generate(prompt, schema)
    }
    
    BaseLLMProvider <|-- OpenAIProvider
    BaseLLMProvider <|-- ClaudeProvider
    
    class MissionEngine {
        -llm_provider: BaseLLMProvider
        +run_research()
    }
    
    MissionEngine --> BaseLLMProvider
```
