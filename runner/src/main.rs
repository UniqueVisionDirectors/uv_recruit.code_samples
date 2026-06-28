#[allow(dead_code)]
mod engine;
#[allow(dead_code)]
mod store;

use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

pub fn app() -> Router {
    Router::new().route("/healthz", get(healthz))
}

async fn healthz() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

#[tokio::main]
async fn main() {
    let database_url = std::env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let pool = sqlx::PgPool::connect(&database_url)
        .await
        .expect("failed to connect to database");
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("failed to run migrations");

    let listener = tokio::net::TcpListener::bind("0.0.0.0:9000").await.unwrap();
    axum::serve(listener, app()).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt; // oneshot

    #[tokio::test]
    async fn healthz_returns_ok() {
        let resp = app()
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
