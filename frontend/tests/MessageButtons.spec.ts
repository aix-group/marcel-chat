import { test, expect } from '@playwright/test'
import { giveConsent, setupApiMocks } from './utils'

const BASE_URL = 'http://localhost:5173'

test.describe('Message Buttons End-to-End Test', () => {
  test.beforeEach(async ({ page }) => {
    setupApiMocks(page)
    await page.goto(BASE_URL)
    await giveConsent(page)
  })

  test('Verify that the message feedback button changes color after feedback is sent.', async ({
    page
  }) => {
    const messageInputTextArea = page.locator('textarea.message-input')
    const messageInputButton = page.locator('#send-message-button')

    // Add a message to trigger the feedback buttons
    await messageInputTextArea.fill('Test message for rating')
    await messageInputButton.click()

    // Select the good response button and verify color change
    const goodButton = page.locator('div[aria-label="Good Response"]').locator('button')
    await goodButton.click()
    await expect(goodButton).toHaveClass(/text-green-500/)

    // Select the bad response button and verify color change
    const badButton = page.locator('div[aria-label="Bad Response"]').locator('button')
    await badButton.click()
    await expect(badButton).toHaveClass(/text-red-500/)

    // Verify that clicking the bad response button removes the green color from the good button
    await expect(goodButton).not.toHaveClass(/text-green-500/)
  })

  test('copy button copies agent message and displays notification', async ({
    page,
    browserName,
    context
  }) => {
    test.skip(
      browserName === 'webkit',
      'Skipping test because webkit does not support clipboard API'
    )
    if (browserName == 'chromium') {
      // chromium needs permissions
      await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    }

    // Add a user message an
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')
    await messageInputTextArea.fill('Test message for copy')
    await messageInputButton.click()

    // Locate the agent response container, and click copy button
    const messageContainer = page.locator('div.message').nth(1)
    const copyButton = messageContainer.locator('button.copy-button')
    await copyButton.click()
    await page.waitForTimeout(100)

    // Check the clipboard to ensure the correct text was copied
    const clipboardText = await page.evaluate(async () => {
      return await navigator.clipboard.readText()
    })
    expect(clipboardText).toBe('This is the assistant response')

    // Check that the notification message is displayed
    const notification = page.getByTestId('chatMessageNotification')
    await notification.waitFor({ state: 'visible' })
    await expect(notification).toBeVisible()
    await expect(notification).toContainText('Message copied to clipboard')
    await page.waitForTimeout(2000)
    await expect(notification).not.toBeVisible()
  })
})
