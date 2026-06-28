<script setup lang="ts">
import { ref } from 'vue'
import { createUser } from '../lib/api'
import type { UserRead } from '../lib/api'

const emit = defineEmits<{
  issued: [user: UserRead]
}>()

const name = ref('')
const error = ref('')
const loading = ref(false)

async function issue(): Promise<void> {
  if (!name.value.trim()) return
  error.value = ''
  loading.value = true
  try {
    const user = await createUser(name.value.trim())
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
  <section class="issue-panel">
    <h2>ユーザーID発行</h2>
    <form @submit.prevent="issue">
      <input
        v-model="name"
        type="text"
        placeholder="名前を入力"
        :disabled="loading"
      />
      <button type="submit" :disabled="loading || !name.trim()">発行</button>
    </form>
    <p v-if="error" class="error-msg">{{ error }}</p>
  </section>
</template>
