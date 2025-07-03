import { test, expect } from '@playwright/test'
import { giveConsent } from './utils'

const BASE_URL = 'http://localhost:5173'

test('should show 404 page on invalid path', async ({ page }) => {
  await page.goto(BASE_URL)
  await giveConsent(page)
  await expect(page.getByTestId('welcome-message')).toBeVisible()
  await page.goto(`${BASE_URL}/doesnotexist`)
  await expect(page.getByTestId('pathNotFoundMessage')).toBeVisible()
  await page.getByText('Back to Homepage').click()
  await expect(page.getByTestId('welcome-message')).toBeVisible()
})
