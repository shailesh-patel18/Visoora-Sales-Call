# Visoora System Architecture Diagram

You can copy this block and paste it directly into a Notion "Mermaid" block to render a beautiful, scalable visual architecture diagram!

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#111,stroke:#00F0FF,stroke-width:2px,color:#fff;
    classDef backend fill:#222,stroke:#10B981,stroke-width:2px,color:#fff;
    classDef agent fill:#00F0FF,stroke:#000,stroke-width:2px,color:#000,font-weight:bold;
    classDef database fill:#ffb347,stroke:#333,stroke-width:2px,color:#000;
    classDef external fill:#b19cd9,stroke:#333,stroke-width:2px,color:#000;
    classDef auth fill:#ff69b4,stroke:#333,stroke-width:2px,color:#000;

    %% 1. FRONTEND
    subgraph Frontend [Frontend: Next.js + Tailwind + Framer Motion]
        Landing[Landing Page]:::frontend
        Login[Supabase Auth UI]:::frontend
        Onboarding[Onboarding: Business Brain]:::frontend
        Dashboard[Command Center]:::frontend
        Creator[Mission Creator]:::frontend
        Cockpit[Approval Cockpit]:::frontend
    end

    %% 2. BACKEND (FASTAPI)
    subgraph Backend [Backend: Python FastAPI]
        AuthGuard[RBAC & Tenant Isolation]:::backend
        API_Gateway[API Router]:::backend
        JobEngine[Background Worker Engine]:::backend
        Followup[Cron: Follow-up Engine]:::backend
    end

    %% 3. DATABASES
    subgraph Databases [Data Storage]
        DB[(Supabase PostgreSQL)]:::database
        Redis[(Redis Task Queue & Cache)]:::database
        VectorDB[(Vector DB: RAG Memory)]:::database
    end

    %% 4. AI AGENT SWARM
    subgraph Agents [The Autonomous AI Agent Swarm]
        Planner[Planning Agent]:::agent
        Prospector[Prospecting Agent]:::agent
        Researcher[Research Agent]:::agent
        Scorer[Lead Scoring Engine]:::agent
        Writer[Email Generator Agent]:::agent
    end

    %% 5. EXTERNAL APIs
    subgraph External [Third-Party Integrations]
        Firecrawl[Firecrawl Website Scraper]:::external
        LLM[Claude 3.5 Sonnet / OpenAI]:::external
        Apollo[Apollo.io / ZoomInfo API]:::external
        Perplexity[Perplexity / Tavily API]:::external
        Nylas[Nylas / SMTP Email Dispatch]:::external
    end

    %% -- FLOW LOGIC --

    %% Auth Flow
    Landing --> Login
    Login <-->|JWT Tokens| AuthGuard
    
    %% Onboarding Flow
    Login --> Onboarding
    Onboarding -->|URL| Firecrawl
    Firecrawl -->|Scraped Content| LLM
    LLM -->|Extracts Value Prop| DB

    %% Mission Launch Flow
    Onboarding --> Dashboard
    Dashboard --> Creator
    Creator -->|POST /mission/launch| API_Gateway
    API_Gateway --> AuthGuard
    API_Gateway -->|Enqueue Task| Redis
    Redis --> JobEngine

    %% Agent Swarm Flow (Triggered by Worker)
    JobEngine --> Planner
    Planner --> Prospector
    Prospector <-->|Search ICP| Apollo
    Prospector --> Researcher
    Researcher <-->|Deep Web Search| Perplexity
    Researcher --> Scorer
    Scorer <-->|Checks against Business Brain| DB
    Scorer -->|Rejects Bad Leads| DB
    Scorer -->|Passes Good Leads| Writer
    Writer <-->|Fetch Tone of Voice| VectorDB
    Writer <-->|Prompting| LLM
    Writer -->|Saves Draft| DB

    %% Human in the Loop
    DB -->|WAITING_APPROVAL| Cockpit
    Cockpit -->|User Edits| VectorDB
    Cockpit -->|User Approves| DB

    %% Dispatch
    Followup -->|Reads QUEUED emails| DB
    DB -->|Passes Payload| Nylas
    Nylas -->|Delivers Email| Prospect((Prospect))
    Prospect -->|Replies| Nylas
    Nylas -->|Webhook| Backend
```
