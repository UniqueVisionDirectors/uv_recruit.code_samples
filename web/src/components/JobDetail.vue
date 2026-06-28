<script setup lang="ts">
import type { RunJob } from '../lib/api'

defineProps<{
  job: RunJob | null
}>()
</script>

<template>
  <section class="job-detail">
    <h2>ジョブ詳細</h2>
    <p v-if="!job">ジョブを選択してください</p>
    <dl v-else>
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
  </section>
</template>
