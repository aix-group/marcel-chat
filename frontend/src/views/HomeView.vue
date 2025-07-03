<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import ChatsSidebar from '../components/ChatsSidebar.vue'
import ChatComponent from '../components/ChatComponent.vue'
import HelpModal from '../components/HelpModal.vue'
import { onMounted } from 'vue'
import { fetchConversation, fetchConversations, hideConversation } from '@/services/chat'
import { useConversationsStore, useConversationStore } from '@/stores/chatStore'
import { storeToRefs } from 'pinia'
import { validateUUID } from '@/utils'
import { startSession } from '@/services/session'
import { APIError } from '@/services/types'
import ErrorDisplay from '@/components/ErrorDisplay.vue'
import { useErrorStore } from '@/stores/errorStore'
import WelcomeMessage from '@/components/WelcomeMessage.vue'
import { useConsentStore } from '@/stores/consentStore'

const router = useRouter()
const route = useRoute()
const { conversation } = storeToRefs(useConversationStore())
const { conversations } = storeToRefs(useConversationsStore())
const consentStore = useConsentStore()
const { showConsentDialog } = storeToRefs(consentStore)
const { addError, clearErrors } = useErrorStore()

onMounted(async () => {
  try {
    await startSession()
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'general',
      retryAction: () => router.go(0),
      actionLabel: 'Please retry.'
    })
  }

  if (route.name === 'chat') {
    const param = route.params['id']
    let conversationId = Array.isArray(param) ? param[0] : param
    conversationId = validateUUID(conversationId)

    try {
      conversation.value = await fetchConversation(conversationId)
    } catch (err) {
      addError({
        title: 'Whoops!',
        message: err instanceof APIError ? err.message : 'Unexpected error.',
        scope: 'general',
        retryAction: async () => {
          clearErrors('general')
          await router.push({ name: 'home' })
        },
        actionLabel: 'Go back.'
      })
    }
  }

  try {
    conversations.value = await fetchConversations()
  } catch (err) {
    addError({
      title: 'Whoops!',
      message: err instanceof APIError ? err.message : 'Unexpected error.',
      scope: 'conversation-list',
      retryAction: () => router.go(0),
      actionLabel: 'Please retry.'
    })
  }
})

async function onCreateConversation() {
  /**
   * Starts a blank conversation.
   */
  conversation.value = {
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages: []
  }
  router.replace({ name: 'home' })
  consentStore.dismissConsentDialog()
}

async function onLoadConversation(id?: string) {
  /**
   * Loads an existing conversation. If a user tries to load the current one, this is a no-op.
   */
  if (!id || id == conversation.value.id) return
  conversation.value = await fetchConversation(id)
  router.replace({ name: 'chat', params: { id } })
}

async function onHideConversation(id?: string) {
  /**
   * Hides a conversation from the list of conversations and starts a new conversation if the current is hidden.
   */
  if (!id) return
  if (conversation.value.id == id) {
    onCreateConversation()
  }
  const index = conversations.value.findIndex((conversation) => conversation.id == id)
  if (index !== -1) {
    conversations.value.splice(index, 1)
  }
  await hideConversation(id)
}

async function onConversationStarted(id?: string) {
  /**
   * When a new conversation is started (i.e., a user message + first assistant response), we update the url to represent the conversation ID and refresh the conversation list.
   */
  if (!id) return
  router.replace({ name: 'chat', params: { id } })
  conversations.value = await fetchConversations()
}

async function onConversationUpdated(id?: string) {
  /**
   * When a new message is added to a conversation, we refresh the updated_at flag such that we can show the most recent conversations first. Note: we could also call fetchConversations() to get the latest data from the backend. However, this would incur unnecessary load. Therefore, we accept that the timestamps are slightly out-of-date, but they will get consistent once the conversation list is refreshed again (e.g., on page reload or when creating a new conversation).
   */
  if (!id) return
  const conversation = conversations.value.find((c) => c.id === id)
  if (conversation) {
    conversation.updated_at = new Date().toISOString()
  }
}
</script>

<template>
  <main class="bg-white dark:bg-gray-900">
    <HelpModal />

    <ChatsSidebar
      @create-conversation="onCreateConversation"
      @hide-conversation="onHideConversation"
      @load-conversation="onLoadConversation"
    />

    <div class="app relative mx-4">
      <div class="h-screen max-h-[100dvh] lg:pt-0 pt-10 mx-auto w-full max-w-3xl flex flex-col">
        <ErrorDisplay scope="general" />
        <div
          v-if="conversation.messages.length == 0 && !showConsentDialog"
          class="flex items-center justify-center h-full"
        >
          <WelcomeMessage />
        </div>
        <ChatComponent
          @conversation-started="onConversationStarted"
          @conversation-updated="onConversationUpdated"
        />
      </div>
    </div>
  </main>
</template>
