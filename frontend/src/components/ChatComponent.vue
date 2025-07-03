<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'

import {
  chat,
  type ChatRequest,
  postConversationRating,
  postMessageFeedback,
  type ChatResponseChunk
} from '../services/chat'
import MessageInput from './MessageInput.vue'
import RatingPrompt from './RatingPrompt.vue'
import NotificationMessage from './NotificationMessage.vue'
import ChatMessage, { type ChatMessageConfig } from './ChatMessage.vue'
import assistantImage from '../assets/assistant.svg'
import userImage from '../assets/user.png'
import { useConversationStore, type Message, type MessageFeedback } from '@/stores/chatStore'
import { storeToRefs } from 'pinia'
import { useNotification } from '@/composables/notification'
import { useConsentStore } from '@/stores/consentStore'
import { useErrorStore } from '@/stores/errorStore'
import { APIError } from '@/services/types'
import ErrorDisplay from '@/components/ErrorDisplay.vue'
import ArrowDownIcon from '@/components/icons/ArrowDownIcon.vue'
import { useRouter } from 'vue-router'
import ConsentDialog from '@/components/ConsentDialog.vue'

const emit = defineEmits<{
  'conversation-started': [id?: string]
  'conversation-updated': [id?: string]
}>()

const { showConsentDialog } = storeToRefs(useConsentStore())
const { conversation } = storeToRefs(useConversationStore())
const router = useRouter()
const { addError, clearErrors } = useErrorStore()

const configs: { [key: string]: ChatMessageConfig } = {
  user: {
    name: 'You',
    image: userImage,
    allowEdit: false,
    allowCopy: false,
    allowRating: false,
    showTimestamp: false
  },
  assistant: {
    name: 'Marcel',
    image: assistantImage,
    allowEdit: false,
    allowCopy: true,
    allowRating: true,
    showTimestamp: false
  }
}

const chatContainer = ref<HTMLElement | null>(null)

export type ResponseState = 'idle' | 'retrieving' | 'streaming'
const responseState = ref<ResponseState>('idle')
const { notification, notify } = useNotification()
const showScrollButton = ref(false)

let scrollTimeout: number | undefined
function handleScroll() {
  /** Only check scroll after some inactivity (i.e debounce). */
  clearTimeout(scrollTimeout)
  scrollTimeout = setTimeout(checkViewScrollable, 50)
}

const checkViewScrollable = () => {
  const el = chatContainer.value
  if (!el) return
  const outsideOfView = el.scrollTop + el.clientHeight < el.scrollHeight - 10
  showScrollButton.value = outsideOfView && conversation.value.messages.length > 0
}

const scrollToBottom = () => {
  const el = chatContainer.value
  if (el) {
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }
}

function scrollToNewMessage(behavior: ScrollBehavior | undefined) {
  nextTick(() => {
    if (chatContainer.value) {
      const lastMessage = chatContainer.value.querySelector('.message:last-child')
      if (lastMessage) {
        lastMessage.scrollIntoView({ behavior: behavior, block: 'start' })
      }
    }
  })
}

watch(conversation, () => {
  // When selecting a new conversation, check for scroll immediately.
  nextTick(() => {
    checkViewScrollable()
  })
})

function stopGeneration() {
  // TODO: interrupt ongoing generation
}

const showRatingPrompt = computed(() => {
  /**
   * Show rating prompt if the following conditions are met:
   * - At least 6 messages (i.e., 3 user-assistant turns)
   * - Conversation does not already have a rating
   * - Last message was sent within the 60 minutes
   * - Finished streaming of current response
   */
  const { messages, rating } = conversation.value
  if (!messages.length) return false
  const lastMessage = messages[messages.length - 1]
  const lastMessageCreatedAt = (
    lastMessage.created_at ? new Date(lastMessage.created_at) : new Date()
  ).getTime()

  return (
    messages.length >= 6 &&
    !rating &&
    Date.now() - lastMessageCreatedAt < 60 * 60 * 1000 &&
    responseState.value == 'idle'
  )
})

function getMessageState(index: number, message: Message): ResponseState {
  if (index === conversation.value.messages.length - 1 && message.role === 'assistant') {
    return responseState.value
  } else {
    return 'idle'
  }
}

