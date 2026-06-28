use runner::api::{app, AppState};
use runner::store::JobStore;
use sqlx::PgPool;

#[sqlx::test(migrations = "./migrations")]
async fn post_runs_returns_202_and_job_completes(pool: PgPool) {
    // Stand up a mock HTTP target that always returns 201.
    let server = httpmock::MockServer::start_async().await;
    server
        .mock_async(|when, then| {
            when.method(httpmock::Method::POST).path("/users");
            then.status(201);
        })
        .await;

    let store = JobStore::new(pool);
    let client = reqwest::Client::new();
    let state = AppState { store, client };
    let the_app = app(state);

    // Bind a random port so multiple test runs don't collide.
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    tokio::spawn(async move {
        axum::serve(listener, the_app).await.unwrap();
    });

    let http = reqwest::Client::new();
    let job_id = uuid::Uuid::new_v4();
    let target = server.base_url();
    let n: u64 = 5;

    // POST /runs must return 202 immediately.
    let resp = http
        .post(format!("http://{addr}/runs"))
        .json(&serde_json::json!({
            "job_id": job_id,
            "target": target,
            "n": n,
            "concurrency": 2
        }))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status().as_u16(), 202, "expected 202 Accepted");

    // Poll GET /runs/{job_id} until status == "completed" (max ~6 s).
    let mut final_job: Option<serde_json::Value> = None;
    for _ in 0..30 {
        tokio::time::sleep(std::time::Duration::from_millis(200)).await;
        let r = http
            .get(format!("http://{addr}/runs/{job_id}"))
            .send()
            .await
            .unwrap();
        assert_eq!(
            r.status().as_u16(),
            200,
            "GET /runs/{job_id} must return 200"
        );
        let body: serde_json::Value = r.json().await.unwrap();
        if body["status"] == "completed" {
            final_job = Some(body);
            break;
        }
    }

    let job = final_job.expect("job should have completed within 6 s");
    assert_eq!(job["status"], "completed");
    assert_eq!(
        job["created_count"].as_i64().unwrap(),
        n as i64,
        "created_count must equal n"
    );
}

#[sqlx::test(migrations = "./migrations")]
async fn get_runs_returns_list(pool: PgPool) {
    let store = JobStore::new(pool);
    let client = reqwest::Client::new();
    let state = AppState { store, client };
    let the_app = app(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    tokio::spawn(async move {
        axum::serve(listener, the_app).await.unwrap();
    });

    let http = reqwest::Client::new();
    let resp = http
        .get(format!("http://{addr}/runs"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status().as_u16(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert!(body.is_array(), "GET /runs must return a JSON array");
}

#[sqlx::test(migrations = "./migrations")]
async fn get_run_unknown_id_returns_404(pool: PgPool) {
    let store = JobStore::new(pool);
    let client = reqwest::Client::new();
    let state = AppState { store, client };
    let the_app = app(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    tokio::spawn(async move {
        axum::serve(listener, the_app).await.unwrap();
    });

    let http = reqwest::Client::new();
    let missing_id = uuid::Uuid::new_v4();
    let resp = http
        .get(format!("http://{addr}/runs/{missing_id}"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status().as_u16(), 404);
}
