<script setup lang="ts">
import { ref, computed } from 'vue'
import JobLauncher from './JobLauncher.vue'
import JobList from './JobList.vue'
import JobDetail from './JobDetail.vue'
import type { RunJob } from '../lib/api'

const props = defineProps<{
  jobs: RunJob[]
  jobsError: string
}>()

const emit = defineEmits<{
  launched: []
}>()

// 選択は純粋に表示の関心事なので JobsView がローカルに所有し、App のポーリングと直交させる。
// 詳細は GET /runs の単一出典（props.jobs）から id 一致で導出するため個別取得しない。
const selectedJobId = ref<string | null>(null)

const selectedJob = computed<RunJob | null>(() =>
  selectedJobId.value === null
    ? null
    : (props.jobs.find((j) => j.job_id === selectedJobId.value) ?? null),
)

function onSelect(jobId: string): void {
  selectedJobId.value = jobId
}

function onBack(): void {
  selectedJobId.value = null
}
</script>

<template>
  <div class="view-stack">
    <JobLauncher @launched="emit('launched')" />
    <p v-if="jobsError" class="error-msg" role="alert">{{ jobsError }}</p>
    <div class="card">
      <JobDetail v-if="selectedJobId !== null" :job="selectedJob" @back="onBack" />
      <JobList v-else :jobs="jobs" @select="onSelect" />
    </div>
  </div>
</template>

<style scoped>
.view-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
</style>
