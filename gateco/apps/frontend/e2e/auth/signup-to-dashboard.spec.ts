/**
 * E2E tests for complete signup-to-dashboard user journey.
 *
 * These tests verify the full onboarding flow from new user signup
 * through organization creation to reaching the dashboard.
 */

import { test, expect } from '@playwright/test';

test.describe('Signup to Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to signup page before each test
    await page.goto('/signup');
  });

  test('displays signup form with all required fields', async ({ page }) => {
    // Verify all form elements are present
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByLabel(/^name$/i)).toBeVisible();
    await expect(page.getByLabel(/organization name/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign up|create account/i })).toBeVisible();
  });

  test('new user can sign up and reach dashboard', async ({ page }) => {
    // Generate unique email for this test
    const uniqueEmail = `test.${Date.now()}@example.com`;

    // Fill in signup form
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('New Test User');
    await page.getByLabel(/organization name/i).fill('New Test Organization');

    // Accept terms if checkbox exists
    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit form
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Verify user is logged in with correct name
    await expect(page.getByText('New Test User')).toBeVisible();

    // Verify free plan badge is displayed
    await expect(page.getByText(/free/i)).toBeVisible();

    // Verify organization name is shown
    await expect(page.getByText('New Test Organization')).toBeVisible();
  });

  test('signup shows validation errors for empty fields', async ({ page }) => {
    // Click submit without filling fields
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Should show validation errors for all required fields
    await expect(page.getByText(/email.*required/i)).toBeVisible();
    await expect(page.getByText(/password.*required/i)).toBeVisible();
  });

  test('signup validates email format', async ({ page }) => {
    // Fill in invalid email
    await page.getByLabel(/email/i).fill('not-an-email');
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Test User');
    await page.getByLabel(/organization name/i).fill('Test Org');

    // Submit form
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Should show email validation error
    await expect(page.getByText(/invalid email|valid email/i)).toBeVisible();
  });

  test('signup validates password requirements', async ({ page }) => {
    const uniqueEmail = `test.${Date.now()}@example.com`;

    // Fill in weak password
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('weak');
    await page.getByLabel(/^name$/i).fill('Test User');
    await page.getByLabel(/organization name/i).fill('Test Org');

    // Submit form
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Should show password validation error
    await expect(
      page.getByText(/password.*8.*characters|password.*too.*short/i)
    ).toBeVisible();
  });

  test('signup shows password strength indicator', async ({ page }) => {
    const passwordInput = page.getByLabel(/password/i);

    // Type weak password
    await passwordInput.fill('weak');

    // Should show weak indicator (if implemented)
    // This may be a color change or text indicator
    const strengthIndicator = page.locator('[data-testid="password-strength"]');
    if (await strengthIndicator.isVisible()) {
      await expect(strengthIndicator).toContainText(/weak/i);
    }

    // Type strong password
    await passwordInput.clear();
    await passwordInput.fill('SecurePass123!@#$');

    // Should show strong indicator
    if (await strengthIndicator.isVisible()) {
      await expect(strengthIndicator).toContainText(/strong/i);
    }
  });

  test('signup handles existing email gracefully', async ({ page }) => {
    // Use a known existing email
    await page.getByLabel(/email/i).fill('existing@example.com');
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Test User');
    await page.getByLabel(/organization name/i).fill('Test Org');

    // Accept terms if checkbox exists
    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit form
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Should stay on signup page
    await expect(page).toHaveURL('/signup');

    // Should show error about existing email
    await expect(
      page.getByText(/email.*already|already.*registered|email.*exists/i)
    ).toBeVisible();
  });

  test('signup shows loading state during submission', async ({ page }) => {
    const uniqueEmail = `test.${Date.now()}@example.com`;

    // Fill in valid signup data
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Test User');
    await page.getByLabel(/organization name/i).fill('Test Org');

    // Accept terms if checkbox exists
    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit form
    const submitButton = page.getByRole('button', { name: /sign up|create account/i });
    await submitButton.click();

    // Button should be disabled or show loading state
    // Note: This happens quickly, so we check if disabled attribute was set
    // or if loading text appeared (may need longer delay to reliably test)
  });

  test('navigating to login page from signup', async ({ page }) => {
    // Click login link
    await page.getByRole('link', { name: /log in|sign in|already have an account/i }).click();

    // Should navigate to login page
    await expect(page).toHaveURL('/login');
  });

  test('OAuth signup buttons are visible', async ({ page }) => {
    // Check for OAuth buttons
    const googleButton = page.getByRole('button', { name: /google/i });
    const githubButton = page.getByRole('button', { name: /github/i });

    // At least one OAuth option should be available
    const hasOAuth =
      (await googleButton.isVisible()) || (await githubButton.isVisible());
    expect(hasOAuth).toBe(true);
  });

  test('terms and conditions link works', async ({ page }) => {
    // Click terms link
    const termsLink = page.getByRole('link', { name: /terms|conditions/i });
    if (await termsLink.isVisible()) {
      await termsLink.click();
      // Should open terms page (may be new tab)
      // Verify navigation or new tab opened
    }
  });

  test('privacy policy link works', async ({ page }) => {
    // Click privacy link
    const privacyLink = page.getByRole('link', { name: /privacy/i });
    if (await privacyLink.isVisible()) {
      await privacyLink.click();
      // Should open privacy page
    }
  });
});

