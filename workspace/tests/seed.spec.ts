import { test, expect } from '@playwright/test';

test.describe('Example Seed Test Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the application', async ({ page }) => {
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('should display main heading', async ({ page }) => {
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });
});
