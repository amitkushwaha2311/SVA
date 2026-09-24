import { test, expect } from '@playwright/test';

test.describe('Landing Page Flow', () => {
  test('unauthenticated user sees public landing page', async ({ page }) => {
    // Navigate to root
    await page.goto('/');

    // Wait for the landing page to load
    await expect(page.locator('text=Software that can prove')).toBeVisible();

    // Verify "Analyze Repository" button links to /login
    const analyzeBtn = page.getByRole('link', { name: 'Analyze Repository' });
    await expect(analyzeBtn).toBeVisible();
    await expect(analyzeBtn).toHaveAttribute('href', '/login');

    // Click it and verify navigation
    await analyzeBtn.click();
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('authenticated user sees empty state or dashboard', async ({ page }) => {
    // 1. Sign up to create a session
    await page.goto('/signup');
    const testEmail = `landing_${Date.now()}@example.com`;
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', 'Password123!');
    const textInputs = await page.locator('input[type="text"]').all();
    await textInputs[0].fill('Jane Landing');
    await textInputs[1].fill('Acme Landing');
    await page.click('button[type="submit"]');

    // 2. Wait for redirect to home
    await page.waitForURL('/');

    // 3. User is authenticated, should see "Analyze Repository" as a BUTTON, not a LINK
    // because they have no repos yet (empty state)
    await expect(page.locator('text=Software that can prove')).toBeVisible();
    
    // The button should be a <button> element, not an <a> tag
    const analyzeBtn = page.getByRole('button', { name: 'Analyze Repository' });
    await expect(analyzeBtn).toBeVisible();

    // Clicking it should open the modal
    await analyzeBtn.click();
    await expect(page.locator('text=Register and analyze a repository')).toBeVisible();

    // Close modal
    await page.locator('button:has-text("Cancel")').click();
  });
});
