use axum::{
    Json, Router,
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
};
use chrono::Utc;
use reqwest::Client;
use serde::Deserialize;
use serde_json::{Value, json};
use std::time::Instant;
use uuid::Uuid;

use crate::engine::{RunSpec, run_load};
use crate::store::{Job, JobStore};

#[derive(Clone)]
pub struct AppState {
    pub store: JobStore,
    pub client: Client,
}

#[derive(Deserialize)]
pub struct RunRequest {
    pub job_id: Uuid,
    pub target: String,
    pub n: u64,
    pub concurrency: usize,
}

/// Returns a minimal router that only serves `/healthz` — no DB state required.
/// Used by the unit test in `main.rs` to keep it DB-free.
pub fn healthz_router() -> Router {
    Router::new().route("/healthz", get(healthz))
}

/// Full application router: `/healthz` + all `/runs` routes wired to `state`.
pub fn app(state: AppState) -> Router {
    let api = Router::new()
        .route("/runs", post(create_run).get(list_runs))
        .route("/runs/{job_id}", get(get_run))
        .with_state(state);
    healthz_router().merge(api)
}

async fn healthz() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

async fn create_run(State(state): State<AppState>, Json(req): Json<RunRequest>) -> StatusCode {
    let job = Job {
        job_id: req.job_id,
        target: req.target.clone(),
        n: req.n as i64,
        concurrency: req.concurrency as i64,
        status: "running".to_string(),
        created_count: 0,
        conflict_count: 0,
        attempt_count: 0,
        started_at: Utc::now(),
        finished_at: None,
        duration_ms: None,
        error: None,
    };

    if let Err(e) = state.store.insert_running(job).await {
        tracing::error!("insert_running failed: {e}");
        return StatusCode::INTERNAL_SERVER_ERROR;
    }

    let job_id = req.job_id;
    let spec = RunSpec {
        target: req.target,
        n: req.n,
        concurrency: req.concurrency,
    };
    // Safety cap: n * 4 + 10_000 prevents runaway loops if the target never
    // returns 201.
    let max_attempts = req.n * 4 + 10_000;
    let store = state.store.clone();
    let client = state.client.clone();

    tokio::spawn(async move {
        let start = Instant::now();
        let result = run_load(spec, client, max_attempts).await;
        let duration_ms = start.elapsed().as_millis() as i64;
        if let Err(e) = store
            .complete(
                job_id,
                result.created as i64,
                result.conflicts as i64,
                result.attempts as i64,
                duration_ms,
            )
            .await
        {
            tracing::error!("store.complete failed for {job_id}: {e}");
            // Best-effort: record the failure so polling clients see an error.
            let _ = store.fail(job_id, e.to_string()).await;
        }
    });

    StatusCode::ACCEPTED
}

async fn list_runs(State(state): State<AppState>) -> Result<Json<Vec<Job>>, StatusCode> {
    state.store.list().await.map(Json).map_err(|e| {
        tracing::error!("list_runs failed: {e}");
        StatusCode::INTERNAL_SERVER_ERROR
    })
}

async fn get_run(
    State(state): State<AppState>,
    Path(job_id): Path<Uuid>,
) -> Result<Json<Job>, StatusCode> {
    match state.store.get(job_id).await {
        Ok(Some(job)) => Ok(Json(job)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            tracing::error!("get_run failed for {job_id}: {e}");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}
