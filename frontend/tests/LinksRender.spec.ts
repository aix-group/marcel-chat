import { test, expect } from '@playwright/test'
import type { ChatResponseChunk } from '@/services/chat'
import { generateUUID, giveConsent } from './utils'

const BASE_URL = 'http://localhost:5173'

test.describe('Links Rendering End-to-End Test', () => {
  test.beforeEach(async ({ page }) => {
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

    await page.route('*/**/api/query', async (route, request) => {
      if (request.method() === 'POST') {
        const requestData = request.postDataJSON()
        const lastUserMessage = requestData['messages'][requestData['messages'].length - 1]

        const assistantMessageContent = `Test Message. Follow [**this link**][122]. And another [valid link][199]. But this is invalid

[122]: http://example0
[199]: https://example1
`
        const response_data: ChatResponseChunk = {
          content: assistantMessageContent,
          conversation_id: generateUUID(),
          user_message: {
            id: 0,
            role: 'user',
            content: lastUserMessage['content'],
            created_at: new Date().toISOString(),
            sources: []
          },
          assistant_message: {
            id: 1,
            role: 'assistant',
            content: assistantMessageContent,
            created_at: new Date().toISOString(),
            sources: []
          }
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(response_data)
        })
      } else {
        await route.continue()
      }
    })

    await page.goto(BASE_URL)
  })

  test('Verify that markdown is rendered', async ({ page }) => {
    await giveConsent(page)
    const messageInputTextArea = page.locator('textarea.message-input')
    const messageInputButton = page.locator('#send-message-button')

    await messageInputTextArea.fill('Test message')
    await messageInputButton.click()

    await expect(page.locator('div.message')).toHaveCount(2)
    const renderedMessage = page.locator('div.message').nth(1)
    await expect(renderedMessage).toContainText(
      'Test Message. Follow this link. And another valid link. But this is invalid'
    )

    const thisLink = renderedMessage.locator('a', { hasText: 'this link' })
    const validLink = renderedMessage.locator('a', { hasText: 'valid link' })

    // Verify that the links are rendered with correct href attributes
    await expect(thisLink).toHaveAttribute('href', 'http://example0')
    await expect(validLink).toHaveAttribute('href', 'https://example1')
  })
})
