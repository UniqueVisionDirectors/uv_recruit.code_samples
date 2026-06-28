<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  jobs: RunJob[]
}>()

const emit = defineEmits<{
  select: [jobId: string]
}>()
</script>

<template>
  <section class="job-list">
    <h2>ジョブ一覧</h2>
    <table v-if="jobs.length">
      <thead>
        <tr>
          <th>job_id</th>
          <th>target</th>
          <th>N</th>
          <th>並列度</th>
          <th>status</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="job in jobs"
          :key="job.job_id"
          style="cursor: pointer"
          @click="emit('select', job.job_id)"
        >
          <td><code>{{ job.job_id.slice(0, 8) }}</code></td>
          <td>{{ job.target }}</td>
          <td>{{ job.n }}</td>
          <td>{{ job.concurrency }}</td>
          <td>{{ job.status }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>ジョブがありません</p>
  </section>
</template>
