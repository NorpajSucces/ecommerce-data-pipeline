BEGIN;

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    run_id UUID PRIMARY KEY,
    pipeline_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    failed_step TEXT,
    exit_code INTEGER,

    CONSTRAINT pipeline_runs_status_check
        CHECK (status IN ('running', 'succeeded', 'failed'))
);

ALTER TABLE audit.pipeline_runs
    DROP CONSTRAINT IF EXISTS pipeline_runs_finish_state_check;

ALTER TABLE audit.pipeline_runs
    ADD CONSTRAINT pipeline_runs_finish_state_check
        CHECK (
            (
                status = 'running'
                AND finished_at IS NULL
                AND failed_step IS NULL
                AND exit_code IS NULL
            )
            OR
            (
                status = 'succeeded'
                AND finished_at IS NOT NULL
                AND failed_step IS NULL
                AND exit_code = 0
            )
            OR
            (
                status = 'failed'
                AND finished_at IS NOT NULL
                AND failed_step IS NOT NULL
                AND length(btrim(failed_step)) > 0
                AND exit_code IS NOT NULL
                AND exit_code <> 0
            )
        );

COMMIT;
