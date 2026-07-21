use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Job {
    pub job_id: Uuid,
    pub target: String,
    pub n: i64,
    pub concurrency: i64,
    pub status: String,
    pub created_count: i64,
    pub conflict_count: i64,
    pub attempt_count: i64,
    pub started_at: DateTime<Utc>,
    pub finished_at: Option<DateTime<Utc>>,
    pub duration_ms: Option<i64>,
    pub error: Option<String>,
}

#[derive(Clone)]
pub struct JobStore {
    pool: PgPool,
}

impl JobStore {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn insert_running(&self, job: Job) -> sqlx::Result<()> {
        sqlx::query(
            "INSERT INTO jobs \
             (job_id, target, n, concurrency, status, \
              created_count, conflict_count, attempt_count, \
              started_at, finished_at, duration_ms, error) \
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
        )
        .bind(job.job_id)
        .bind(job.target)
        .bind(job.n)
        .bind(job.concurrency)
        .bind(job.status)
        .bind(job.created_count)
        .bind(job.conflict_count)
        .bind(job.attempt_count)
        .bind(job.started_at)
        .bind(job.finished_at)
        .bind(job.duration_ms)
        .bind(job.error)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    pub async fn complete(
        &self,
        job_id: Uuid,
        created_count: i64,
        conflict_count: i64,
        attempt_count: i64,
        duration_ms: i64,
    ) -> sqlx::Result<()> {
        sqlx::query(
            "UPDATE jobs \
             SET status = 'completed', \
                 created_count = $1, \
                 conflict_count = $2, \
                 attempt_count = $3, \
                 duration_ms = $4, \
                 finished_at = now() \
             WHERE job_id = $5",
        )
        .bind(created_count)
        .bind(conflict_count)
        .bind(attempt_count)
        .bind(duration_ms)
        .bind(job_id)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    pub async fn fail(&self, job_id: Uuid, error: String) -> sqlx::Result<()> {
        sqlx::query(
            "UPDATE jobs \
             SET status = 'failed', \
                 error = $1, \
                 finished_at = now() \
             WHERE job_id = $2",
        )
        .bind(error)
        .bind(job_id)
        .execute(&self.pool)
        .await?;
        Ok(())
    }

    pub async fn get(&self, job_id: Uuid) -> sqlx::Result<Option<Job>> {
        sqlx::query_as::<_, Job>(
            "SELECT job_id, target, n, concurrency, status, \
                    created_count, conflict_count, attempt_count, \
                    started_at, finished_at, duration_ms, error \
             FROM jobs WHERE job_id = $1",
        )
        .bind(job_id)
        .fetch_optional(&self.pool)
        .await
    }

    pub async fn list(&self) -> sqlx::Result<Vec<Job>> {
        sqlx::query_as::<_, Job>(
            "SELECT job_id, target, n, concurrency, status, \
                    created_count, conflict_count, attempt_count, \
                    started_at, finished_at, duration_ms, error \
             FROM jobs ORDER BY started_at DESC",
        )
        .fetch_all(&self.pool)
        .await
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sqlx::PgPool;

    #[sqlx::test(migrations = "./migrations")]
    async fn test_insert_running_get_complete_state_transition(pool: PgPool) -> sqlx::Result<()> {
        let store = JobStore::new(pool);

        let job = Job {
            job_id: Uuid::new_v4(),
            target: "http://example.com/users".to_string(),
            n: 100,
            concurrency: 10,
            status: "running".to_string(),
            created_count: 0,
            conflict_count: 0,
            attempt_count: 0,
            started_at: Utc::now(),
            finished_at: None,
            duration_ms: None,
            error: None,
        };
        let job_id = job.job_id;

        // insert_running
        store.insert_running(job).await?;

        // get → status == "running"
        let fetched = store
            .get(job_id)
            .await?
            .expect("job should exist after insert");
        assert_eq!(fetched.status, "running");
        assert_eq!(fetched.target, "http://example.com/users");
        assert_eq!(fetched.n, 100);
        assert!(fetched.finished_at.is_none());
        assert!(fetched.duration_ms.is_none());

        // complete
        store.complete(job_id, 90, 5, 95, 2000).await?;

        // get → status == "completed", counts updated
        let completed = store
            .get(job_id)
            .await?
            .expect("job should exist after complete");
        assert_eq!(completed.status, "completed");
        assert_eq!(completed.created_count, 90);
        assert_eq!(completed.conflict_count, 5);
        assert_eq!(completed.attempt_count, 95);
        assert_eq!(completed.duration_ms, Some(2000));
        assert!(completed.finished_at.is_some());

        Ok(())
    }

    #[sqlx::test(migrations = "./migrations")]
    async fn test_fail_state_transition(pool: PgPool) -> sqlx::Result<()> {
        let store = JobStore::new(pool);

        let job = Job {
            job_id: Uuid::new_v4(),
            target: "http://example.com/users".to_string(),
            n: 50,
            concurrency: 5,
            status: "running".to_string(),
            created_count: 0,
            conflict_count: 0,
            attempt_count: 0,
            started_at: Utc::now(),
            finished_at: None,
            duration_ms: None,
            error: None,
        };
        let job_id = job.job_id;

        store.insert_running(job).await?;
        store.fail(job_id, "connection refused".to_string()).await?;

        let failed = store
            .get(job_id)
            .await?
            .expect("job should exist after fail");
        assert_eq!(failed.status, "failed");
        assert_eq!(failed.error.as_deref(), Some("connection refused"));
        assert!(failed.finished_at.is_some());

        Ok(())
    }

    #[sqlx::test(migrations = "./migrations")]
    async fn test_list(pool: PgPool) -> sqlx::Result<()> {
        let store = JobStore::new(pool);

        let jobs_before = store.list().await?;
        assert_eq!(jobs_before.len(), 0);

        for i in 0..3 {
            store
                .insert_running(Job {
                    job_id: Uuid::new_v4(),
                    target: format!("http://example.com/{}", i),
                    n: 10,
                    concurrency: 1,
                    status: "running".to_string(),
                    created_count: 0,
                    conflict_count: 0,
                    attempt_count: 0,
                    started_at: Utc::now(),
                    finished_at: None,
                    duration_ms: None,
                    error: None,
                })
                .await?;
        }

        let jobs_after = store.list().await?;
        assert_eq!(jobs_after.len(), 3);

        Ok(())
    }
}
