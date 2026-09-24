import { test, expect } from '@playwright/test';

test('diagnose workspace 403', async ({ page }) => {
  // 1. Sign up
  await page.goto('/signup');
  const testEmail = `workspace_${Date.now()}@example.com`;
  await page.fill('input[type="email"]', testEmail);
  await page.fill('input[type="password"]', 'Password123!');
  const textInputs = await page.locator('input[type="text"]').all();
  await textInputs[0].fill('Jane Workspace');
  await textInputs[1].fill('Acme Workspace');
  await page.click('button[type="submit"]');

  // 2. Wait for home
  await page.waitForURL('/');

  // 3. Open Analyze Modal
  const analyzeBtn = page.getByRole('button', { name: 'Analyze Repository' });
  await expect(analyzeBtn).toBeVisible();
  await analyzeBtn.click();

  // 4. Fill modal and submit
  await page.fill('input[placeholder="https://github.com/org/repo"]', 'https://github.com/amitkushwaha2311/LIFE-OS.git');
  await page.click('button:has-text("Start Analysis")');

  // 5. Watch network requests
  const response = await page.waitForResponse(response => response.url().includes('/repositories') && response.request().method() === 'POST');
  const status = response.status();
  const body = await response.json().catch(() => null);
  
  console.log(`POST /repositories -> Status: ${status}`);
  console.log(`Body: ${JSON.stringify(body)}`);

  const requestPostData = response.request().postData();
  console.log(`Request payload: ${requestPostData}`);
  
  // Also check /v1/workspaces/
  const workspacesResponse = await page.evaluate(async () => {
    const res = await fetch('/api/v1/workspaces/');
    return res.json();
  });
  console.log(`GET /v1/workspaces/ -> ${JSON.stringify(workspacesResponse)}`);
});
