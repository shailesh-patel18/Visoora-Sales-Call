ALTER TABLE missions ADD COLUMN IF NOT EXISTS execution_time_ms FLOAT;
ALTER TABLE missions ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
ALTER TABLE missions ADD COLUMN IF NOT EXISTS planner_version VARCHAR(50) DEFAULT 'v1.0';
ALTER TABLE missions ADD COLUMN IF NOT EXISTS llm_version VARCHAR(50) DEFAULT 'unknown';

ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
-- The created_at in audit_events is already timestamp, but we can also add the explicit timestamp from the event model if we want, or just rely on created_at.
-- Let's stick with created_at for DB time and let payload have the event generation time.
