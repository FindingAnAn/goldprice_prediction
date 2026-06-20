-- =============================================================================
-- Forecasting experiment registry.
-- One run_id correlates logs, filesystem artifacts, models and database rows.
-- =============================================================================

CREATE TABLE IF NOT EXISTS forecasting.model_runs (
    run_id                  VARCHAR(96) PRIMARY KEY,
    experiment_name         VARCHAR(160) NOT NULL,
    run_type                VARCHAR(40) NOT NULL,
    status                  VARCHAR(24) NOT NULL,
    started_at              TIMESTAMPTZ NOT NULL,
    completed_at            TIMESTAMPTZ,
    as_of_date              DATE,
    target_name             VARCHAR(80) NOT NULL,
    horizon_sessions        INTEGER NOT NULL,
    selected_model          VARCHAR(120),
    model_version           VARCHAR(120),
    data_hash               VARCHAR(64),
    feature_count           INTEGER,
    train_rows              INTEGER,
    validation_rows         INTEGER,
    test_rows               INTEGER,
    random_seed             INTEGER,
    artifact_dir            TEXT NOT NULL,
    log_path                TEXT NOT NULL,
    json_log_path           TEXT,
    duration_seconds        DOUBLE PRECISION,
    peak_rss_mb             DOUBLE PRECISION,
    average_cpu_percent     DOUBLE PRECISION,
    max_cpu_percent         DOUBLE PRECISION,
    read_bytes              BIGINT,
    write_bytes             BIGINT,
    config                  JSONB NOT NULL DEFAULT '{}'::JSONB,
    library_versions        JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_type              VARCHAR(160),
    error_message           TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_model_runs_status
        CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE TABLE IF NOT EXISTS forecasting.model_candidates (
    run_id                  VARCHAR(96) NOT NULL REFERENCES forecasting.model_runs(run_id) ON DELETE CASCADE,
    model_name              VARCHAR(120) NOT NULL,
    selected                BOOLEAN NOT NULL DEFAULT FALSE,
    parameters              JSONB NOT NULL DEFAULT '{}'::JSONB,
    cv_rmse                 DOUBLE PRECISION,
    holdout_rmse            DOUBLE PRECISION,
    holdout_mae             DOUBLE PRECISION,
    holdout_mape            DOUBLE PRECISION,
    holdout_r2              DOUBLE PRECISION,
    rmse_improvement_vs_persistence_pct DOUBLE PRECISION,
    training_seconds        DOUBLE PRECISION,
    artifact_path           TEXT,
    PRIMARY KEY (run_id, model_name)
);

CREATE TABLE IF NOT EXISTS forecasting.model_metrics (
    run_id                  VARCHAR(96) NOT NULL REFERENCES forecasting.model_runs(run_id) ON DELETE CASCADE,
    model_name              VARCHAR(120) NOT NULL,
    split_name              VARCHAR(32) NOT NULL,
    horizon_step            INTEGER NOT NULL DEFAULT 0,
    metric_name             VARCHAR(80) NOT NULL,
    metric_value            DOUBLE PRECISION,
    sample_count            INTEGER,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (run_id, model_name, split_name, horizon_step, metric_name)
);

CREATE TABLE IF NOT EXISTS forecasting.open_predictions (
    run_id                  VARCHAR(96) NOT NULL REFERENCES forecasting.model_runs(run_id) ON DELETE CASCADE,
    as_of_date              DATE NOT NULL,
    forecast_step           INTEGER NOT NULL,
    forecast_date           DATE NOT NULL,
    predicted_open          DOUBLE PRECISION NOT NULL,
    reference_close         DOUBLE PRECISION,
    predicted_change_amount DOUBLE PRECISION,
    predicted_change_pct    DOUBLE PRECISION,
    forecast_direction      VARCHAR(24),
    lower_80                DOUBLE PRECISION,
    upper_80                DOUBLE PRECISION,
    lower_95                DOUBLE PRECISION,
    upper_95                DOUBLE PRECISION,
    actual_open             DOUBLE PRECISION,
    absolute_error          DOUBLE PRECISION,
    percentage_error        DOUBLE PRECISION,
    is_estimated_date       BOOLEAN NOT NULL DEFAULT TRUE,
    top_reason_1            TEXT,
    top_reason_2            TEXT,
    top_reason_3            TEXT,
    explanation_method      VARCHAR(80),
    evaluated_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (run_id, forecast_step)
);

CREATE TABLE IF NOT EXISTS forecasting.stage_metrics (
    run_id                  VARCHAR(96) NOT NULL REFERENCES forecasting.model_runs(run_id) ON DELETE CASCADE,
    stage_name              VARCHAR(100) NOT NULL,
    duration_seconds        DOUBLE PRECISION NOT NULL,
    status                  VARCHAR(24) NOT NULL,
    details                 JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (run_id, stage_name)
);

CREATE TABLE IF NOT EXISTS forecasting.resource_metrics (
    run_id                  VARCHAR(96) NOT NULL REFERENCES forecasting.model_runs(run_id) ON DELETE CASCADE,
    metric_name             VARCHAR(100) NOT NULL,
    metric_value            DOUBLE PRECISION,
    unit                    VARCHAR(32) NOT NULL,
    recorded_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (run_id, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_model_runs_started_at
    ON forecasting.model_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_runs_status
    ON forecasting.model_runs (status);
CREATE INDEX IF NOT EXISTS idx_open_predictions_forecast_date
    ON forecasting.open_predictions (forecast_date);

ALTER TABLE forecasting.model_candidates
    ADD COLUMN IF NOT EXISTS rmse_improvement_vs_persistence_pct
        DOUBLE PRECISION;

ALTER TABLE forecasting.open_predictions
    ADD COLUMN IF NOT EXISTS reference_close DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS predicted_change_amount DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS predicted_change_pct DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS forecast_direction VARCHAR(24),
    ADD COLUMN IF NOT EXISTS top_reason_1 TEXT,
    ADD COLUMN IF NOT EXISTS top_reason_2 TEXT,
    ADD COLUMN IF NOT EXISTS top_reason_3 TEXT,
    ADD COLUMN IF NOT EXISTS explanation_method VARCHAR(80);
