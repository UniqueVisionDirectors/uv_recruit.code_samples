<script setup lang="ts">
import { ref } from 'vue'
import { startRun } from '../lib/api'

const emit = defineEmits<{
  launched: []
}>()

// runner は target をベースURLとして使い、サーバ間で `{target}/users` に POST する。
// そのため docker ネットワーク内部の絶対URL（scheme+port）を渡す。
const target = ref('http://app:8000')
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
  <section class="card job-launcher">
    <h2>ジョブ起動</h2>
    <p class="hint">大量のID発行を並列で実行し、衝突回数（conflict_count）を観測します。</p>
    <form class="launch-form" @submit.prevent="launch">
      <label class="field">
        <span>ターゲット</span>
        <select v-model="target" :disabled="loading">
          <option value="http://app:8000">app</option>
          <option value="http://lb:8080">lb</option>
        </select>
      </label>
      <label class="field">
        <span>N（件数）</span>
        <input v-model.number="n" type="number" min="1" :disabled="loading" />
      </label>
      <label class="field">
        <span>並列度</span>
        <select v-model.number="concurrency" :disabled="loading">
          <option :value="1">1</option>
          <option :value="100">100</option>
          <option :value="1000">1000</option>
        </select>
      </label>
      <button class="btn btn--primary" type="submit" :disabled="loading">
        {{ loading ? '起動中…' : '起動' }}
      </button>
    </form>
    <p v-if="error" class="error-msg" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.hint {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: var(--space-4);
}

.launch-form {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  flex-wrap: wrap;
}

.launch-form .field {
  flex: 1 1 140px;
}

.error-msg {
  margin-top: var(--space-3);
}
</style>
