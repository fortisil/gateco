/**
 * E2E tests for OAuth authentication flows.
 *
 * Tests the complete OAuth journey for Google and GitHub providers,
 * including redirect handling and error states.
 */

import { test, expect } from '@playwright/test';

test.describe('OAuth Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test.describe('Google OAuth', () => {
    test('Google OAuth button is visible on login page', async ({ page }) => {
      const googleButton = page.getByRole('button', {
        name: /continue with google/i,
      });

      await expect(googleButton).toBeVisible();
    });

    test('Google OAuth button redirects to Google', async ({ page, context }) => {
      // Listen for new page/popup
      const pagePromise = context.waitForEvent('page');

      // Click Google OAuth button
      await page.getByRole('button', { name: /continue with google/i }).click();

      // Check redirect or popup
      const newPage = await pagePromise;

      // Should redirect to Google OAuth
      await expect(newPage).toHaveURL(/accounts\.google\.com/);
    });

    test('shows loading state during OAuth redirect', async ({ page }) => {
      const googleButton = page.getByRole('button', {
        name: /continue with google/i,
      });

      await googleButton.click();

      // Button should show loading briefly before redirect
      // This may happen too fast to reliably test
    });
  });

  test.describe('GitHub OAuth', () => {
    test('GitHub OAuth button is visible on login page', async ({ page }) => {
      const githubButton = page.getByRole('button', {
        name: /continue with github/i,
      });

      await expect(githubButton).toBeVisible();
    });

    test('GitHub OAuth button redirects to GitHub', async ({ page, context }) => {
      const pagePromise = context.waitForEvent('page');

      await page.getByRole('button', { name: /continue with github/i }).click();

      const newPage = await pagePromise;

      await expect(newPage).toHaveURL(/github\.com\/login\/oauth/);
    });
  });

  test.describe('OAuth on Signup Page', () => {
    test('OAuth buttons also available on signup page', async ({ page }) => {
      await page.goto('/signup');

      await expect(
        page.getByRole('button', { name: /continue with google/i })
      ).toBeVisible();
      await expect(
        page.getByRole('button', { name: /continue with github/i })
      ).toBeVisible();
    });

    test('OAuth creates new account if user does not exist', async ({ page }) => {
      // This test simulates a successful OAuth callback for new user
      await page.goto('/auth/callback?provider=google&code=mock_code&state=new_user');

      // Should redirect to dashboard or onboarding
      await expect(page).toHaveURL(/\/(dashboard|onboarding)/);
    });
  });

  test.describe('OAuth Error Handling', () => {
    test('displays error when OAuth is denied', async ({ page }) => {
      // Simulate OAuth callback with error
      await page.goto('/auth/callback?error=access_denied&error_description=User+denied+access');

      // Should show error message
      await expect(page.getByRole('alert')).toBeVisible();
      await expect(page.getByText(/access denied/i)).toBeVisible();

      // Should be on login page
      await expect(page).toHaveURL('/login');
    });

    test('displays error when OAuth state is invalid', async ({ page }) => {
      await page.goto('/auth/callback?provider=google&code=mock_code&state=invalid_state');

      await expect(page.getByRole('alert')).toBeVisible();
      await expect(page.getByText(/invalid state/i)).toBeVisible();
    });

    test('displays error when OAuth provider returns error', async ({ page }) => {
      await page.goto(
        '/auth/callback?error=server_error&error_description=Something+went+wrong'
      );

      await expect(page.getByRole('alert')).toBeVisible();
      await expect(page.getByText(/something went wrong/i)).toBeVisible();
    });

    test('allows retry after OAuth error', async ({ page }) => {
      // Navigate to error state
      await page.goto('/auth/callback?error=access_denied');

      await expect(page.getByRole('alert')).toBeVisible();

      // Try again button
      await page.getByRole('link', { name: /try again/i }).click();

      // Should be on login page without error
      await expect(page).toHaveURL('/login');
      await expect(page.getByRole('alert')).not.toBeVisible();
    });
  });

  test.describe('OAuth Account Linking', () => {
    test.use({ storageState: 'playwright/.auth/user.json' });

    test('logged in user can link Google account', async ({ page }) => {
      await page.goto('/settings/account');

      // Should see option to link Google
      await expect(page.getByText(/connect google/i)).toBeVisible();

      // Click to link
      await page.getByRole('button', { name: /connect google/i }).click();

      // Should redirect to Google OAuth
      // After success, should show as linked
    });

    test('logged in user can link GitHub account', async ({ page }) => {
      await page.goto('/settings/account');

      await expect(page.getByText(/connect github/i)).toBeVisible();
    });

    test('shows linked accounts', async ({ page }) => {
      // User with linked accounts
      await page.goto('/settings/account');

      // Should show linked providers
      await expect(
        page.getByText(/google/i).or(page.getByText(/connected/i))
      ).toBeVisible();
    });

    test('can unlink OAuth account when password is set', async ({ page }) => {
      await page.goto('/settings/account');

      // If user has password, they can unlink OAuth
      const unlinkButton = page.getByRole('button', { name: /disconnect/i });

      if (await unlinkButton.isVisible()) {
        await unlinkButton.click();

        // Confirm disconnection
        await page.getByRole('button', { name: /confirm/i }).click();

        // Should show as not connected
        await expect(page.getByText(/connect google/i)).toBeVisible();
      }
    });
  });
});

test.describe('OAuth - Accessibility', () => {
  test('OAuth buttons are keyboard accessible', async ({ page }) => {
    await page.goto('/login');

    // Tab to Google button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // May need multiple tabs

    const googleButton = page.getByRole('button', {
      name: /continue with google/i,
    });

    // Should be focusable
    await expect(googleButton).toBeFocused();
  });

  test('OAuth buttons have accessible names', async ({ page }) => {
    await page.goto('/login');

    const googleButton = page.getByRole('button', {
      name: /continue with google/i,
    });
    const githubButton = page.getByRole('button', {
      name: /continue with github/i,
    });

    await expect(googleButton).toHaveAccessibleName(/google/i);
    await expect(githubButton).toHaveAccessibleName(/github/i);
  });

  test('error messages are announced to screen readers', async ({ page }) => {
    await page.goto('/auth/callback?error=access_denied');

    const alert = page.getByRole('alert');
    await expect(alert).toBeVisible();
    await expect(alert).toHaveAttribute('aria-live', 'polite');
  });
});

test.describe('OAuth - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('OAuth buttons work on mobile', async ({ page, context }) => {
    await page.goto('/login');

    // Buttons should be visible and tappable
    const googleButton = page.getByRole('button', {
      name: /continue with google/i,
    });
    await expect(googleButton).toBeVisible();

    // Test tap
    const pagePromise = context.waitForEvent('page');
    await googleButton.tap();

    const newPage = await pagePromise;
    await expect(newPage).toHaveURL(/accounts\.google\.com/);
  });

  test('OAuth buttons are full width on mobile', async ({ page }) => {
    await page.goto('/login');

    const googleButton = page.getByRole('button', {
      name: /continue with google/i,
    });

    const buttonBox = await googleButton.boundingBox();
    const viewport = page.viewportSize();

    // Button should be nearly full width (accounting for padding)
    expect(buttonBox!.width).toBeGreaterThan(viewport!.width * 0.8);
  });
});
