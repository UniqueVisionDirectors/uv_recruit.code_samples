<script setup lang="ts">
import { ref, onMounted } from 'vue'
import IssuePanel from './components/IssuePanel.vue'
import UserTable from './components/UserTable.vue'
import { listUsers } from './lib/api'
import type { UserRead } from './lib/api'

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
})

function onIssued(): void {
  void refresh()
}
</script>

<template>
  <div id="app-inner">
    <h1>ユーザー管理</h1>
    <IssuePanel @issued="onIssued" />
    <p v-if="fetchError" class="error-msg">{{ fetchError }}</p>
    <UserTable :users="users" />
  </div>
</template>