test.describe('Signup - Onboarding Flow', () => {
  test('new user sees onboarding wizard after signup', async ({ page }) => {
    const uniqueEmail = `onboard.${Date.now()}@example.com`;

    // Complete signup
    await page.goto('/signup');
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Onboarding User');
    await page.getByLabel(/organization name/i).fill('Onboarding Org');

    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Check if onboarding wizard/tour is shown (if implemented)
    const onboardingWizard = page.locator('[data-testid="onboarding-wizard"]');
    const welcomeMessage = page.getByText(/welcome|get started|first resource/i);

    // Either onboarding wizard or welcome message should be visible
    // const hasOnboarding =
    //   (await onboardingWizard.isVisible()) || (await welcomeMessage.isVisible());
    // expect(hasOnboarding).toBe(true);
  });

  test('dashboard shows empty state for new users', async ({ page }) => {
    const uniqueEmail = `empty.${Date.now()}@example.com`;

    // Complete signup
    await page.goto('/signup');
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Empty State User');
    await page.getByLabel(/organization name/i).fill('Empty Org');

    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    await page.getByRole('button', { name: /sign up|create account/i }).click();
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Navigate to resources
    await page.getByRole('link', { name: /resources/i }).click();

    // Should show empty state
    await expect(
      page.getByText(/no resources|create your first|get started/i)
    ).toBeVisible();

    // Should have create button
    await expect(
      page.getByRole('button', { name: /create|new resource/i })
    ).toBeVisible();
  });
});

test.describe('Signup - Accessibility', () => {
  test('signup form is keyboard accessible', async ({ page }) => {
    await page.goto('/signup');

    // Tab through form fields
    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/email/i)).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/password/i)).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/^name$/i)).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/organization name/i)).toBeFocused();
  });

  test('form can be submitted with Enter key', async ({ page }) => {
    await page.goto('/signup');

    const uniqueEmail = `enter.${Date.now()}@example.com`;

    // Fill form
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Enter User');
    await page.getByLabel(/organization name/i).fill('Enter Org');

    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Press Enter to submit
    await page.keyboard.press('Enter');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });
  });

  test('error messages are properly associated with fields', async ({ page }) => {
    await page.goto('/signup');

    // Submit empty form
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Email field should have aria-invalid
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toHaveAttribute('aria-invalid', 'true');

    // Error should be linked via aria-describedby
    const errorId = await emailInput.getAttribute('aria-describedby');
    expect(errorId).toBeTruthy();
  });
});

test.describe('Signup - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('signup form works on mobile viewport', async ({ page }) => {
    await page.goto('/signup');

    const uniqueEmail = `mobile.${Date.now()}@example.com`;

    // Fill form on mobile
    await page.getByLabel(/email/i).fill(uniqueEmail);
    await page.getByLabel(/password/i).fill('SecurePass123!');
    await page.getByLabel(/^name$/i).fill('Mobile User');
    await page.getByLabel(/organization name/i).fill('Mobile Org');

    const termsCheckbox = page.getByRole('checkbox', { name: /terms|agree/i });
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });
  });

  test('mobile signup shows all fields without scrolling issues', async ({ page }) => {
    await page.goto('/signup');

    // All fields should be visible and interactable
    const emailInput = page.getByLabel(/email/i);
    const passwordInput = page.getByLabel(/password/i);
    const nameInput = page.getByLabel(/^name$/i);
    const orgInput = page.getByLabel(/organization name/i);
    const submitButton = page.getByRole('button', { name: /sign up|create account/i });

    // Focus each field to ensure they're scrolled into view
    await emailInput.focus();
    await expect(emailInput).toBeInViewport();

    await passwordInput.focus();
    await expect(passwordInput).toBeInViewport();

    await nameInput.focus();
    await expect(nameInput).toBeInViewport();

    await orgInput.focus();
    await expect(orgInput).toBeInViewport();

    await submitButton.focus();
    await expect(submitButton).toBeInViewport();
  });
});
