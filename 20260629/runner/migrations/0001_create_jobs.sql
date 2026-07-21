CREATE TABLE IF NOT EXISTS jobs (
    job_id        UUID PRIMARY KEY,
    target        TEXT        NOT NULL,
    n             BIGINT      NOT NULL,
    concurrency   BIGINT      NOT NULL,
    status        TEXT        NOT NULL,
    created_count BIGINT      NOT NULL DEFAULT 0,
    conflict_count BIGINT     NOT NULL DEFAULT 0,
    attempt_count BIGINT      NOT NULL DEFAULT 0,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    duration_ms   BIGINT,
    error         TEXT
);
