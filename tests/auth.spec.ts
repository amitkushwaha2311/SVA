import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  const timestamp = Date.now();
  const email = `testuser_${timestamp}@example.com`;
  const password = 'Password123!';
  const wrongPassword = 'WrongPassword123!';
  const unknownEmail = `unknown_${timestamp}@example.com`;

  test.beforeEach(async ({ page }) => {
    // Clear cookies before each test just in case
    await page.context().clearCookies();
  });

  test('successful signup and login, refresh persistence, logout', async ({ page }) => {
    // 1. Signup
    await page.goto('/signup');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    
    // Fill other fields if present
    const textInputs = await page.locator('input[type="text"]').all();
    if (textInputs.length >= 2) {
      await textInputs[0].fill('Test User');
      await textInputs[1].fill('Test Workspace');
    } else if (textInputs.length === 1) {
      await textInputs[0].fill('Test User');
    }

    await page.click('button[type="submit"]');
    
    // Should be redirected to home
    await expect(page).toHaveURL('/');
    
    // Verify session cookie creation via context
    const cookiesAfterSignup = await page.context().cookies();
    const sessionCookie = cookiesAfterSignup.find(c => c.name === 'session');
    expect(sessionCookie).toBeDefined();
    expect(sessionCookie?.httpOnly).toBeTruthy();
    
    // 2. Refresh/session persistence
    await page.reload();
    await expect(page).toHaveURL('/');

    // 3. Logout
    // There isn't an explicit logout button in the test yet, so we'll simulate API call or click the UI if it exists
    // We'll just call the logout API directly for now
    const csrfCookie = cookiesAfterSignup.find(c => c.name === 'csrf_token' || c.name === '__Host-csrf');
    const csrfToken = csrfCookie?.value || '';
    
    const logoutRes = await page.request.post('/api/auth/logout', {
      headers: { 'X-CSRF-Token': csrfToken }
    });
    expect(logoutRes.status()).toBe(204);
    
    await page.reload();
    // Unauthenticated user is redirected, or first-run shows. But wait, if they don't have workspaces it might show first run.
    // Let's actually test login.

    // 4. Successful login
    await page.goto('/login');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/');
    const cookiesAfterLogin = await page.context().cookies();
    expect(cookiesAfterLogin.find(c => c.name === 'session')).toBeDefined();
    
    // /auth/me after login
    const meRes = await page.request.get('/api/auth/me');
    expect(meRes.status()).toBe(200);
  });

  test('invalid password', async ({ page }) => {
    // Attempt to login with unknown user (created in previous test)
    // Wait, tests might run in parallel, we need to create one if it doesn't exist, or just use the same
    
    await page.goto('/login');
    // Using a new user that doesn't exist yet for "unknown user"
    await page.fill('input[type="email"]', unknownEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    
    await expect(page.locator('p.text-\\[\\#EF4444\\]')).toContainText('Invalid email or password');

    // Wait, invalid password on existing user
    // To ensure user exists, we can sign them up via API first
    const setupEmail = `setup_${Date.now()}@example.com`;
    await page.request.post('/api/auth/signup', {
      data: {
        email: setupEmail,
        password: password,
        display_name: 'Setup User',
        workspace_name: 'Setup WS'
      }
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', setupEmail);
    await page.fill('input[type="password"]', wrongPassword);
    await page.click('button[type="submit"]');
    
    await expect(page.locator('p.text-\\[\\#EF4444\\]')).toContainText('Invalid email or password');
  });

  test('unknown user', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', `random_${Date.now()}@example.com`);
    await page.fill('input[type="password"]', 'Whatever123!');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('p.text-\\[\\#EF4444\\]')).toContainText('Invalid email or password');
  });
});
