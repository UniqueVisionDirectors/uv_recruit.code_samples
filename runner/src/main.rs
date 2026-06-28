use runner::api::{app, AppState};
use runner::store::JobStore;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let database_url = std::env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let pool = sqlx::PgPool::connect(&database_url)
        .await
        .expect("failed to connect to database");
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("failed to run migrations");

    let store = JobStore::new(pool);
    let client = reqwest::Client::new();
    let state = AppState { store, client };

    let listener = tokio::net::TcpListener::bind("0.0.0.0:9000").await.unwrap();
    axum::serve(listener, app(state)).await.unwrap();
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use runner::api::healthz_router;
    use tower::ServiceExt;

    // healthz is stateless — no DB needed.
    #[tokio::test]
    async fn healthz_returns_ok() {
        let resp = healthz_router()
            .oneshot(
                Request::builder()
                    .uri("/healthz")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::OK);
    }
}
