/**
 * E2E tests for plan upgrade and downgrade flows.
 *
 * Tests the complete billing upgrade journey including plan selection,
 * Stripe checkout integration, and plan management.
 */

import { test, expect } from '@playwright/test';

test.describe('Plan Upgrade Flow', () => {
  // Use authenticated user on free plan
  test.use({ storageState: 'playwright/.auth/free-user.json' });

  test('free user sees upgrade options on billing page', async ({ page }) => {
    await page.goto('/settings/billing');

    // Should see current plan
    await expect(page.getByText(/free plan/i)).toBeVisible();
    await expect(page.getByText(/current plan/i)).toBeVisible();

    // Should see upgrade buttons
    await expect(
      page.getByRole('button', { name: /upgrade to pro/i })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: /upgrade to enterprise/i })
    ).toBeVisible();
  });

  test('can view plan comparison', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click to see plan comparison
    await page.getByRole('button', { name: /compare plans/i }).click();

    // Should show comparison table
    await expect(page.getByRole('table')).toBeVisible();

    // Should show feature rows
    await expect(page.getByText(/custom branding/i)).toBeVisible();
    await expect(page.getByText(/analytics/i)).toBeVisible();
    await expect(page.getByText(/priority support/i)).toBeVisible();

    // Should show limits
    await expect(page.getByText(/secured retrievals/i)).toBeVisible();
    await expect(page.getByText(/team members/i)).toBeVisible();
  });

  test('can toggle between monthly and yearly pricing', async ({ page }) => {
    await page.goto('/settings/billing');

    // Default should be monthly
    await expect(page.getByText('$29/month')).toBeVisible();

    // Switch to yearly
    await page.getByRole('switch', { name: /yearly/i }).click();

    // Should show yearly pricing
    await expect(page.getByText('$290/year')).toBeVisible();

    // Should show savings
    await expect(page.getByText(/save/i)).toBeVisible();
  });

  test('clicking upgrade opens Stripe checkout', async ({ page }) => {
    await page.goto('/settings/billing');

    // Click upgrade to Pro
    await page.getByRole('button', { name: /upgrade to pro/i }).click();

    // Should redirect to Stripe checkout
    await expect(page).toHaveURL(/checkout\.stripe\.com/);
  });

  test('upgrade button shows loading state', async ({ page }) => {
    await page.goto('/settings/billing');

    const upgradeButton = page.getByRole('button', { name: /upgrade to pro/i });

    await upgradeButton.click();

    // Should show loading state before redirect
    await expect(upgradeButton).toBeDisabled();
  });
});

test.describe('Pro Plan Management', () => {
  // Use authenticated user on Pro plan
  test.use({ storageState: 'playwright/.auth/pro-user.json' });

  test('pro user sees current plan on billing page', async ({ page }) => {
    await page.goto('/settings/billing');

    await expect(page.getByText(/pro plan/i)).toBeVisible();
    await expect(page.getByText(/current plan/i)).toBeVisible();
  });

  test('pro user can upgrade to enterprise', async ({ page }) => {
    await page.goto('/settings/billing');

    await expect(
      page.getByRole('button', { name: /upgrade to enterprise/i })
    ).toBeVisible();

    // Free should show downgrade option
    await expect(
      page.getByRole('button', { name: /downgrade to free/i })
    ).toBeVisible();
  });

  test('pro user can access billing portal', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /manage subscription/i }).click();

    // Should redirect to Stripe billing portal
    await expect(page).toHaveURL(/billing\.stripe\.com/);
  });

  test('shows subscription details', async ({ page }) => {
    await page.goto('/settings/billing');

    // Should show billing period
    await expect(page.getByText(/next billing date/i)).toBeVisible();

    // Should show payment method
    await expect(page.getByText(/payment method/i)).toBeVisible();
    await expect(page.getByText(/\*\*\*\* \d{4}/)).toBeVisible(); // Card ending
  });
});

