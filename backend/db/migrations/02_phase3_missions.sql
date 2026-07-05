-- Phase 3: AI Mission Orchestrator Migrations

-- Table: missions
-- The enterprise orchestration object representing a high-level goal (e.g. Outbound Campaign, Growth Audit)
CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL,
    business_brain_id UUID REFERENCES business_brains(id) ON DELETE CASCADE,
    mission_type TEXT NOT NULL, -- e.g., 'Outbound Campaign', 'Growth Audit'
    goal TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'planning', -- planning, running, waiting_approval, paused, completed, failed
    execution_mode TEXT DEFAULT 'autonomous', -- autonomous, human_in_the_loop
    progress JSONB DEFAULT '[]'::jsonb,
    success_metrics JSONB DEFAULT '{}'::jsonb,
    budget JSONB DEFAULT '{"max_cost": 5.0, "max_tokens": 100000, "max_calls": 0, "max_emails": 100}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: mission_artifacts
-- Agents communicate purely through artifacts, enabling loose coupling and DAG dependencies.
CREATE TABLE IF NOT EXISTS mission_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL, -- e.g., 'company_intelligence', 'qualified_leads', 'email_draft'
    content JSONB DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: mission_tasks
-- A single step in the execution graph (DAG) assigned to a specific worker/agent.
CREATE TABLE IF NOT EXISTS mission_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL, -- e.g., 'research_agent', 'email_agent', 'prospecting_agent', 'planning_agent'
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, waiting_approval, success, failed
    dependencies JSONB DEFAULT '[]'::jsonb, -- Array of parent task UUIDs that must complete first
    payload JSONB DEFAULT '{}'::jsonb, -- Input instructions
    result_artifact_id UUID REFERENCES mission_artifacts(id) ON DELETE SET NULL, -- Output artifact
    cost NUMERIC(10, 6) DEFAULT 0,
    tokens INTEGER DEFAULT 0,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: mission_events
-- Telemetry for monitoring, analytics, and debugging the mission lifecycle.
CREATE TABLE IF NOT EXISTS mission_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
    task_id UUID REFERENCES mission_tasks(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- 'mission_created', 'task_started', 'task_completed', 'waiting_approval'
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_missions_modtime ON missions;
CREATE TRIGGER update_missions_modtime
BEFORE UPDATE ON missions
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

DROP TRIGGER IF EXISTS update_mission_artifacts_modtime ON mission_artifacts;
CREATE TRIGGER update_mission_artifacts_modtime
BEFORE UPDATE ON mission_artifacts
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

DROP TRIGGER IF EXISTS update_mission_tasks_modtime ON mission_tasks;
CREATE TRIGGER update_mission_tasks_modtime
BEFORE UPDATE ON mission_tasks
FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
