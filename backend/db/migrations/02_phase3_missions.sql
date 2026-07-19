CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_step VARCHAR(255),
    memory_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    mission_id UUID REFERENCES missions(id) ON DELETE CASCADE,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB,
    source VARCHAR(255),
    provider VARCHAR(255),
    duration_ms FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_events_mission_id ON audit_events(mission_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events(event_type);
