<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

onMounted(() => {
  void refresh()
  void refreshJobs()
})

function onIssued(): void {
  void refresh()
}

const jobs = ref<RunJob[]>([])
const jobsError = ref('')
const selectedJobId = ref<string | null>(null)

async function refreshJobs(): Promise<void> {
  jobsError.value = ''
  try {
    jobs.value = await listRuns()
  } catch (e) {
    jobsError.value = e instanceof Error ? e.message : 'フェッチエラー'
  }
}

function onLaunched(): void {
  void refreshJobs()
}

function onSelectJob(jobId: string): void {
  selectedJobId.value = jobId
}
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
    <JobDetail :job-id="selectedJobId" />
  </div>
</template>
