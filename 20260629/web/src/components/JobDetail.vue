<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  job: RunJob | null
}>()

const emit = defineEmits<{
  back: []
}>()

const statusLabel: Record<string, string> = {
  running: '実行中',
  completed: '完了',
  failed: '失敗',
}
</script>

<template>
  <section class="job-detail">
    <div class="detail-head">
      <button class="btn back-btn" type="button" @click="emit('back')">← 一覧へ戻る</button>
      <h2>ジョブ詳細</h2>
    </div>
    <p v-if="!job" class="empty">ジョブを選択してください</p>
    <template v-else>
      <div class="status-row">
        <span class="status" :class="`status--${job.status}`">
          <span v-if="job.status === 'running'" class="spinner" aria-hidden="true"></span>
          <span v-else aria-hidden="true">{{ job.status === 'completed' ? '✓' : job.status === 'failed' ? '✕' : '•' }}</span>
          {{ statusLabel[job.status] ?? job.status }}
        </span>
        <code class="job-id">{{ job.job_id }}</code>
      </div>

      <div
        class="conflict-card"
        :class="job.conflict_count > 0 ? 'conflict-card--warn' : 'conflict-card--zero'"
      >
        <span class="conflict-label">conflict_count（衝突）</span>
        <span class="conflict-value">{{ job.conflict_count }}</span>
        <span class="conflict-note">{{ job.conflict_count > 0 ? '衝突が発生しました' : '衝突なし' }}</span>
      </div>

      <dl class="metrics">
        <div class="metric">
          <dt>created_count</dt>
          <dd>{{ job.created_count }}</dd>
        </div>
        <div class="metric">
          <dt>attempt_count</dt>
          <dd>{{ job.attempt_count }}</dd>
        </div>
        <div class="metric">
          <dt>duration_ms</dt>
          <dd>{{ job.duration_ms ?? '—' }}</dd>
        </div>
        <div class="metric">
          <dt>N / 並列度</dt>
          <dd>{{ job.n }} / {{ job.concurrency }}</dd>
        </div>
      </dl>

      <p v-if="job.error" class="error-msg" role="alert">{{ job.error }}</p>
    </template>
  </section>
</template>

<style scoped>
.detail-head {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.detail-head h2 {
  margin: 0;
}

.back-btn {
  font-size: 0.85rem;
  padding: var(--space-1) var(--space-3);
}

.status-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
}

.job-id {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.conflict-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-5);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: var(--space-4);
}

.conflict-card--zero {
  background: var(--surface);
}

.conflict-card--warn {
  background: var(--warn-bg);
  border-color: var(--warn);
}

.conflict-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
}

.conflict-value {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1;
  color: var(--text-h);
}

.conflict-card--warn .conflict-value {
  color: var(--warn);
}

.conflict-note {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.metric {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
}

.metric dt {
  font-size: 0.8rem;
  font-family: var(--mono);
  color: var(--text-muted);
}

.metric dd {
  margin: 4px 0 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-h);
}

.empty {
  color: var(--text-muted);
}
</style>
