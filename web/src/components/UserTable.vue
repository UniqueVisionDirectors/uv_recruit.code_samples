<script setup lang="ts">
import { computed } from 'vue'
import type { UserRead } from '../lib/api'
import { validateId, summarize } from '../lib/validate'

const props = defineProps<{
  users: UserRead[]
}>()

const ids = computed(() => props.users.map((u) => u.id))
const summary = computed(() => summarize(ids.value))
const rows = computed(() =>
  props.users.map((u) => ({ ...u, v: validateId(u.id) })),
)
</script>

<template>
  <section class="user-table">
    <h2>ユーザー一覧</h2>
    <div class="summary-bar">
      <span>合計: {{ summary.total }}</span>
      <span>妥当: {{ summary.valid }}</span>
      <span>不正: {{ summary.invalid }}</span>
      <span :class="summary.sortedOk ? 'badge-ok' : 'badge-ng'">
        ソート: {{ summary.sortedOk ? 'OK' : 'NG' }}
      </span>
    </div>
    <table v-if="rows.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>名前</th>
          <th>作成日時</th>
          <th>10桁</th>
          <th>base62</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td><code>{{ row.id }}</code></td>
          <td>{{ row.name }}</td>
          <td>{{ row.created_at }}</td>
          <td>
            <span :class="row.v.len ? 'badge-ok' : 'badge-ng'">
              {{ row.v.len ? '10桁' : '×' }}
            </span>
          </td>
          <td>
            <span :class="row.v.charset ? 'badge-ok' : 'badge-ng'">
              {{ row.v.charset ? 'base62' : '×' }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>ユーザーがいません</p>
  </section>
</template>
