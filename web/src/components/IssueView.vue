<script setup lang="ts">
import IssuePanel from './IssuePanel.vue'
import UserTable from './UserTable.vue'
import type { UserRead } from '../lib/api'

defineProps<{
  users: UserRead[]
  fetchError: string
}>()

const emit = defineEmits<{
  issued: []
}>()
</script>

<template>
  <div class="view-stack">
    <IssuePanel @issued="emit('issued')" />
    <p v-if="fetchError" class="error-msg" role="alert">{{ fetchError }}</p>
    <UserTable :users="users" />
  </div>
</template>

<style scoped>
.view-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
</style>
