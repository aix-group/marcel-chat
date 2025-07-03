import { test, expect } from '@playwright/test'
import { setupApiMocks } from './utils'

const BASE_URL = 'http://localhost:5173'

test.describe('Consent dialog', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
    await page.goto(BASE_URL)
  })

  test('consent dialog shows on first use', async ({ page }) => {
    const dialog = page.getByTestId('consent-dialog')
    await expect(dialog).toBeVisible()
    await page.getByTestId('consent-submit-button').click()
    const successMessage = page.getByTestId('consent-success')
    await expect(successMessage).toBeVisible()

    await page.reload()
    await expect(dialog).toHaveCount(0)

    const welcomeMessage = page.getByTestId('welcome-message')
    await expect(welcomeMessage).toBeVisible()
  })

  test('consent can be declined and accepted', async ({ page }) => {
    const dialog = page.getByTestId('consent-dialog')
    await expect(dialog).toBeVisible()

    await page.getByTestId('consent-decline-button').click()
    const declinedMessage = page.getByTestId('consent-declined')
    await expect(declinedMessage).toBeVisible()

    await page.getByTestId('consent-submit-button').click()
    const successMessage = page.getByTestId('consent-success')
    await expect(successMessage).toBeVisible()

    await page.reload()
    await expect(dialog).toHaveCount(0)

    const welcomeMessage = page.getByTestId('welcome-message')
    await expect(welcomeMessage).toBeVisible()
  })
})
