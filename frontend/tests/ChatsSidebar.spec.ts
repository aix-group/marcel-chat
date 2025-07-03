import { test, expect } from '@playwright/test'
import { resetConversations, giveConsent, setupApiMocks } from './utils'

const BASE_URL = 'http://localhost:5173'

test.describe('ChatsSidebar End-to-End Test', () => {
  test.beforeEach(async ({ page }) => {
    resetConversations()
    await setupApiMocks(page)
    await page.goto(BASE_URL)
    await giveConsent(page)
  })
  test('add new conversation', async ({ page }) => {
    // at the beginning there are no messages - "new conversation" button is disabled
    const OpenSideBarButton = page.locator('button#open-sidebar')
    await OpenSideBarButton.click()
    const newConversationButton = page.locator('button#new-conversation')
    await expect(newConversationButton).toBeDisabled()

    // we need to add two messages
    await page.waitForSelector('textarea#message-input', { state: 'visible' })
    const messageInputTextArea = page.locator('textarea#message-input')
    let messageText = 'Message 1'
    await messageInputTextArea.fill(messageText)
    const messageInputButton = page.locator('#send-message-button')
    await messageInputButton.click()
    await page.waitForSelector('div.message', { state: 'visible' })

    // the 'new conversation" button should be enabled
    await expect(page.locator('div.message')).toHaveCount(2)
    await expect(newConversationButton).toBeEnabled()
    await newConversationButton.click()

    // conversation should be added to conversations list
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(1)
    await expect(conversationListItems).toContainText('Message 1')

    // amount of messages should be 0
    await expect(page.locator('div.message')).toHaveCount(0)
    await expect(newConversationButton).toBeDisabled()

    // add 2 messages
    messageText = 'Message 3'
    await messageInputTextArea.fill(messageText)
    await messageInputButton.click()

    await expect(newConversationButton).toBeEnabled()
    await expect(conversationListItems).toHaveCount(2)
    await expect(conversationListItems.nth(0)).toContainText('Message 3')
  })

  test('open and close sidebar', async ({ page }) => {
    const OpenSideBarButton = page.locator('button#open-sidebar')
    await OpenSideBarButton.click()
    const sidebar = page.locator('#drawer-navigation')
    await expect(sidebar).toBeVisible()
    const CloseSideBarButton = page.locator('button#close-sidebar')
    await CloseSideBarButton.click()
    await expect(sidebar).toHaveClass(/-translate-x-full/)
  })

  test('remove a conversation from the list', async ({ page }) => {
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // First conversation
    await messageInputTextArea.fill('Message 1')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    //Locate new conversation button
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const newConversationButton = page.locator('button#new-conversation')
    await newConversationButton.click()

    // Second conversation
    await messageInputTextArea.fill('Message 2')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Third conversation
    await messageInputTextArea.fill('Message 3')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    // Verify that three conversations are added to the list
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(3)
    await expect(conversationListItems.nth(2)).toContainText('Message 1')
    await expect(conversationListItems.nth(1)).toContainText('Message 2')
    await expect(conversationListItems.nth(0)).toContainText('Message 3')

    // Remove the first conversation
    const removeFirstConversationButton = conversationListItems.nth(2).locator('button')
    await removeFirstConversationButton.click()

    await expect(conversationListItems).toHaveCount(2)
    await expect(conversationListItems.nth(0)).toContainText('Message 3')
    await expect(conversationListItems.nth(1)).toContainText('Message 2')

    // remove third conversation
    const removeThirdConversationButton = conversationListItems.nth(0).locator('button')
    await removeThirdConversationButton.click()
    await expect(conversationListItems).toHaveCount(1)
    await expect(conversationListItems.nth(0)).toContainText('Message 2')
  })

  test('load a conversation from the list', async ({ page }) => {
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // First conversation
    await messageInputTextArea.fill('Message 1')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    //Locate new conversation button
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const newConversationButton = page.locator('button#new-conversation')
    await newConversationButton.click()

    // Second conversation
    await messageInputTextArea.fill('Message 2')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Third conversation
    await messageInputTextArea.fill('Message 3')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    // Verify that three conversations are added to the list
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(3)
    await expect(conversationListItems.nth(2)).toContainText('Message 1')
    await expect(conversationListItems.nth(1)).toContainText('Message 2')
    await expect(conversationListItems.nth(0)).toContainText('Message 3')

    // Click on the second conversation to load it
    const secondConversationLink = conversationListItems.nth(1).locator('a')
    await secondConversationLink.click()

    // Verify that the second conversation is loaded with its messages
    const messages = page.locator('div.message')
    await expect(messages).toHaveCount(2)
    await expect(messages.nth(0)).toContainText('Message 2')
    await expect(messages.nth(1)).toContainText('This is the assistant response')
  })

  test('load a conversation after updating the page', async ({ page }) => {
    // Add messages to the conversation
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // Add messages to the current conversation
    await messageInputTextArea.fill('Message 2')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await expect(page.locator('div.message').nth(0)).toContainText('Message 2')
    await expect(page.locator('div.message').nth(1)).toContainText('This is the assistant response')

    // Reload the page
    await page.reload()

    // Verify that the same messages are still displayed after reload
    const messagesAfterReload = page.locator('div.message')
    await expect(messagesAfterReload).toHaveCount(2)
    await expect(messagesAfterReload.nth(0)).toContainText('Message 2')
    await expect(messagesAfterReload.nth(1)).toContainText('This is the assistant response')

    // Send another message to verify that everything is working
    await messageInputTextArea.fill('Message 3')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(4)
    await expect(page.locator('div.message').nth(2)).toContainText('Message 3')
    await expect(page.locator('div.message').nth(3)).toContainText('This is the assistant response')
  })
  test('remove the current conversation', async ({ page }) => {
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // Add two messages to the current conversation
    await messageInputTextArea.fill('Message A')
    await messageInputButton.click()
    await messageInputTextArea.fill('Message B')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(4)
    await expect(page.locator('div.message').nth(0)).toContainText('Message A')
    await expect(page.locator('div.message').nth(2)).toContainText('Message B')

    // Verify conversation count and preview text
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(1)
    await expect(conversationListItems.nth(0)).toContainText('Message A')

    // Click to remove the current conversation
    const removeConversationButton = conversationListItems.nth(0).locator('button')
    await removeConversationButton.click()

    // Verify conversation list is empty
    await expect(conversationListItems).toHaveCount(0)

    // Verify message list is empty
    await expect(page.locator('div.message')).toHaveCount(0)
  })
  test('check that conversations are sorted by date in descending order', async ({ page }) => {
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // First conversation
    await messageInputTextArea.fill('Message 1')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    //Locate new conversation button
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const newConversationButton = page.locator('button#new-conversation')
    await newConversationButton.click()

    // Second conversation
    await messageInputTextArea.fill('Message 2')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Third conversation
    await messageInputTextArea.fill('Message 3')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Forth conversation
    await messageInputTextArea.fill('Message 4')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Fifth conversation
    await messageInputTextArea.fill('Message 5')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    // Verify that three conversations are added to the list
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(5)
    await expect(conversationListItems.nth(4)).toContainText('Message 1')
    await expect(conversationListItems.nth(3)).toContainText('Message 2')
    await expect(conversationListItems.nth(2)).toContainText('Message 3')
    await expect(conversationListItems.nth(1)).toContainText('Message 4')
    await expect(conversationListItems.nth(0)).toContainText('Message 5')
  })
  test('verify that a new message in an old conversation updates the timestamp.', async ({
    page
  }) => {
    const messageInputTextArea = page.locator('textarea#message-input')
    const messageInputButton = page.locator('#send-message-button')

    // First conversation
    await messageInputTextArea.fill('Message 1')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)

    //Locate new conversation button
    const openSidebarButton = page.locator('button#open-sidebar')
    await openSidebarButton.click()
    const newConversationButton = page.locator('button#new-conversation')
    await newConversationButton.click()

    // Second conversation
    await messageInputTextArea.fill('Message 2')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Third conversation
    await messageInputTextArea.fill('Message 3')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(2)
    await newConversationButton.click()

    // Verify that three conversations are added to the list
    const conversationListItems = page.locator('li.conversation-item')
    await expect(conversationListItems).toHaveCount(3)
    await expect(conversationListItems.nth(2)).toContainText('Message 1')
    await expect(conversationListItems.nth(1)).toContainText('Message 2')
    await expect(conversationListItems.nth(0)).toContainText('Message 3')

    // Click on the second conversation to load it
    const secondConversationLink = conversationListItems.nth(1).locator('a')
    await secondConversationLink.click()

    await messageInputTextArea.fill('Message 4')
    await messageInputButton.click()
    await expect(page.locator('div.message')).toHaveCount(4)
    await expect(page.locator('div.message').nth(0)).toContainText('Message 2')
    await expect(page.locator('div.message').nth(2)).toContainText('Message 4')

    await expect(conversationListItems).toHaveCount(3)
    await expect(conversationListItems.nth(2)).toContainText('Message 1')
    await expect(conversationListItems.nth(0)).toContainText('Message 2')
    await expect(conversationListItems.nth(1)).toContainText('Message 3')
  })
})
