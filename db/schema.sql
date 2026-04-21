CREATE TABLE IF NOT EXISTS runs (
    id               SERIAL PRIMARY KEY,
    query            TEXT        NOT NULL,
    company          TEXT,
    region           TEXT,
    risk_score       NUMERIC(5,2),
    risk_label       VARCHAR(20),
    judge_verdict    TEXT,
    bear_analysis    TEXT,
    bull_analysis    TEXT,
    geopolitical_analysis TEXT,
    guardrail_report JSONB,
    final_output     JSONB,
    partial_context  BOOLEAN     DEFAULT FALSE,
    failed_sources   TEXT[]      DEFAULT '{}',
    created_at       TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Migrations: add columns if upgrading an existing DB
ALTER TABLE runs ADD COLUMN IF NOT EXISTS partial_context BOOLEAN DEFAULT FALSE;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS failed_sources  TEXT[]  DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_risk_score  ON runs (risk_score DESC);
