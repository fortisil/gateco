/**
 * Authentication fixtures for E2E tests.
 *
 * Provides helper functions for common authentication operations
 * in E2E tests.
 */

import { Page, expect } from '@playwright/test';

/**
 * Test user credentials.
 */
export const testUsers = {
  owner: {
    email: 'owner@example.com',
    password: 'TestPass123!',
    name: 'Test Owner',
    role: 'owner' as const,
  },
  admin: {
    email: 'admin@example.com',
    password: 'TestPass123!',
    name: 'Test Admin',
    role: 'admin' as const,
  },
  member: {
    email: 'member@example.com',
    password: 'TestPass123!',
    name: 'Test Member',
    role: 'member' as const,
  },
  freeUser: {
    email: 'free@example.com',
    password: 'TestPass123!',
    name: 'Free User',
    role: 'owner' as const,
    plan: 'free' as const,
  },
  proUser: {
    email: 'pro@example.com',
    password: 'TestPass123!',
    name: 'Pro User',
    role: 'owner' as const,
    plan: 'pro' as const,
  },
};

/**
 * Login as a user via the UI.
 *
 * @param page - Playwright page
 * @param email - User email
 * @param password - User password
 */
export async function loginAsUser(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  await page.goto('/login');

  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /log in/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
}

/**
 * Login as test owner user.
 */
export async function loginAsOwner(page: Page): Promise<void> {
  await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
}

/**
 * Login as test admin user.
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await loginAsUser(page, testUsers.admin.email, testUsers.admin.password);
}

/**
 * Login as test member user.
 */
export async function loginAsMember(page: Page): Promise<void> {
  await loginAsUser(page, testUsers.member.email, testUsers.member.password);
}

/**
 * Logout the current user.
 */
export async function logout(page: Page): Promise<void> {
  await page.getByRole('button', { name: /user menu/i }).click();
  await page.getByRole('menuitem', { name: /log out/i }).click();

  // Wait for redirect to login
  await expect(page).toHaveURL('/login');
}

/**
 * Sign up a new user via the UI.
 *
 * @param page - Playwright page
 * @param userData - User data for signup
 */
export async function signupUser(
  page: Page,
  userData: {
    email: string;
    password: string;
    name: string;
    organizationName: string;
  }
): Promise<void> {
  await page.goto('/signup');

  await page.getByLabel(/email/i).fill(userData.email);
  await page.getByLabel(/password/i).first().fill(userData.password);
  await page.getByLabel(/confirm password/i).fill(userData.password);
  await page.getByLabel(/name/i).fill(userData.name);
  await page.getByLabel(/organization/i).fill(userData.organizationName);

  await page.getByRole('button', { name: /sign up/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL('/dashboard');
}

/**
 * Check if user is logged in.
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    await page.goto('/dashboard');
    await page.waitForURL('/dashboard', { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Ensure user is logged out before test.
 */
export async function ensureLoggedOut(page: Page): Promise<void> {
  // Try to access dashboard
  await page.goto('/dashboard');

  // If we're redirected to login, we're logged out
  const url = page.url();
  if (!url.includes('/login')) {
    // We're logged in, so logout
    await logout(page);
  }
}

/**
 * Get authentication token from storage (for API calls).
 */
export async function getAuthToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return localStorage.getItem('access_token');
  });
}

/**
 * Set authentication token in storage.
 */
export async function setAuthToken(
  page: Page,
  token: string
): Promise<void> {
  await page.evaluate((t) => {
    localStorage.setItem('access_token', t);
  }, token);
}

/**
 * Clear authentication tokens from storage.
 */
export async function clearAuthTokens(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  });
}
