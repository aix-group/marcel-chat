import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type MessageFeedback = 'good' | 'bad' | null

export interface Source {
  url: string
  score: number
  title?: string
  favicon?: string
}

export interface Message {
  id?: number
  role: 'user' | 'assistant'
  content: string
  non_answer?: boolean
  feedback?: MessageFeedback
  created_at?: string // iso date
  sources: Array<Source>
}

export interface Conversation {
  id?: string
  rating?: number
  created_at: string // iso date
  updated_at: string // iso date
  messages: Array<Message>
}

export interface ConversationListItem {
  id?: string
  rating?: number
  created_at: string // iso date
  updated_at: string // iso date
  preview: string
}

export const useConversationStore = defineStore('conversation', () => {
  const conversation = ref<Conversation>({
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages: []
  })

  return { conversation }
})

export const useConversationsStore = defineStore('conversations', () => {
  const _conversations = ref<Array<ConversationListItem>>([])
  const conversations = computed({
    get() {
      return _conversations.value.sort((a, b) => {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      })
    },
    set(newValue) {
      _conversations.value = newValue
    }
  })
  return { conversations }
})
