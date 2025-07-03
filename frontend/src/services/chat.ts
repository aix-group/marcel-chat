import { APIError } from './types'

const BASE_URL = '/api'

export type MessageFeedback = 'good' | 'bad' | null
export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface ChatRequest {
  conversation_id?: string // uuid
  messages: Array<ChatMessage>
}

export interface SourceRead {
  url: string
  score: number
  title: string
  favicon: string
}

export interface MessageRead {
  id: number
  role: ChatRole
  content: string
  non_answer?: boolean
  feedback?: MessageFeedback
  created_at: string
  sources: Array<SourceRead>
}

export interface ChatResponseChunk {
  conversation_id?: string
  user_message?: MessageRead
  assistant_message?: MessageRead
  content?: string
  non_answer?: boolean

  // Returned by API on streaming errors
  error_status_code?: number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  error_content?: { [key: string]: any }
}

export interface ConversationRead {
  id: string // uuid
  rating?: number
  created_at: string
  updated_at: string
  messages: Array<MessageRead>
}

export interface ConversationListItem {
  id: string // uuid
  rating?: number
  created_at: string
  updated_at: string
  preview: string
}

export interface MessageFeedbackRequest {
  message_id: number
  feedback: MessageFeedback
}

export interface ConversationRatingRequest {
  conversation_id: string // uuid
  rating: number
}

export async function fetchConversation(id: string): Promise<ConversationRead> {
  const response = await fetch(`${BASE_URL}/conversation/${id}`)
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return await response.json()
}

export async function fetchConversations(): Promise<Array<ConversationListItem>> {
  const response = await fetch(`${BASE_URL}/conversations`)
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return await response.json()
}

export async function hideConversation(id: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/conversation/${id}/hide`, {
    method: 'PUT'
  })
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
}

export async function postMessageFeedback(feedbackRequest: MessageFeedbackRequest) {
  const response = await fetch(`${BASE_URL}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(feedbackRequest)
  })
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return await response.json()
}

export async function postConversationRating(ratingRequest: ConversationRatingRequest) {
  const response = await fetch(`${BASE_URL}/rating`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(ratingRequest)
  })
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return await response.json()
}

export async function chat(
  chatRequest: ChatRequest,
  onMessage: (chunk: ChatResponseChunk) => void
): Promise<void> {
  const response = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(chatRequest)
  })

  if (!response.ok || !response.body) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }

  const reader = response.body.getReader()
  async function readStream() {
    // The response is a jsonl stream. First decode binary to string, then parse json objects.
    // As one chunk may contain multiple (or partial) lines, we buffer the data and process finished lines one-by-one
    const decoder = new TextDecoder()
    let buffer = ''

    function processLine(line: string) {
      if (line.trim()) {
        const chunk: ChatResponseChunk = JSON.parse(line)

        // Streaming errors are signaled through an error chunk.
        // We raise this to clients in an APIError with the detail, so that the can use try/except
        if (chunk.error_content && chunk.error_status_code) {
          throw new APIError(chunk.error_content['detail'], chunk.error_status_code)
        }

        onMessage(chunk)
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep the last unfinished line for the next chunk
      lines.forEach(processLine)
    }

    if (buffer.trim()) {
      processLine(buffer)
    }
  }

  await readStream()
}
