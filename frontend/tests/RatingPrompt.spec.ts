import { test, expect } from '@playwright/test'
import { giveConsent, resetConversations, setupApiMocks } from './utils'

const BASE_URL = 'http://localhost:5173'

test.describe('Conversation rating prompt', () => {
  test.beforeEach(async ({ page }) => {
    resetConversations()
    await setupApiMocks(page)
    await page.goto(BASE_URL)
  })
  test('Confirm that the rating prompt appears after six messages in the current conversation.', async ({
    page
  }) => {
    await giveConsent(page)

    // Add messages to the conversation
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // Add three messages to trigger the rating prompt
    for (let i = 0; i < 3; i++) {
      await messageInputTextArea.fill(`Test message ${i + 1}`)
      await messageInputButton.click()
    }

    // Verify the rating prompt is displayed after 6 messages
    const ratingPrompt = page.locator('#rating-prompt')
    await expect(ratingPrompt).toBeVisible()

    // Verify the default rating value is 5
    const ratingInput = ratingPrompt.locator('#rating-input')
    await expect(ratingInput).toHaveValue('5')

    // Change the rating to 7
    await ratingInput.fill('7')
    await expect(ratingInput).toHaveValue('7')

    // Submit the rating
    const submitButton = ratingPrompt.locator('#rating-submit')
    submitButton.click()
    await ratingPrompt.waitFor({ state: 'detached' })

    const notification = page.getByTestId('chatComponentNotification')
    await notification.waitFor({ state: 'visible' })
    await expect(notification).toBeVisible()

    await expect(notification).toContainText('Your feedback has been submitted successfully!')
    await page.waitForTimeout(2000)

    await expect(notification).not.toBeVisible()
  })
  test('Confirm that the rating prompt appears only once for each conversation', async ({
    page
  }) => {
    await giveConsent(page)

    // Add messages to the conversation
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const messageInputTextArea = page.locator('textarea.message-input')
    const messageInputButton = page.locator('#send-message-button')

    // Add three messages to trigger the rating prompt
    for (let i = 0; i < 3; i++) {
      await messageInputTextArea.fill(`Test message ${i + 1}`)
      await messageInputButton.click()
    }

    // send rating to conversation id
    const ratingPrompt = page.locator('#rating-prompt')
    await expect(ratingPrompt).toBeVisible()
    const ratingInput = ratingPrompt.locator('#rating-input')
    await ratingInput.fill('7')
    await expect(ratingInput).toHaveValue('7')
    const submitButton = ratingPrompt.locator('#rating-submit')
    await submitButton.click()

    // Open new conversation
    const newConversationButton = page.locator('button#new-conversation')
    await expect(newConversationButton).toBeEnabled()
    await newConversationButton.click()

    // Add three messages to trigger the rating prompt
    for (let i = 3; i < 6; i++) {
      await messageInputTextArea.fill(`Test message ${i + 1}`)
      await messageInputButton.click()
    }

    // Send rating for conversation 2
    await expect(ratingPrompt).toBeVisible()
    await ratingInput.fill('7')
    await expect(ratingInput).toHaveValue('7')
    await submitButton.click()

    // Load conversation 1
    const conversationListItems = page.locator('li.conversation-item')
    const firstConversationLink = conversationListItems.nth(1).locator('a')
    await firstConversationLink.click()

    // Add another 3 messages
    for (let i = 6; i < 9; i++) {
      await messageInputTextArea.fill(`Test message ${i + 1}`)
      await messageInputButton.click()
    }

    //Expect that now rating prompt is not shown
    await expect(ratingPrompt).not.toBeVisible()

    // Load conversation 2
    const secondConversationLink = conversationListItems.nth(1).locator('a')
    await secondConversationLink.click()

    // Add another 3 messages
    for (let i = 9; i < 12; i++) {
      await messageInputTextArea.fill(`Test message ${i + 1}`)
      await messageInputButton.click()
    }

    //Expect that now rating prompt is not shown
    await expect(ratingPrompt).not.toBeVisible()
  })
})
