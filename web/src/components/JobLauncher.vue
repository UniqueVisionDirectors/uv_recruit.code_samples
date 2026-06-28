<script setup lang="ts">
import { ref } from 'vue'
import { startRun } from '../lib/api'

const emit = defineEmits<{
  launched: []
}>()

const target = ref<'app' | 'lb'>('app')
const n = ref(1000)
const concurrency = ref(1)
const loading = ref(false)
const error = ref('')

async function launch(): Promise<void> {
  error.value = ''
  loading.value = true
  try {
    await startRun({ target: target.value, n: n.value, concurrency: concurrency.value })
    emit('launched')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="job-launcher">
    <h2>ジョブ起動</h2>
    <form @submit.prevent="launch">
      <label>
        ターゲット
        <select v-model="target" :disabled="loading">
          <option value="app">app</option>
          <option value="lb">lb</option>
        </select>
      </label>
      <label>
        N
        <input v-model.number="n" type="number" min="1" :disabled="loading" />
      </label>
      <label>
        並列度
        <select v-model.number="concurrency" :disabled="loading">
          <option :value="1">1</option>
          <option :value="100">100</option>
          <option :value="1000">1000</option>
        </select>
      </label>
      <button type="submit" :disabled="loading">起動</button>
    </form>
    <p v-if="error" class="error-msg">{{ error }}</p>
  </section>
</template>
