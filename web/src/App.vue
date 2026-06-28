<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import IssuePanel from './components/IssuePanel.vue'
import UserTable from './components/UserTable.vue'
import JobLauncher from './components/JobLauncher.vue'
import JobList from './components/JobList.vue'
import JobDetail from './components/JobDetail.vue'
import { listUsers, listRuns } from './lib/api'
import type { UserRead, RunJob } from './lib/api'

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
const selectedJobId = ref<string | null>(null)

// 一覧・詳細は GET /runs を唯一の出典とする（UserTable と同じく App がデータを所有し、
// JobList / JobDetail は純表示）。選択中ジョブの詳細は取得済みの一覧から導出するため、
// 個別取得は不要。
const selectedJob = computed<RunJob | null>(() =>
  selectedJobId.value === null
    ? null
    : (jobs.value.find((j) => j.job_id === selectedJobId.value) ?? null),
)

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

function onSelectJob(jobId: string): void {
  selectedJobId.value = jobId
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
  <div id="app-inner">
    <h1>ユーザー管理</h1>
    <IssuePanel @issued="onIssued" />
    <p v-if="fetchError" class="error-msg">{{ fetchError }}</p>
    <UserTable :users="users" />

    <h1>ジョブ管理</h1>
    <JobLauncher @launched="onLaunched" />
    <p v-if="jobsError" class="error-msg">{{ jobsError }}</p>
    <JobList :jobs="jobs" @select="onSelectJob" />
    <JobDetail :job="selectedJob" />
  </div>
</template>
