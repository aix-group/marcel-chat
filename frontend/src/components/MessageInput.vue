<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import ArrowUpIcon from './icons/ArrowUpIcon.vue'
import StopIcon from './icons/StopIcon.vue'
import { useConsentStore } from '@/stores/consentStore'
import { storeToRefs } from 'pinia'

const { consentGiven } = storeToRefs(useConsentStore())

export interface Props {
  placeholder?: string
  generating?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Send a Message',
  generating: false
})

const emit = defineEmits<{
  sendMessage: [message: string]
  stopGeneration: []
}>()

const message = ref('')

function sendMessage() {
  if (!props.generating) {
    emit('sendMessage', message.value)
    message.value = ''
  }
}

const submitButtonClasses = computed(() => {
  if (message.value === '') {
    return 'bg-gray-200 dark:bg-gray-700 disabled'
  } else {
    return 'bg-black hover:bg-gray-900 dark:bg-white dark:text-gray-900 hover:dark:bg-gray-100'
  }
})

function adjustHeight() {
  const textarea = textareaRef.value
  const container = chatInput.value
  if (!textarea || !container) return

  nextTick(() => {
    textarea.style.height = 'auto'
    const newHeight = `${textarea.scrollHeight}px`
    textarea.style.height = newHeight
    // Adjust container scroll to maintain bottom alignment
    container.scrollTop = container.scrollHeight
  })
}

function handleKeydown(event: KeyboardEvent) {
  const textarea = textareaRef.value
  const container = chatInput.value
  if (!textarea || !container) return

  if (event.key === 'Enter' && event.shiftKey) {
    event.preventDefault() // Prevent default enter behavior
    const cursorPosition = textarea.selectionStart
    const textBeforeCursor = textarea.value.substring(0, cursorPosition)
    const textAfterCursor = textarea.value.substring(cursorPosition)
    textarea.value = `${textBeforeCursor}\n${textAfterCursor}`
    textarea.selectionStart = cursorPosition + 1
    textarea.selectionEnd = cursorPosition + 1
    adjustHeight()
  } else if (event.key === 'Enter' && message.value !== '') {
    event.preventDefault()
    sendMessage()
    adjustHeight()
  } else if (event.key === 'Enter' && message.value === '') {
    event.preventDefault()
    // noop
  }
}

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const chatInput = ref<HTMLDivElement | null>(null)

onMounted(() => {
  if (textareaRef.value && chatInput.value) {
    adjustHeight()
  }
})
</script>

<template>
  <form
    ref="chatInput"
    class="w-full rounded-3xl px-1.5 border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-850 dark:text-gray-100"
  >
    <div class="flex">
      <textarea
        id="message-input"
        ref="textareaRef"
        v-model="message"
        :placeholder="placeholder"
        class="message-input w-full overflow-hidden resize-none border-none outline-hidden bg-inherit border-0 focus:outline-hidden focus:ring-0 py-3 px-3 rounded-xl h-[48px]"
        rows="1"
        @keydown="(event) => handleKeydown(event)"
        @input="adjustHeight"
        :disabled="!consentGiven"
      ></textarea>

      <div class="self-end mb-2 flex space-x-1 mr-1">
        <button
          v-if="generating"
          class="transition rounded-full p-1.5 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 hover:dark:bg-gray-600 text-gray-800 dark:text-gray-200"
          type="button"
          @click="$emit('stopGeneration')"
        >
          <StopIcon class="w-5 h-5" />
        </button>
        <button
          v-else
          id="send-message-button"
          :class="['text-white transition rounded-full p-1.5 self-center', submitButtonClasses]"
          :disabled="!message"
          type="button"
          @click="sendMessage"
        >
          <ArrowUpIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </form>
</template>