async function sendMessage(message: string) {
  conversation.value.messages.push({
    content: message,
    role: 'user',
    sources: []
  })

  // placeholder assistant response
  conversation.value.messages.push({
    content: '',
    role: 'assistant',
    sources: []
  })

  const userMessage = conversation.value.messages[conversation.value.messages.length - 2]
  const assistantMessage = conversation.value.messages[conversation.value.messages.length - 1]
  responseState.value = 'retrieving'
  scrollToNewMessage('smooth')

  try {
    const request: ChatRequest = {
      conversation_id: conversation.value.id,
      messages: conversation.value.messages
        .slice(0, -1)
        .map(({ role, content }) => ({ role, content }))
    }

    let chunksReceived = 0
    await chat(request, (chunk: ChatResponseChunk) => {
      const { conversation_id, user_message, assistant_message, content, non_answer } = chunk
      if (conversation_id) {
        conversation.value.id = conversation_id
      }

      if (user_message) {
        userMessage.id = user_message.id
        userMessage.created_at = user_message.created_at
      }

      if (assistant_message) {
        assistantMessage.id = assistant_message.id
        assistantMessage.created_at = assistant_message.created_at
        assistantMessage.sources = assistant_message.sources
      }

      if (non_answer) {
        assistantMessage.non_answer = non_answer
      }

      if (content?.length) {
        assistantMessage.content += chunk.content
        responseState.value = 'streaming'
      }

      chunksReceived += 1
      if (chunksReceived % 10 == 0) {
        checkViewScrollable()
      }
    })

    emit('conversation-updated', conversation.value.id)
    if (conversation.value.messages.length == 2) {
      emit('conversation-started', conversation.value.id)
    }
  } catch (err) {
    // Drop the agent message placeholder because it failed.
    conversation.value.messages.pop()

    async function retryInNewConversation() {
      /** Just start a fresh conversation and send user message there */
      clearErrors('chat')
      conversation.value = {
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: []
      }
      router.replace({ name: 'home' })
      sendMessage(message)
    }

    async function retryInCurrentConversation() {
      /** Drop the current user message and resend it. */
      clearErrors('chat')
      conversation.value.messages.pop()
      sendMessage(message)
    }

    let retryAction = retryInCurrentConversation
    if (err instanceof APIError && err.status == 404) {
      retryAction = retryInNewConversation
    }

    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'chat',
      retryAction: retryAction,
      actionLabel: 'Retry.'
    })
  } finally {
    responseState.value = 'idle'
  }
}

async function rateMessage(feedback: MessageFeedback, message: Message) {
  if (message.id == null) {
    return
  }

  try {
    await postMessageFeedback({
      message_id: message.id,
      feedback: feedback
    })
    message.feedback = feedback
  } catch (error) {
    console.error('Failed to submit feedback:', error)
  }
}

async function rateConversation(rating: number) {
  if (conversation.value.id == null) {
    return
  }
  await postConversationRating({ conversation_id: conversation.value.id, rating: rating })
  conversation.value.rating = rating
  notify('Your feedback has been submitted successfully!', 'success')
}
</script>

<template>
  <div
    ref="chatContainer"
    class="flex-1 dark:[color-scheme:dark] overflow-y-auto"
    @scroll="handleScroll"
  >
    <ConsentDialog v-if="showConsentDialog" />

    <div v-if="conversation.messages.length > 0" class="flex flex-col mt-4 mb-3 space-y-3">
      <ChatMessage
        v-for="(message, index) in conversation.messages"
        :key="index"
        class="message"
        :message="message"
        :state="getMessageState(index, message)"
        :config="configs[message['role']]"
        @rate-message="(feedback) => rateMessage(feedback, message)"
      />
    </div>

    <ErrorDisplay scope="chat" />
    <RatingPrompt v-if="showRatingPrompt" @submit="rateConversation" />
  </div>
  <NotificationMessage
    data-testid="chatComponentNotification"
    v-if="notification"
    :message="notification.message"
    :kind="notification.kind"
  />
  <MessageInput
    :generating="responseState != 'idle'"
    @send-message="sendMessage"
    @stop-generation="stopGeneration"
  />
  <div class="mt-1.5 mb-1.5 text-center text-xs text-gray-500 dark:text-gray-400">
    Marcel can make mistakes. Double-check important info. See
    <RouterLink class="font-medium underline hover:no-underline" :to="{ name: 'privacy' }"
      >privacy</RouterLink
    >
    and
    <a
      class="font-medium underline hover:no-underline"
      href="https://www.mathematik.uni-marburg.de/legal/datenschutz.html#english"
      >legal</a
    >
    terms.
  </div>

  <!-- Scroll to bottom button -->
  <div class="absolute left-1/2 transform -translate-x-1/2 bottom-24" v-if="showScrollButton">
    <button
      class="transition rounded-full p-1.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 hover:dark:bg-gray-600 text-gray-800 dark:text-gray-200"
      @click="scrollToBottom"
    >
      <ArrowDownIcon class="w-5 h-5" />
    </button>
  </div>
</template>
