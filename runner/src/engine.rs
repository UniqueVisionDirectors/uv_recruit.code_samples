use serde_json::json;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tokio::sync::mpsc;

pub struct RunSpec {
    pub target: String,
    pub n: u64,
    pub concurrency: usize,
}

pub struct RunResult {
    pub created: u64,
    pub conflicts: u64,
    pub attempts: u64,
}

enum Outcome {
    Created,
    Conflict,
    Other,
}

async fn post_one(client: &reqwest::Client, target: &str) -> Outcome {
    let url = format!("{}/users", target);
    // app の `POST /users` は `{"name": ...}` を必須とする。ボディ無しだと 422 に
    // なるため、負荷用の固定名を送る（id はサーバ側で発行され、衝突観測が目的なので
    // name の一意性は不要）。
    match client
        .post(&url)
        .json(&json!({"name": "load"}))
        .send()
        .await
    {
        Ok(resp) => match resp.status().as_u16() {
            201 | 200 => Outcome::Created,
            409 => Outcome::Conflict,
            _ => Outcome::Other,
        },
        Err(_) => Outcome::Other,
    }
}

/// Drive `spec.concurrency` concurrent tasks that POST to `{spec.target}/users`,
/// routing each outcome through a single mpsc aggregator.
///
/// Stops when `created >= spec.n` OR `attempts >= max_attempts`.
///
/// Anti-deadlock guarantee: after the aggregator breaks out of its receive
/// loop it drops `rx`, causing every blocked or future `tx.send().await` in
/// the load tasks to return `Err`. Tasks observe the error and exit their
/// loops, so the subsequent `h.await` joins always terminate.
pub async fn run_load(spec: RunSpec, client: reqwest::Client, max_attempts: u64) -> RunResult {
    // Channel capacity: each task can buffer up to 2 in-flight outcomes before
    // back-pressure stalls it, which is enough to keep concurrency saturated
    // without a huge unbounded queue.
    let (tx, mut rx) = mpsc::channel::<Outcome>(spec.concurrency * 2);
    let stop = Arc::new(AtomicBool::new(false));

    let mut handles = Vec::new();
    for _ in 0..spec.concurrency {
        let tx = tx.clone();
        let stop = stop.clone();
        let client = client.clone();
        let target = spec.target.clone();
        handles.push(tokio::spawn(async move {
            while !stop.load(Ordering::Relaxed) {
                let outcome = post_one(&client, &target).await;
                // If the receiver has been dropped, exit immediately.
                if tx.send(outcome).await.is_err() {
                    break;
                }
            }
        }));
    }
    // Drop the original sender so the channel closes when all task clones exit.
    drop(tx);

    let (mut created, mut conflicts, mut attempts) = (0u64, 0u64, 0u64);
    while let Some(o) = rx.recv().await {
        attempts += 1;
        match o {
            Outcome::Created => created += 1,
            Outcome::Conflict => conflicts += 1,
            Outcome::Other => {}
        }
        if created >= spec.n || attempts >= max_attempts {
            stop.store(true, Ordering::Relaxed);
            break;
        }
    }
    // Drop rx NOW so any task blocked on tx.send() gets Err and exits.
    // Without this, full-channel senders would block indefinitely during join.
    drop(rx);

    for h in handles {
        let _ = h.await;
    }

    RunResult {
        created,
        conflicts,
        attempts,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use httpmock::prelude::*;

    /// Mock always returns 201. Engine should stop exactly at n=50 created.
    ///
    /// The matcher also requires the `{"name": ...}` JSON body: the app rejects
    /// body-less POSTs with 422, so this guards against regressing back to an
    /// empty request that would never create a user.
    #[tokio::test]
    async fn run_load_all_created() {
        let server = MockServer::start_async().await;
        server
            .mock_async(|when, then| {
                when.method(POST)
                    .path("/users")
                    .json_body(json!({"name": "load"}));
                then.status(201);
            })
            .await;

        let client = reqwest::Client::new();
        let spec = RunSpec {
            target: server.base_url(),
            n: 50,
            concurrency: 8,
        };
        let result = run_load(spec, client, 1000).await;
        assert_eq!(result.created, 50);
        assert!(result.attempts >= 50);
    }

    /// Every 3rd request returns 409, rest return 201. Engine should stop at
    /// n=20 created, with conflicts > 0 (because 409s were encountered).
    #[tokio::test]
    async fn run_load_mixed_created_and_conflicts() {
        use axum::http::StatusCode;
        use std::sync::atomic::AtomicUsize;

        let counter = Arc::new(AtomicUsize::new(0));
        let counter_clone = counter.clone();

        let app = axum::Router::new().route(
            "/users",
            axum::routing::post(move || {
                let count = counter_clone.fetch_add(1, Ordering::Relaxed);
                async move {
                    if count % 3 == 0 {
                        StatusCode::CONFLICT
                    } else {
                        StatusCode::CREATED
                    }
                }
            }),
        );

        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        tokio::spawn(async move {
            axum::serve(listener, app).await.unwrap();
        });

        let client = reqwest::Client::new();
        let spec = RunSpec {
            target: format!("http://{}", addr),
            n: 20,
            concurrency: 4,
        };
        let result = run_load(spec, client, 1000).await;
        assert_eq!(result.created, 20);
        assert!(result.conflicts > 0, "expected some 409 conflicts");
    }
}
