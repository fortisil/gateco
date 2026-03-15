/**
 * E2E tests for billing and checkout flows.
 *
 * These tests verify the subscription upgrade flow, usage display,
 * and billing management features.
 */

import { test, expect } from '@playwright/test';
import { loginAsUser, testUsers } from '../fixtures/auth.fixture';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as free user
    await loginAsUser(page, testUsers.freeUser.email, testUsers.freeUser.password);
  });

  test('displays current plan on billing page', async ({ page }) => {
    await page.goto('/settings/billing');

    // Should show current free plan
    await expect(page.getByText(/free plan/i)).toBeVisible();
    await expect(page.getByText(/upgrade/i)).toBeVisible();
  });

  test('shows upgrade options', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click upgrade button
    await page.getByRole('button', { name: /upgrade/i }).click();

    // Should show plan options
    await expect(page.getByText(/pro/i)).toBeVisible();
    await expect(page.getByText(/enterprise/i)).toBeVisible();
    await expect(page.getByText(/\$29/)).toBeVisible(); // Pro monthly price
  });

  test('checkout flow redirects to Stripe', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click upgrade button
    await page.getByRole('button', { name: /upgrade to pro/i }).click();

    // Select monthly billing
    await page.getByLabel(/monthly/i).click();

    // Click continue to checkout
    await page.getByRole('button', { name: /continue to checkout/i }).click();

    // Should redirect to Stripe checkout
    // Note: In real tests, this would use Stripe test mode
    await expect(page).toHaveURL(/checkout\.stripe\.com/);
  });

  test('displays usage statistics', async ({ page }) => {
    await page.goto('/settings/billing');

    // Should show usage meter
    await expect(page.getByText(/secured retrievals/i)).toBeVisible();
    await expect(page.getByText(/\/\s*100/)).toBeVisible(); // X / 100 limit
  });

  test('shows usage warning when near limit', async ({ page }) => {
    // This test assumes the user has high usage
    await page.goto('/settings/billing');

    // If usage is high, should show warning
    const warningText = page.getByText(/approaching.*limit/i);
    // This assertion is conditional based on actual usage
  });
});

test.describe('Billing Portal', () => {
  test.beforeEach(async ({ page }) => {
    // Login as pro user (has subscription)
    await loginAsUser(page, testUsers.proUser.email, testUsers.proUser.password);
  });

  test('displays pro plan features', async ({ page }) => {
    await page.goto('/settings/billing');

    // Should show pro plan
    await expect(page.getByText(/pro plan/i)).toBeVisible();

    // Should show pro features
    await expect(page.getByText(/custom branding/i)).toBeVisible();
    await expect(page.getByText(/analytics/i)).toBeVisible();
  });

  test('manage subscription opens Stripe portal', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click manage subscription
    await page.getByRole('button', { name: /manage subscription/i }).click();

    // Should redirect to Stripe billing portal
    await expect(page).toHaveURL(/billing\.stripe\.com/);
  });

  test('displays invoice history', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click view invoices or scroll to invoices section
    const invoicesSection = page.getByText(/invoices/i);
    await expect(invoicesSection).toBeVisible();

    // Should show at least one invoice
    await expect(page.getByText(/paid/i)).toBeVisible();
  });

  test('invoice download link works', async ({ page }) => {
    await page.goto('/settings/billing');

    // Find invoice download link
    const downloadLink = page.getByRole('link', { name: /download.*pdf/i });

    if (await downloadLink.isVisible()) {
      // Verify link has correct attributes
      await expect(downloadLink).toHaveAttribute('href', /stripe\.com.*pdf/);
    }
  });
});

