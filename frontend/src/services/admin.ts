import { APIError } from '@/services/types'

const BASE_URL = '/api'

export type MessageFeedback = 'good' | 'bad' | null
export type ChatRole = 'user' | 'assistant'

export interface UserRead {
  username: string
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

export interface ConversationRead {
  id: string
  user_id: number
  rating: number | null
  created_at: string
  updated_at: string
  messages: Array<MessageRead>
}

export interface ConversationListItem {
  id: string
  user_id: number
  rating: number | null
  created_at: string
  updated_at: string
  n_messages: number
}

export interface ConversationList {
  page: number
  size: number
  total: number
  conversations: Array<ConversationListItem>
}

export interface TimeSeriesItem {
  date: string
  value: number | null
}

export interface StatsTimeSeries {
  conversations: TimeSeriesItem[]
  users: TimeSeriesItem[]
  messages: TimeSeriesItem[]
  ratings: TimeSeriesItem[]
}

export interface StatsTotal {
  total_conversations: number
  total_users: number
  total_messages: number
  total_average_rating: number | null
}

export interface StatisticsRead {
  time_series: StatsTimeSeries
  totals: StatsTotal
}

export type Agg = 'day' | 'week' | 'month' | 'year'

export async function fetchConversations(page = 0, size = 10): Promise<ConversationList> {
  const response = await fetch(`${BASE_URL}/admin/conversations?page=${page}&size=${size}`)
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}

export async function fetchConversation(id: string): Promise<ConversationRead> {
  const response = await fetch(`${BASE_URL}/admin/conversation/${id}`)
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}

export async function login(username: string, password: string): Promise<UserRead> {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await fetch(`${BASE_URL}/admin/login`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })

  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}

export async function logout() {
  const response = await fetch(`${BASE_URL}/admin/logout`, {
    method: 'POST'
  })
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}

export async function isAuthenticated() {
  const response = await fetch(`${BASE_URL}/admin/me`)
  return response.ok
}

/**
 * Fetches statistical data from the backend API within an optional date range.
 *
 * @param start_date - Optional start date in ISO format (YYYY-MM-DD). If null or undefined, no filtering is applied.
 * @param end_date - Optional end date in ISO format (YYYY-MM-DD). If null or undefined, no filtering is applied.
 * @param agg - Optional aggregation type
 * @returns A promise that resolves to the fetched statistics.
 * @throws An error if the request fails or the server returns an error response.
 */
export async function fetchStatistics(
  start_date?: string,
  end_date?: string,
  agg: Agg = 'day'
): Promise<StatisticsRead> {
  let url = `${BASE_URL}/admin/statistics`

  if (start_date && end_date) {
    const params = new URLSearchParams({ start_date, end_date, agg })
    url += `?${params.toString()}`
  }

  const response = await fetch(url, {
    method: 'GET'
  })

  if (!response.ok) {
    const responseData = await response.json()
    throw new Error(responseData['detail'] || 'Failed to fetch statistics')
  }

  return response.json()
}
