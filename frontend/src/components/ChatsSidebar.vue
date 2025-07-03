<script setup lang="ts">
import { ref } from 'vue'
import PlusIcon from './icons/PlusIcon.vue'
import LinesIcon from './icons/LinesIcon.vue'
import CloseIcon from './icons/CloseIcon.vue'
import { useConversationStore, useConversationsStore } from '@/stores/chatStore'
import { storeToRefs } from 'pinia'
import ErrorDisplay from '@/components/ErrorDisplay.vue'

const emit = defineEmits<{
  'create-conversation': []
  'load-conversation': [id?: string]
  'hide-conversation': [id?: string]
}>()

const isDrawerOpen = ref(false)
const { conversation } = storeToRefs(useConversationStore())
const { conversations } = storeToRefs(useConversationsStore())

function toggleDrawer() {
  isDrawerOpen.value = !isDrawerOpen.value
}
</script>

<template>
  <button
    id="open-sidebar"
    type="button"
    class="fixed p-2 mt-2 ms-3 text-sm rounded-lg focus:outline-hidden z-10 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 focus:ring-gray-200 dark:focus:ring-gray-600"
    @click="toggleDrawer"
  >
    <span class="sr-only">Open sidebar</span>
    <LinesIcon class="w-6 h-6" />
  </button>

  <!-- Drawer -->
  <div
    id="drawer-navigation"
    :class="[
      'fixed top-0 left-0 z-40 w-64 h-screen p-4 overflow-y-auto dark:[color-scheme:dark] transition-transform',
      'bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100',
      { '-translate-x-full': !isDrawerOpen, 'translate-x-0': isDrawerOpen }
    ]"
    tabindex="-1"
    aria-labelledby="drawer-navigation-label"
  >
    <div class="flex justify-between items-center">
      <h5 id="drawer-navigation-label" class="text-base font-semibold text-gray-500 uppercase">
        Conversations
      </h5>
      <!-- text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 -->
      <button
        id="close-sidebar"
        type="button"
        aria-controls="drawer-navigation"
        class="rounded-lg text-sm p-1.5 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100 bg-transparent"
        @click="toggleDrawer"
      >
        <CloseIcon class="w-5 h-5" />
        <span class="sr-only">Close menu</span>
      </button>
    </div>
    <div class="py-4 overflow-y-auto">
      <button
        id="new-conversation"
        :disabled="conversation.messages?.length === 0"
        :class="[
          'flex items-center w-full p-2 mb-4 rounded-lg focus:outline-hidden focus:ring-2',
          conversation.messages?.length == 0
            ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 dark:hover:bg-blue-400 text-white focus:ring-blue-400 dark:focus:ring-blue-300'
        ]"
        @click="emit('create-conversation')"
      >
        <PlusIcon class="w-5 h-5 mr-2" />
        New Conversation
      </button>

      <ErrorDisplay scope="conversation-list" />
      <ul class="">
        <li
          v-for="conversation in conversations"
          :key="conversation.id"
          class="conversation-item flex justify-between items-center rounded-lg p-2 hover:bg-gray-200 dark:hover:bg-gray-700"
        >
          <a
            href="#"
            @click="emit('load-conversation', conversation.id)"
            class="dark:text-gray-200 conversation-preview"
          >
            {{ conversation.preview }}
          </a>

          <button
            type="button"
            class="text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"
            @click="emit('hide-conversation', conversation.id)"
          >
            <CloseIcon class="w-5 h-5" />
            <span class="sr-only">Remove conversation</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style>
.conversation-preview {
  white-space: nowrap;
  overflow: hidden;
  width: calc(100%);
  -webkit-mask-image: linear-gradient(to right, black 80%, transparent 100%);
  mask-image: linear-gradient(to right, black 80%, transparent 100%);
}
</style>
