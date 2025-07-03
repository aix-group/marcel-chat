<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'
import ChatMessage, { type ChatMessageConfig } from '@/components/ChatMessage.vue'
import assistantImage from '@/assets/assistant.svg'
import userImage from '@/assets/user.png'
import { fetchConversation, type ConversationRead } from '@/services/admin'
import LoadingIndicator from '@/components/icons/LoadingIndicator.vue'
import { formatDate } from '@/utils'
import { validateUUID } from '@/utils'
import { APIError } from '@/services/types'
import { useErrorStore } from '@/stores/errorStore'
import ErrorDisplay from '@/components/ErrorDisplay.vue'

const route = useRoute()

const configs: { [key: string]: ChatMessageConfig } = {
  user: {
    name: 'You',
    image: userImage,
    allowEdit: false,
    allowCopy: false,
    allowRating: false,
    showTimestamp: true
  },
  assistant: {
    name: 'Marcel',
    image: assistantImage,
    allowEdit: false,
    allowCopy: true,
    allowRating: true,
    showTimestamp: true
  }
}

const conversation = ref<ConversationRead | null>(null)
const { addError } = useErrorStore()
const router = useRouter()
const isLoading = ref<boolean>(false)

async function load() {
  isLoading.value = true
  try {
    let param = route.params.id
    param = Array.isArray(param) ? param[0] : param
    const id = validateUUID(param)
    const response = await fetchConversation(id)
    conversation.value = response
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'admin-conversation',
      retryAction: () => router.go(0),
      actionLabel: 'Please retry.'
    })
  }
  isLoading.value = false
}

onMounted(() => {
  load()
})
</script>

<template>
  <h2 class="text-2xl text-gray-700 dark:text-white">
    Conversation {{ conversation?.id.slice(0, 8) }}
  </h2>
  <ErrorDisplay scope="admin-conversation" />
  <template v-if="conversation">
    <hr class="h-px my-2 bg-gray-200 border-0 dark:bg-gray-700" />
    <div class="flex flex-col text-gray-400 text-sm">
      <span>Conversation ID: {{ conversation.id }}</span>
      <span>User ID: {{ conversation.user_id }}</span>
      <span>Rating: {{ conversation.rating !== null ? conversation.rating : 'None' }}</span>
      <span
        >Created At:
        {{ formatDate(conversation.created_at) }}
      </span>
    </div>
    <hr class="h-px my-2 bg-gray-200 border-0 dark:bg-gray-700" />
    <div v-if="conversation.messages.length > 0" class="flex flex-col mt-4 mb-3 space-y-3">
      <div :key="index" v-for="(message, index) in conversation.messages">
        <ChatMessage
          class="message"
          :message="message"
          :state="'idle'"
          :config="configs[message['role']]"
          :feedback="message.feedback"
        >
        </ChatMessage>
      </div>
    </div>
  </template>
  <div v-if="isLoading" class="flex items-center space-x-2">
    <LoadingIndicator class="w-6 h-6" />
    <span class="text-gray-700">Loading conversation...</span>
  </div>
</template>
