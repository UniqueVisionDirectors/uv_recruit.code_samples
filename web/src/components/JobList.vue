<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  jobs: RunJob[]
}>()

const emit = defineEmits<{
  select: [jobId: string]
}>()

const statusLabel: Record<string, string> = {
  running: '実行中',
  completed: '完了',
  failed: '失敗',
}
</script>

<template>
  <section class="job-list">
    <h2>ジョブ一覧</h2>
    <div class="table-wrap">
      <table v-if="jobs.length" class="table">
        <thead>
          <tr>
            <th>job_id</th>
            <th>target</th>
            <th>N</th>
            <th>並列度</th>
            <th>状態</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="job in jobs"
            :key="job.job_id"
            class="row"
            role="button"
            tabindex="0"
            @click="emit('select', job.job_id)"
            @keydown.enter.prevent="emit('select', job.job_id)"
            @keydown.space.prevent="emit('select', job.job_id)"
          >
            <td><code>{{ job.job_id.slice(0, 8) }}</code></td>
            <td>{{ job.target }}</td>
            <td>{{ job.n }}</td>
            <td>{{ job.concurrency }}</td>
            <td>
              <span class="status" :class="`status--${job.status}`">
                <span v-if="job.status === 'running'" class="spinner" aria-hidden="true"></span>
                <span v-else aria-hidden="true">{{ job.status === 'completed' ? '✓' : job.status === 'failed' ? '✕' : '•' }}</span>
                {{ statusLabel[job.status] ?? job.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">ジョブがありません。上のフォームから起動してください。</p>
    </div>
  </section>
</template>

<style scoped>
.table-wrap {
  overflow-x: auto;
}

.row {
  cursor: pointer;
}

.row:hover {
  background: var(--accent-bg);
}

.row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.empty {
  color: var(--text-muted);
}
</style>
