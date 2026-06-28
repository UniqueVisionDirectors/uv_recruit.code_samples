<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import IssueView from './components/IssueView.vue'
import JobsView from './components/JobsView.vue'
import { listUsers, listRuns } from './lib/api'
import type { UserRead, RunJob } from './lib/api'

type View = 'issue' | 'jobs'
const activeView = ref<View>('issue')

const users = ref<UserRead[]>([])
const fetchError = ref('')

async function refresh(): Promise<void> {
  fetchError.value = ''
  try {
    users.value = await listUsers(100, 0)
  } catch (e) {
    fetchError.value = e instanceof Error ? e.message : 'フェッチエラー'
  }
}

function onIssued(): void {
  void refresh()
}

const jobs = ref<RunJob[]>([])
const jobsError = ref('')

// runner はジョブを非同期実行し、完了/失敗時にだけ jobs を更新する。running が残る間だけ
// 一覧をポーリングし、全ジョブが終了したら止める（無駄な定常ポーリングを避ける）。
let jobsTimerId: ReturnType<typeof setInterval> | null = null

function anyRunning(): boolean {
  return jobs.value.some((j) => j.status === 'running')
}

async function refreshJobs(): Promise<void> {
  jobsError.value = ''
  try {
    jobs.value = await listRuns()
  } catch (e) {
    jobsError.value = e instanceof Error ? e.message : 'フェッチエラー'
  }
}

function stopJobsPolling(): void {
  if (jobsTimerId !== null) {
    clearInterval(jobsTimerId)
    jobsTimerId = null
  }
}

function ensureJobsPolling(): void {
  if (jobsTimerId !== null || !anyRunning()) return
  jobsTimerId = setInterval(() => {
    void (async () => {
      await refreshJobs()
      if (!anyRunning()) stopJobsPolling()
    })()
  }, 1500)
}

function onLaunched(): void {
  void (async () => {
    await refreshJobs()
    ensureJobsPolling()
  })()
}

onMounted(() => {
  void refresh()
  void (async () => {
    await refreshJobs()
    ensureJobsPolling()
  })()
})

onUnmounted(() => {
  stopJobsPolling()
})
</script>

<template>
  <header class="app-header">
    <h1>ユーザーID発行 API デモ</h1>
    <p class="subtitle">
      IDを発行して要件（10文字・base62・発行順ソート整合）を確認し、負荷ジョブで衝突を観測します。
    </p>
  </header>

  <nav class="tabs" aria-label="表示切替">
    <button
      class="tab"
      type="button"
      :class="{ 'tab--active': activeView === 'issue' }"
      :aria-pressed="activeView === 'issue'"
      @click="activeView = 'issue'"
    >
      単発発行
    </button>
    <button
      class="tab"
      type="button"
      :class="{ 'tab--active': activeView === 'jobs' }"
      :aria-pressed="activeView === 'jobs'"
      @click="activeView = 'jobs'"
    >
      負荷ジョブ
    </button>
  </nav>

  <main>
    <IssueView
      v-if="activeView === 'issue'"
      :users="users"
      :fetch-error="fetchError"
      @issued="onIssued"
    />
    <JobsView
      v-else
      :jobs="jobs"
      :jobs-error="jobsError"
      @launched="onLaunched"
    />
  </main>
</template>

<style scoped>
.app-header {
  margin-bottom: var(--space-5);
}

.app-header h1 {
  font-size: 1.75rem;
  letter-spacing: -0.02em;
  margin: 0 0 var(--space-2);
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  border-bottom: 1px solid var(--border);
}

.tab {
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  background: none;
  border: none;
  color: var(--text-muted);
  padding: var(--space-3) var(--space-4);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.tab:hover {
  color: var(--text-h);
}

.tab:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
</style>
