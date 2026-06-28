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
  <section class="card user-table">
    <h2>ユーザー一覧</h2>
    <div class="summary" role="group" aria-label="妥当性集計">
      <span class="badge">合計 {{ summary.total }}</span>
      <span class="badge badge--ok">妥当 {{ summary.valid }}</span>
      <span class="badge" :class="summary.invalid > 0 ? 'badge--ng' : ''">不正 {{ summary.invalid }}</span>
      <span class="badge" :class="summary.sortedOk ? 'badge--ok' : 'badge--ng'">
        ソート整合 {{ summary.sortedOk ? '✓ OK' : '✕ NG' }}
      </span>
    </div>
    <div class="table-wrap">
      <table v-if="rows.length" class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名前</th>
            <th>作成日時</th>
            <th>10文字</th>
            <th>base62</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td><code>{{ row.id }}</code></td>
            <td>{{ row.name }}</td>
            <td class="muted">{{ row.created_at }}</td>
            <td>
              <span class="badge" :class="row.v.len ? 'badge--ok' : 'badge--ng'">{{ row.v.len ? '✓' : '✕' }}</span>
            </td>
            <td>
              <span class="badge" :class="row.v.charset ? 'badge--ok' : 'badge--ng'">{{ row.v.charset ? '✓' : '✕' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">ユーザーがいません。上のフォームから発行してください。</p>
    </div>
  </section>
</template>

<style scoped>
.summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.table-wrap {
  overflow-x: auto;
}

.muted {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.empty {
  color: var(--text-muted);
}
</style>
