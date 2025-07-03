<script setup lang="ts">
import { type ResponseState } from './ChatComponent.vue'
import { formatDate } from '@/utils'
import CollapsibleSection from './CollapsibleSection.vue'
import ChatMessageSkeleton from './ChatMessageSkeleton.vue'
import NotificationMessage from './NotificationMessage.vue'
import ClipboardIcon from './icons/ClipboardIcon.vue'
import PencilIcon from './icons/PencilIcon.vue'
import ThumbsUpIcon from './icons/ThumbsUpIcon.vue'
import ThumbsDownIcon from './icons/ThumbsDownIcon.vue'
import placeholderUser from '../assets/user.png'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { Message } from '@/stores/chatStore'
import { useNotification } from '@/composables/notification'
import SourceList from '@/components/SourceList.vue'

const emit = defineEmits(['rate-message'])

export interface ChatMessageConfig {
  name: string
  image: string
  allowEdit: boolean
  allowCopy: boolean
  allowRating: boolean
  showTimestamp: boolean
}

export interface Props {
  message: Message
  state?: ResponseState
  config?: ChatMessageConfig
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  config: () => ({
    name: 'Unknown User',
    image: placeholderUser,
    allowCopy: true,
    allowEdit: false,
    allowRating: false,
    showTimestamp: false
  })
})

const { notification, notify } = useNotification()

function convertMarkupToHtml(markup: string): string {
  return DOMPurify.sanitize(marked(markup, { async: false }))
}

function copyToClipboard() {
  const textToCopy = props.message.content
  navigator.clipboard
    .writeText(textToCopy)
    .then(() => notify('Message copied to clipboard', 'success'))
    .catch(() => notify('Something went wrong.', 'warning'))
}
</script>

<template>
  <div class="grid lg:grid-cols-[28px_minmax(0,1fr)] grid-cols-1">
    <div class="col-span-2 flex items-center">
      <img
        class="mr-4 max-w-[28px] max-h-[28px] border-1 border-white/40 rounded-full"
        :src="config.image"
      />

      <div>
        <span class="font-bold capitalize text-gray-800 dark:text-gray-100">
          {{ config.name }}
        </span>
        <span v-if="config.showTimestamp && message.created_at" class="text-gray-300">
          {{ ` (${formatDate(message.created_at)})` }}
        </span>
      </div>
    </div>

    <div class="col-span-2 grid grid-cols-subgrid mt-2">
      <div class="col-start-1 lg:col-start-2 lg:ml-4">
        <template v-if="state == 'retrieving'">
          <ChatMessageSkeleton />
        </template>
        <template v-else>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span
            class="mt-3 prose dark:prose-invert"
            v-html="convertMarkupToHtml(message.content)"
          ></span>

          <template v-if="state == 'idle'">
            <CollapsibleSection
              v-if="!message.non_answer && message.sources.length > 0"
              class="mt-3 text-sm text-slate-600 dark:text-slate-400"
              title="Where can I verify this answer?"
            >
              <SourceList :sources="message.sources" class="mt-2" />
            </CollapsibleSection>

            <div
              class="flex text-gray-600 gap-2 dark:text-gray-400 mt-3"
              v-if="config.allowCopy || config.allowEdit || config.allowRating"
            >
              <div v-if="config.allowCopy" aria-label="Copy" class="flex">
                <button
                  class="copy-button rounded-sm transition hover:text-black dark:hover:text-white"
                  @click="copyToClipboard"
                >
                  <ClipboardIcon class="w-4 h-4" />
                </button>
                <NotificationMessage
                  data-testid="chatMessageNotification"
                  v-if="notification"
                  :message="notification.message"
                  :kind="notification.kind"
                />
              </div>
              <div v-if="config.allowEdit" aria-label="Edit" class="flex">
                <button class="rounded-sm transition hover:text-black dark:hover:text-white">
                  <PencilIcon class="w-4 h-4" />
                </button>
              </div>

              <div v-if="config.allowRating" aria-label="Good Response" class="flex">
                <button
                  :class="[
                    'rounded-sm transition',
                    message.feedback === 'good'
                      ? 'text-green-500 dark:text-green-400'
                      : 'hover:text-black dark:hover:text-white'
                  ]"
                  @click="emit('rate-message', message.feedback === 'good' ? null : 'good')"
                >
                  <ThumbsUpIcon class="w-4 h-4" />
                </button>
              </div>

              <div v-if="config.allowRating" aria-label="Bad Response" class="flex">
                <button
                  :class="[
                    'rounded-sm transition',
                    message.feedback === 'bad'
                      ? 'text-red-500 dark:text-red-400'
                      : 'hover:text-black dark:hover:text-white'
                  ]"
                  @click="emit('rate-message', message.feedback === 'bad' ? null : 'bad')"
                >
                  <ThumbsDownIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>
