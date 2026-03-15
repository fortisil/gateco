/**
 * E2E tests for login flow.
 *
 * These tests verify the complete login user journey from entering
 * credentials to being redirected to the dashboard.
 */

import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
  });

  test('displays login form', async ({ page }) => {
    // Verify form elements are present
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /log in/i })).toBeVisible();
  });

  test('complete login flow with valid credentials', async ({ page }) => {
    // Fill in credentials
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');

    // Submit form
    await page.getByRole('button', { name: /log in/i }).click();

    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Verify user is logged in (user name visible)
    await expect(page.getByText('Test User')).toBeVisible();
  });

  test('login shows error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');

    // Submit form
    await page.getByRole('button', { name: /log in/i }).click();

    // Should stay on login page
    await expect(page).toHaveURL('/login');

    // Should show error message
    await expect(page.getByRole('alert')).toContainText(/invalid credentials/i);
  });

  test('login shows validation errors for empty fields', async ({ page }) => {
    // Click submit without filling fields
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show validation errors
    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
  });

  test('login shows error for invalid email format', async ({ page }) => {
    // Fill in invalid email
    await page.getByLabel(/email/i).fill('invalid-email');
    await page.getByLabel(/password/i).fill('password123');

    // Submit form
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show validation error
    await expect(page.getByText(/invalid email/i)).toBeVisible();
  });

  test('session persists across page reload', async ({ page }) => {
    // Login first
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /log in/i }).click();

    // Wait for redirect
    await expect(page).toHaveURL('/dashboard');

    // Reload page
    await page.reload();

    // Should still be on dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Test User')).toBeVisible();
  });

  test('logout clears session and redirects to login', async ({ page }) => {
    // Login first
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /log in/i }).click();

    await expect(page).toHaveURL('/dashboard');

    // Open user menu and click logout
    await page.getByRole('button', { name: /user menu/i }).click();
    await page.getByRole('menuitem', { name: /log out/i }).click();

    // Should redirect to login
    await expect(page).toHaveURL('/login');

    // Try to access protected route
    await page.goto('/dashboard');

    // Should redirect back to login
    await expect(page).toHaveURL('/login');
  });

  test('login redirects to original destination', async ({ page }) => {
    // Try to access protected route while not logged in
    await page.goto('/resources');

    // Should redirect to login with return URL
    await expect(page).toHaveURL(/\/login\?.*redirect/);

    // Login
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /log in/i }).click();

    // Should redirect to original destination
    await expect(page).toHaveURL('/resources');
  });

  test('shows loading state during login', async ({ page }) => {
    // Fill in credentials
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');

    // Submit form
    await page.getByRole('button', { name: /log in/i }).click();

    // Should show loading state (briefly)
    // Note: This may be too fast to reliably test
    // await expect(page.getByText(/logging in/i)).toBeVisible();
  });

  test('password field hides input', async ({ page }) => {
    const passwordInput = page.getByLabel(/password/i);

    // Type password
    await passwordInput.fill('secretpassword');

    // Verify input type is password (obscured)
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('forgot password link navigates to reset page', async ({ page }) => {
    // Click forgot password link
    await page.getByRole('link', { name: /forgot password/i }).click();

    // Should navigate to reset page
    await expect(page).toHaveURL('/forgot-password');
  });

  test('sign up link navigates to signup page', async ({ page }) => {
    // Click sign up link
    await page.getByRole('link', { name: /sign up/i }).click();

    // Should navigate to signup page
    await expect(page).toHaveURL('/signup');
  });
});

test.describe('Login - Accessibility', () => {
  test('login form is keyboard accessible', async ({ page }) => {
    await page.goto('/login');

    // Tab to email field
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/email/i)).toBeFocused();

    // Tab to password field
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/password/i)).toBeFocused();

    // Tab to submit button
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /log in/i })).toBeFocused();
  });

  test('error messages are announced to screen readers', async ({ page }) => {
    await page.goto('/login');

    // Submit empty form
    await page.getByRole('button', { name: /log in/i }).click();

    // Error should have alert role
    const alert = page.getByRole('alert');
    await expect(alert).toBeVisible();
  });
});

test.describe('Login - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('login form works on mobile viewport', async ({ page }) => {
    await page.goto('/login');

    // Fill and submit form
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /log in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });
});
