<script setup lang="ts">
import { ref } from 'vue'
import { createUser } from '../lib/api'
import type { UserRead } from '../lib/api'
import { validateId } from '../lib/validate'

const emit = defineEmits<{
  issued: [user: UserRead]
}>()

const name = ref('')
const error = ref('')
const loading = ref(false)
const lastIssued = ref<UserRead | null>(null)

async function issue(): Promise<void> {
  if (!name.value.trim()) return
  error.value = ''
  loading.value = true
  try {
    const user = await createUser(name.value.trim())
    lastIssued.value = user
    emit('issued', user)
    name.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'エラーが発生しました'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="card issue-panel">
    <h2>単発発行</h2>
    <p class="hint">名前を入力してIDを1件発行し、要件（10文字・base62）を確認します。</p>
    <form class="issue-form" @submit.prevent="issue">
      <label class="field">
        <span>名前</span>
        <input v-model="name" type="text" placeholder="例: 山田太郎" :disabled="loading" />
      </label>
      <button class="btn btn--primary" type="submit" :disabled="loading || !name.trim()">
        {{ loading ? '発行中…' : '発行' }}
      </button>
    </form>
    <p v-if="error" class="error-msg" role="alert">{{ error }}</p>
    <div v-if="lastIssued" class="result">
      <span class="result-label">発行されたID</span>
      <code>{{ lastIssued.id }}</code>
      <span class="badge" :class="validateId(lastIssued.id).len ? 'badge--ok' : 'badge--ng'">
        {{ validateId(lastIssued.id).len ? '✓ 10文字' : '✕ 文字数' }}
      </span>
      <span class="badge" :class="validateId(lastIssued.id).charset ? 'badge--ok' : 'badge--ng'">
        {{ validateId(lastIssued.id).charset ? '✓ base62' : '✕ base62' }}
      </span>
    </div>
  </section>
</template>

<style scoped>
.hint {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: var(--space-4);
}

.issue-form {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  flex-wrap: wrap;
}

.issue-form .field {
  flex: 1 1 220px;
}

.error-msg {
  margin-top: var(--space-3);
}

.result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.result-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
}
</style>
