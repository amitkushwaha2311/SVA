import { test, expect } from '@playwright/test';

/**
 * Navigation and Search E2E tests.
 *
 * These tests run against the live dev server (http://localhost:3000).
 * API mocking is used only where the real backend requires authentication.
 *
 * apiFetch(path) → fetch(`/api${path}`)
 *   GET /api/auth/me            → returns User directly
 *   GET /api/v1/workspaces/     → returns { items: Workspace[] }
 *   GET /api/v1/orchestration/repositories?workspace_id=... → { items: Repository[] }
 */

test.describe('Navigation and Search', () => {
  test.beforeEach(async ({ page }) => {
    // Mock auth so we don't need a live session
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'u1', email: 'test@example.com', role: 'admin' })
      });
    });

    // Mock workspaces
    await page.route('**/api/v1/workspaces/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [{ id: 'ws-1', name: 'Default', role: 'admin' }] })
      });
    });
  });

  // ─── Repository Card Navigation ──────────────────────────────────────────────

  test('repository card navigation and external URL', async ({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    // Mock repositories list for the dashboard
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'repo-1',
            name: 'LIFE-OS',
            repository_identifier: 'https://github.com/test/LIFE-OS.git',
            provider_type: 'git',
            created_at: new Date().toISOString()
          }]
        })
      });
    });

    // Mock repository detail
    await page.route('**/api/v1/repositories/repo-1**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'repo-1',
          name: 'LIFE-OS',
          repository_identifier: 'https://github.com/test/LIFE-OS.git',
          source_type: 'git',
          workspace_id: 'ws-1',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
      });
    });

    await page.route('**/api/v1/analyses**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ analyses: [] })
      });
    });

    await page.goto('/');

    // Wait for the Link that wraps the LIFE-OS card content (aria-label set on it)
    const repoCard = page.getByRole('link', { name: /Open LIFE-OS repository/i });
    await expect(repoCard).toBeVisible({ timeout: 10000 });

    // Verify the href is the real repo ID, not hardcoded
    const href = await repoCard.getAttribute('href');
    expect(href).toBe('/repositories/repo-1');

    // Verify bounding box is non-zero (element actually occupies space)
    const box = await repoCard.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThan(0);
    expect(box!.height).toBeGreaterThan(0);

    // Verify no nested <a> tags
    const nestedAnchors = await page.evaluate(() => {
      const allLinks = document.querySelectorAll('a');
      let hasNested = false;
      allLinks.forEach(link => { if (link.querySelector('a')) hasNested = true; });
      return hasNested;
    });
    expect(nestedAnchors).toBe(false);

    // Click navigates to detail page
    await repoCard.click();
    await expect(page).toHaveURL(/\/repositories\/repo-1/, { timeout: 10000 });

    // Detail page renders the repo name
    await expect(page.getByText('LIFE-OS').first()).toBeVisible({ timeout: 10000 });
  });

  // ─── External GitHub URL ─────────────────────────────────────────────────────

  test('external GitHub URL is a separate non-nested link with target=_blank', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'repo-1',
            name: 'LIFE-OS',
            repository_identifier: 'https://github.com/test/LIFE-OS.git',
            provider_type: 'git',
            created_at: new Date().toISOString()
          }]
        })
      });
    });

    await page.goto('/');
    await page.waitForSelector('a[aria-label*="Open LIFE-OS repository"]', { timeout: 10000 });

    const isNested = await page.evaluate(() => {
      const cardLink = document.querySelector('a[aria-label*="Open LIFE-OS repository"]');
      const externalLink = document.querySelector('a[target="_blank"]');
      if (!cardLink || !externalLink) return 'missing-elements';
      if (cardLink.contains(externalLink)) return 'external-inside-card';
      if (externalLink.contains(cardLink)) return 'card-inside-external';
      return 'ok';
    });
    expect(isNested).toBe('ok');

    const externalLink = page.getByRole('link', { name: /Open LIFE-OS on external host/i });
    await expect(externalLink).toBeVisible();
    await expect(externalLink).toHaveAttribute('target', '_blank');
    await expect(externalLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  // ─── TopBar Repository Selector ──────────────────────────────────────────────

  test('Repository selector button opens dropdown with real repo list', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'repo-1',
            name: 'LIFE-OS',
            repository_identifier: 'https://github.com/test/LIFE-OS.git',
            provider_type: 'git',
            created_at: new Date().toISOString()
          }]
        })
      });
    });

    await page.goto('/');

    // The Repository button must be a semantic button
    const repoBtn = page.getByRole('button', { name: /Select repository/i });
    await expect(repoBtn).toBeVisible({ timeout: 10000 });

    // aria-expanded starts false
    await expect(repoBtn).toHaveAttribute('aria-expanded', 'false');

    // Click opens dropdown
    await repoBtn.click();
    await expect(repoBtn).toHaveAttribute('aria-expanded', 'true');

    // Dropdown shows the real repository
    const menuItem = page.getByRole('menuitem', { name: /LIFE-OS/i }).first();
    await expect(menuItem).toBeVisible({ timeout: 5000 });

    // The menu item must be an <a> link to the real repo ID
    const menuHref = await menuItem.getAttribute('href');
    expect(menuHref).toBe('/repositories/repo-1');

    // Pressing Escape closes it
    await page.keyboard.press('Escape');
    await expect(repoBtn).toHaveAttribute('aria-expanded', 'false');
  });

  test('Repository selector navigates to repo detail on click', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [{
            id: 'repo-1',
            name: 'LIFE-OS',
            repository_identifier: 'https://github.com/test/LIFE-OS.git',
            provider_type: 'git',
            created_at: new Date().toISOString()
          }]
        })
      });
    });

    await page.route('**/api/v1/repositories/repo-1**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'repo-1', name: 'LIFE-OS',
          repository_identifier: 'https://github.com/test/LIFE-OS.git',
          source_type: 'git', workspace_id: 'ws-1',
          created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
        })
      });
    });

    await page.route('**/api/v1/analyses**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ analyses: [] }) });
    });

    await page.goto('/');

    const repoBtn = page.getByRole('button', { name: /Select repository/i });
    await expect(repoBtn).toBeVisible({ timeout: 10000 });
    await repoBtn.click();

    const menuItem = page.getByRole('menuitem', { name: /LIFE-OS/i }).first();
    await expect(menuItem).toBeVisible({ timeout: 5000 });
    await menuItem.click();

    await expect(page).toHaveURL(/\/repositories\/repo-1/, { timeout: 10000 });
    await expect(page.getByText('LIFE-OS').first()).toBeVisible({ timeout: 10000 });
  });

  // ─── Global Search ──────────────────────────────────────────────────────────

  test('Search button (click) opens command palette with input', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: [] })
      });
    });

    await page.goto('/');
    // Wait for HMR to settle fully before interacting
    await page.waitForLoadState('networkidle');

    // The Search button must be a semantic button visible at desktop width
    const searchBtn = page.getByRole('button', { name: /Open search/i });
    await expect(searchBtn).toBeVisible({ timeout: 10000 });

    // Use force:true to bypass any transient re-render
    await searchBtn.click({ force: true });

    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await expect(searchInput).toBeFocused();

    // Escape closes the palette
    await page.keyboard.press('Escape');
    await expect(searchInput).not.toBeVisible({ timeout: 3000 });
  });

  test('Ctrl+K opens command palette with input', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [] }) });
    });

    await page.goto('/');
    // Wait for HMR and React to fully initialize before sending keyboard events
    await page.waitForLoadState('networkidle');
    // Give React event listener time to register
    await page.waitForTimeout(500);

    await page.keyboard.press('Control+k');

    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await expect(searchInput).toBeFocused();
  });

  test('Search uses real backend API with workspace_id', async ({ page }) => {
    await page.route('**/api/v1/orchestration/repositories**', async route => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [] }) });
    });

    let capturedSearchUrl: string | null = null;
    await page.route('**/api/v1/search**', async route => {
      capturedSearchUrl = route.request().url();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [{
            id: 'repo-1', type: 'repository', label: 'LIFE-OS', href: '/repositories/repo-1'
          }]
        })
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Open search via button
    const searchBtn = page.getByRole('button', { name: /Open search/i });
    await expect(searchBtn).toBeVisible({ timeout: 10000 });
    await searchBtn.click({ force: true });

    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });

    // Type a query to trigger the real API call
    await searchInput.fill('LIFE-OS');

    // Wait for search results to appear
    await expect(page.getByText('LIFE-OS').first()).toBeVisible({ timeout: 5000 });

    // Verify the search request included workspace_id and query
    expect(capturedSearchUrl).not.toBeNull();
    const url = new URL(capturedSearchUrl!);
    expect(url.searchParams.get('workspace_id')).toBe('ws-1');
    expect(url.searchParams.get('q')).toBe('LIFE-OS');
  });
});