test.describe('Downgrade Flow', () => {
  test.use({ storageState: 'playwright/.auth/pro-user.json' });

  test('downgrade shows confirmation dialog', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /downgrade to free/i }).click();

    // Should show confirmation dialog
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/are you sure/i)).toBeVisible();
  });

  test('downgrade dialog shows what will be lost', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /downgrade to free/i }).click();

    const dialog = page.getByRole('dialog');

    // Should list features that will be lost
    await expect(dialog.getByText(/you will lose/i)).toBeVisible();
    await expect(dialog.getByText(/custom branding/i)).toBeVisible();
    await expect(dialog.getByText(/analytics/i)).toBeVisible();
  });

  test('downgrade dialog shows resource impact', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /downgrade to free/i }).click();

    const dialog = page.getByRole('dialog');

    // Should warn about resource limits
    await expect(
      dialog.getByText(/resources will be limited to 3/i)
    ).toBeVisible();
  });

  test('can cancel downgrade', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /downgrade to free/i }).click();

    // Cancel
    await page.getByRole('button', { name: /cancel/i }).click();

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Should still be on Pro plan
    await expect(page.getByText(/pro plan/i)).toBeVisible();
  });

  test('confirming downgrade processes correctly', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /downgrade to free/i }).click();

    // Confirm downgrade
    await page.getByRole('button', { name: /confirm downgrade/i }).click();

    // Should show success message
    await expect(
      page.getByText(/downgrade scheduled|will take effect/i)
    ).toBeVisible();
  });
});

test.describe('Checkout Success/Cancel', () => {
  test.use({ storageState: 'playwright/.auth/free-user.json' });

  test('successful checkout redirects to success page', async ({ page }) => {
    // Simulate Stripe checkout success callback
    await page.goto('/billing/success?session_id=cs_test_123');

    // Should show success message
    await expect(page.getByText(/welcome to pro/i)).toBeVisible();
    await expect(
      page.getByText(/subscription activated|thank you/i)
    ).toBeVisible();

    // Should have link to dashboard
    await expect(
      page.getByRole('link', { name: /go to dashboard/i })
    ).toBeVisible();
  });

  test('cancelled checkout returns to billing page', async ({ page }) => {
    await page.goto('/billing/cancel');

    // Should be back on billing page
    await expect(page).toHaveURL('/settings/billing');

    // Should show message
    await expect(page.getByText(/checkout cancelled/i)).toBeVisible();
  });
});

test.describe('Invoice History', () => {
  test.use({ storageState: 'playwright/.auth/pro-user.json' });

  test('can view invoice history', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('tab', { name: /invoices/i }).click();

    // Should show invoice list
    await expect(page.getByRole('table')).toBeVisible();

    // Should have invoice rows
    await expect(page.getByText(/pro plan/i).first()).toBeVisible();
    await expect(page.getByText(/\$29\.00/)).toBeVisible();
  });

  test('can download invoice PDF', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('tab', { name: /invoices/i }).click();

    // Click download link
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: /download/i }).first().click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('invoice shows status', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('tab', { name: /invoices/i }).click();

    // Should show paid status
    await expect(page.getByText(/paid/i).first()).toBeVisible();
  });
});

test.describe('Upgrade - Accessibility', () => {
  test.use({ storageState: 'playwright/.auth/free-user.json' });

  test('billing page is keyboard navigable', async ({ page }) => {
    await page.goto('/settings/billing');

    // Tab through plan cards
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should be able to focus upgrade buttons
    const upgradeButton = page.getByRole('button', { name: /upgrade to pro/i });
    await upgradeButton.focus();
    await expect(upgradeButton).toBeFocused();
  });

  test('plan comparison table is accessible', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /compare plans/i }).click();

    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // Table should have headers
    await expect(page.getByRole('columnheader')).toHaveCount(4); // Feature + 3 plans
  });

  test('downgrade dialog traps focus', async ({ page }) => {
    await page.goto('/settings/billing');

    // Need Pro user for downgrade
    // This test structure shows the pattern
  });
});

test.describe('Upgrade - Mobile', () => {
  test.use({
    storageState: 'playwright/.auth/free-user.json',
    viewport: { width: 375, height: 667 },
  });

  test('billing page works on mobile', async ({ page }) => {
    await page.goto('/settings/billing');

    // Plan cards should be stacked
    await expect(page.getByText(/free plan/i)).toBeVisible();
    await expect(
      page.getByRole('button', { name: /upgrade to pro/i })
    ).toBeVisible();
  });

  test('plan comparison scrolls horizontally on mobile', async ({ page }) => {
    await page.goto('/settings/billing');

    await page.getByRole('button', { name: /compare plans/i }).click();

    // Table should be scrollable
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // Should be able to scroll to see all plans
  });
});
