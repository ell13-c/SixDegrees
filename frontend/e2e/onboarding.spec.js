import { test, expect } from '@playwright/test';

test.describe('New user onboarding flow', () => {

  test.beforeEach(async ({ page }) => {
    // Clear any stored auth state between tests
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('unauthenticated user redirected from / to /login', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('**/login', { timeout: 5000 });
    await expect(page).toHaveURL(/login/);
  });

  test('unauthenticated user redirected from /profile-setup to /login', async ({ page }) => {
    await page.goto('/profile-setup');
    await page.waitForURL('**/login', { timeout: 5000 });
    await expect(page).toHaveURL(/login/);
  });

  test('signup page loads with email and password fields', async ({ page }) => {
    await page.goto('/signup');
    await expect(page).toHaveURL(/signup/);
    const emailField = page.locator('input[type="email"], input[placeholder*="email" i], input[name="email"]');
    const passwordField = page.locator('input[type="password"]');
    await expect(emailField.first()).toBeVisible({ timeout: 5000 });
    await expect(passwordField.first()).toBeVisible({ timeout: 5000 });
  });

  test('login page loads with email and password fields', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL(/login/);
    const emailField = page.locator('input[type="email"], input[placeholder*="email" i], input[name="email"]');
    const passwordField = page.locator('input[type="password"]');
    await expect(emailField.first()).toBeVisible({ timeout: 5000 });
    await expect(passwordField.first()).toBeVisible({ timeout: 5000 });
  });

  // MANUAL INTEGRATION TEST — requires live Supabase and test credentials in env
  // Enable by setting TEST_EMAIL and TEST_PASSWORD environment variables
  test('full signup to profile setup flow', async ({ page }) => {
    test.skip(!process.env.TEST_EMAIL, 'Set TEST_EMAIL and TEST_PASSWORD to enable');
    const email = process.env.TEST_EMAIL;
    const password = process.env.TEST_PASSWORD;

    await page.goto('/signup');
    await page.locator('input[type="email"]').first().fill(email);
    await page.locator('input[type="password"]').first().fill(password);
    await page.locator('button[type="submit"]').click();

    await page.waitForURL('**/profile-setup', { timeout: 10000 });
    await expect(page).toHaveURL(/profile-setup/);

    const displayNameField = page.locator('input[placeholder*="name" i], input[name="display_name"]');
    if (await displayNameField.count() > 0) {
      await displayNameField.first().fill('Test Playwright User');
    }
    await page.locator('button[type="submit"]').click();

    await page.waitForURL('**/', { timeout: 10000 });
    await expect(page).toHaveURL(/\/$/);
  });

});
