import { APIError } from './types'

const BASE_URL = '/api'

export async function startSession() {
  // Calls backend to start session. The response includes an httpOnly cookie with the user ID.
  const response = await fetch(`${BASE_URL}/start_session`)
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}

export async function putUserConsent() {
  const response = await fetch(`${BASE_URL}/me/consent`, {
    method: 'PUT'
  })
  if (!response.ok) {
    const responseData = await response.json()
    throw new APIError(responseData['detail'], response.status)
  }
  return response.json()
}
