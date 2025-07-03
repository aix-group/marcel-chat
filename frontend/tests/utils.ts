import type {
  ConversationRead,
  ConversationListItem,
  MessageRead,
  ChatResponseChunk,
  ChatRequest,
  ConversationRatingRequest
} from '@/services/chat'
import { expect, type Page } from 'playwright/test'

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0,
      v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export async function giveConsent(page: Page) {
  await page.evaluate(() => localStorage.setItem('consentGiven', 'true'))
  await page.reload()
}

/**
 * Mock backend
 */
export const conversations: Array<ConversationRead> = []

export function resetConversations() {
  conversations.splice(0, conversations.length)
}

export function mockFetchConversation(id: string): ConversationRead | undefined {
  return conversations.find((c) => c.id == id)
}

export function mockFetchConversations(): Array<ConversationListItem> {
  const conversationsSorted = conversations.sort((a, b) => {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

  return conversationsSorted.map((c) => {
    return {
      id: c.id,
      created_at: c.created_at,
      updated_at: c.updated_at,
      rating: c.rating,
      preview: c.messages[0].content
    }
  })
}

export function mockHideConversation(id: string) {
  const index = conversations.findIndex((c) => c.id == id)
  conversations.splice(index, 1)
}

export function mockPostConversationRating(ratingRequest: ConversationRatingRequest) {
  const conversation = conversations.find((c) => c.id == ratingRequest.conversation_id)
  if (conversation) {
    conversation.rating = ratingRequest.rating
  }
  return { status: 'success' }
}

export function mockChat(chatRequest: ChatRequest): ChatResponseChunk {
  // use existing conversation or create a new one
  let conversation = conversations.find((c) => c.id == chatRequest.conversation_id)
  if (!conversation) {
    conversation = {
      id: generateUUID(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: []
    }
    conversations.push(conversation)
  }
  conversation.updated_at = new Date().toISOString()

  const lastUserMessage = chatRequest['messages'][chatRequest['messages'].length - 1]['content']
  const userMessage: MessageRead = {
    id: 0,
    role: 'user',
    content: lastUserMessage,
    created_at: new Date().toISOString(),
    sources: []
  }
  const assistantMessage: MessageRead = {
    id: 1,
    role: 'assistant',
    content: 'This is the assistant response',
    created_at: new Date().toISOString(),
    sources: []
  }
  conversation.messages.push(userMessage, assistantMessage)

  const responseData: ChatResponseChunk = {
    content: assistantMessage.content,
    conversation_id: conversation.id,
    user_message: userMessage,
    assistant_message: assistantMessage
  }

  return responseData
}

export async function setupApiMocks(page: Page) {
  await page.route('*/**/api/start_session', async (route) => {
    const response = {
      user_id: generateUUID()
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response)
    })
  })

  await page.route('*/**/api/me/consent', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true })
    })
  })

  await page.route('*/**/api/query', async (route, request) => {
    const response = mockChat(request.postDataJSON())
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response)
    })
  })

  await page.route('*/**/api/conversations', async (route) => {
    const response = mockFetchConversations()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response)
    })
  })

  await page.route('*/**/api/conversation/*/hide', async (route, request) => {
    const url = new URL(request.url())
    const pathnameParts = url.pathname.split('/')
    const id = pathnameParts[pathnameParts.indexOf('conversation') + 1]
    mockHideConversation(id)
    await route.fulfill()
  })

  await page.route('*/**/api/conversation/*', async (route, request) => {
    const url = new URL(request.url())
    const pathnameParts = url.pathname.split('/')
    const id = pathnameParts[pathnameParts.indexOf('conversation') + 1]
    const response = mockFetchConversation(id)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response)
    })
  })

  await page.route('*/**/api/feedback', async (route, request) => {
    if (request.method() === 'POST') {
      const { feedback } = request.postDataJSON()
      await expect(feedback === 'good' || feedback === 'bad').toBeTruthy()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success' })
      })
    }
  })

  await page.route('*/**/api/rating*', async (route, request) => {
    if (request.method() === 'POST') {
      const response = mockPostConversationRating(request.postDataJSON())
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      })
    }
  })
}
