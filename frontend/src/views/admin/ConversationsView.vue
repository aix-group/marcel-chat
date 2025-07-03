<template>
  <DataTable
    :value="tableData"
    :totalRecords="totalRecords"
    paginator
    lazy
    :rows="size"
    :rowsPerPageOptions="[10, 20, 50, 100]"
    size="small"
    @page="pageCallback"
  >
    <Column field="id" header="Conversation">
      <template #body="slotProps">
        <!-- show the first part of UUID4 -->
        {{ slotProps.data.id.slice(0, 8) }}
      </template>
    </Column>
    <Column field="user_id" header="User"></Column>
    <Column field="n_messages" header="Messages"></Column>
    <Column field="rating" header="Rating"></Column>
    <Column field="created_at" header="Created At">
      <template #body="slotProps">
        {{ formatDate(slotProps.data.created_at) }}
      </template>
    </Column>
    <Column field="updated_at" header="Updated At">
      <template #body="slotProps">
        {{ formatDate(slotProps.data.updated_at) }}
      </template>
    </Column>
    <Column header="View">
      <template #body="slotProps">
        <RouterLink
          class="text-blue-600 dark:text-blue-400"
          :to="{ name: 'conversation', params: { id: slotProps.data.id } }"
          >View</RouterLink
        >
      </template>
    </Column>
  </DataTable>
  <ErrorDisplay scope="admin-conversations" />
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { formatDate } from '@/utils'
import DataTable from 'primevue/datatable'
import type { DataTablePageEvent } from 'primevue/datatable'
import Column from 'primevue/column'
import { ref, onMounted } from 'vue'
import { fetchConversations, type ConversationListItem } from '@/services/admin.ts'
import { APIError } from '@/services/types'
import { useErrorStore } from '@/stores/errorStore'
import ErrorDisplay from '@/components/ErrorDisplay.vue'

const size = ref<number>(10)
const totalRecords = ref<number>(0)
const tableData = ref<Array<ConversationListItem> | null>(null)
const { addError } = useErrorStore()
const router = useRouter()

async function loadPage(page: number, size: number) {
  try {
    const response = await fetchConversations(page, size)
    totalRecords.value = response.total
    tableData.value = response.conversations
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'admin-conversations',
      retryAction: () => router.go(0),
      actionLabel: 'Please retry.'
    })
  }
}

function pageCallback(event: DataTablePageEvent) {
  loadPage(event.page, event.rows)
}

onMounted(() => {
  loadPage(0, size.value)
})
</script>