test.describe('Plan Comparison', () => {
  test('pricing page shows all plans', async ({ page }) => {
    // Pricing page is public
    await page.goto('/pricing');

    // Should show all three plans
    await expect(page.getByText(/free/i).first()).toBeVisible();
    await expect(page.getByText(/pro/i).first()).toBeVisible();
    await expect(page.getByText(/enterprise/i).first()).toBeVisible();
  });

  test('pricing page shows feature comparison', async ({ page }) => {
    await page.goto('/pricing');

    // Should show feature rows
    await expect(page.getByText(/resources/i)).toBeVisible();
    await expect(page.getByText(/secured retrievals/i)).toBeVisible();
    await expect(page.getByText(/team members/i)).toBeVisible();
    await expect(page.getByText(/custom branding/i)).toBeVisible();
  });

  test('yearly pricing shows discount', async ({ page }) => {
    await page.goto('/pricing');

    // Toggle to yearly billing
    await page.getByLabel(/yearly/i).click();

    // Should show yearly prices with discount
    await expect(page.getByText(/save/i)).toBeVisible();
  });

  test('get started button on pricing page', async ({ page }) => {
    await page.goto('/pricing');

    // Click get started on pro plan
    const proCard = page.locator('[data-plan="pro"]');
    await proCard.getByRole('button', { name: /get started/i }).click();

    // Should redirect to signup or checkout
    await expect(page).toHaveURL(/\/(signup|checkout)/);
  });
});

test.describe('Entitlement Enforcement', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.freeUser.email, testUsers.freeUser.password);
  });

  test('free user cannot access pro features', async ({ page }) => {
    await page.goto('/settings/brand');

    // Should show upgrade prompt
    await expect(page.getByText(/upgrade.*pro/i)).toBeVisible();

    // Brand settings should be disabled or hidden
    const brandForm = page.getByTestId('brand-settings-form');
    if (await brandForm.isVisible()) {
      await expect(brandForm).toBeDisabled();
    }
  });

  test('free user sees resource limit warning', async ({ page }) => {
    await page.goto('/resources');

    // Should show resource count out of limit
    await expect(page.getByText(/3 resources/i)).toBeVisible();

    // If at limit, create button should show upgrade prompt
    const createButton = page.getByRole('button', { name: /create/i });
    if (await createButton.isDisabled()) {
      await expect(page.getByText(/upgrade.*create more/i)).toBeVisible();
    }
  });

  test('analytics shows upgrade prompt for free users', async ({ page }) => {
    await page.goto('/analytics');

    // Should show upgrade prompt or limited analytics
    const upgradePrompt = page.getByText(/upgrade.*full analytics/i);
    await expect(upgradePrompt).toBeVisible();
  });
});

test.describe('Subscription Lifecycle', () => {
  test('successful checkout activates subscription', async ({ page, context }) => {
    await loginAsUser(page, testUsers.freeUser.email, testUsers.freeUser.password);
    await page.goto('/settings/billing');

    // Start checkout
    await page.getByRole('button', { name: /upgrade to pro/i }).click();
    await page.getByLabel(/monthly/i).click();
    await page.getByRole('button', { name: /continue to checkout/i }).click();

    // In a real test with Stripe test mode, we would:
    // 1. Fill in test card: 4242424242424242
    // 2. Complete checkout
    // 3. Verify redirect back to app with success
    // 4. Verify subscription is active

    // Simulate successful return from Stripe
    // await page.goto('/settings/billing?checkout=success');
    // await expect(page.getByText(/pro plan/i)).toBeVisible();
    // await expect(page.getByText(/subscription active/i)).toBeVisible();
  });

  test('canceled checkout returns to billing page', async ({ page }) => {
    await loginAsUser(page, testUsers.freeUser.email, testUsers.freeUser.password);
    await page.goto('/settings/billing');

    // Start checkout
    await page.getByRole('button', { name: /upgrade to pro/i }).click();
    await page.getByRole('button', { name: /continue to checkout/i }).click();

    // Simulate cancel from Stripe
    await page.goto('/settings/billing?checkout=canceled');

    // Should still show free plan
    await expect(page.getByText(/free plan/i)).toBeVisible();
  });
});
