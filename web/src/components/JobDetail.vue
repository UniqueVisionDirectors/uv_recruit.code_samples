<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { getRun } from '../lib/api'
import type { RunJob } from '../lib/api'

const props = defineProps<{
  jobId: string | null
}>()

const job = ref<RunJob | null>(null)
const error = ref('')
let timerId: ReturnType<typeof setInterval> | null = null

function stopPolling(): void {
  if (timerId !== null) {
    clearInterval(timerId)
    timerId = null
  }
}

async function fetchJob(id: string): Promise<void> {
  try {
    job.value = await getRun(id)
    if (job.value.status !== 'running') {
      stopPolling()
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'エラーが発生しました'
    stopPolling()
  }
}

function startPolling(id: string): void {
  stopPolling()
  void fetchJob(id)
  timerId = setInterval(() => {
    void fetchJob(id)
  }, 1500)
}

watch(
  () => props.jobId,
  (id) => {
    job.value = null
    error.value = ''
    stopPolling()
    if (id !== null) {
      startPolling(id)
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <section class="job-detail">
    <h2>ジョブ詳細</h2>
    <p v-if="!jobId">ジョブを選択してください</p>
    <p v-else-if="error" class="error-msg">{{ error }}</p>
    <template v-else-if="job">
      <dl>
        <dt>status</dt>
        <dd>{{ job.status }}</dd>
        <dt>created_count</dt>
        <dd>{{ job.created_count }}</dd>
        <dt>conflict_count</dt>
        <dd>{{ job.conflict_count }}</dd>
        <dt>attempt_count</dt>
        <dd>{{ job.attempt_count }}</dd>
        <dt>duration_ms</dt>
        <dd>{{ job.duration_ms ?? '—' }}</dd>
      </dl>
    </template>
    <p v-else>読み込み中…</p>
  </section>
</template>
