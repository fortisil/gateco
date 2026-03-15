/**
 * E2E tests for resource management.
 *
 * These tests verify creating, viewing, editing, and deleting
 * gated resources.
 */

import { test, expect } from '@playwright/test';
import { loginAsUser, testUsers } from '../fixtures/auth.fixture';

test.describe('Resource Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
  });

  test('displays resource list', async ({ page }) => {
    await page.goto('/resources');

    // Should show resources header
    await expect(page.getByRole('heading', { name: /resources/i })).toBeVisible();

    // Should show create button
    await expect(page.getByRole('button', { name: /create/i })).toBeVisible();
  });

  test('create public link resource', async ({ page }) => {
    await page.goto('/resources');

    // Click create button
    await page.getByRole('button', { name: /create/i }).click();

    // Should show create form
    await expect(page.getByRole('heading', { name: /create resource/i })).toBeVisible();

    // Select link type
    await page.getByLabel(/link/i).click();

    // Fill in resource details
    await page.getByLabel(/title/i).fill('Test Link Resource');
    await page.getByLabel(/description/i).fill('A test link resource');
    await page.getByLabel(/content url/i).fill('https://example.com/content');

    // Set access type to public
    await page.getByLabel(/public/i).click();

    // Submit form
    await page.getByRole('button', { name: /create/i }).click();

    // Should redirect to resource list or detail page
    await expect(page).toHaveURL(/\/resources/);

    // Should show success message
    await expect(page.getByText(/resource created/i)).toBeVisible();

    // Resource should appear in list
    await expect(page.getByText('Test Link Resource')).toBeVisible();
  });

  test('create paid resource with price', async ({ page }) => {
    await page.goto('/resources/new');

    // Select file type
    await page.getByLabel(/file/i).click();

    // Fill in resource details
    await page.getByLabel(/title/i).fill('Premium Content');
    await page.getByLabel(/content url/i).fill('https://example.com/premium.pdf');

    // Set access type to paid
    await page.getByLabel(/paid/i).click();

    // Set price
    await page.getByLabel(/price/i).fill('9.99');

    // Submit form
    await page.getByRole('button', { name: /create/i }).click();

    // Should show success
    await expect(page.getByText(/resource created/i)).toBeVisible();

    // Resource should show price
    await expect(page.getByText(/\$9\.99/)).toBeVisible();
  });

  test('create invite-only resource', async ({ page }) => {
    await page.goto('/resources/new');

    // Fill in resource details
    await page.getByLabel(/title/i).fill('Exclusive Content');
    await page.getByLabel(/content url/i).fill('https://example.com/exclusive');

    // Set access type to invite-only
    await page.getByLabel(/invite only/i).click();

    // Add allowed emails
    const emailInput = page.getByLabel(/allowed emails/i);
    await emailInput.fill('vip1@example.com');
    await page.keyboard.press('Enter');
    await emailInput.fill('vip2@example.com');
    await page.keyboard.press('Enter');

    // Submit form
    await page.getByRole('button', { name: /create/i }).click();

    // Should show success
    await expect(page.getByText(/resource created/i)).toBeVisible();
  });

  test('validates required fields', async ({ page }) => {
    await page.goto('/resources/new');

    // Submit without filling required fields
    await page.getByRole('button', { name: /create/i }).click();

    // Should show validation errors
    await expect(page.getByText(/title is required/i)).toBeVisible();
    await expect(page.getByText(/content url is required/i)).toBeVisible();
  });

  test('validates URL format', async ({ page }) => {
    await page.goto('/resources/new');

    // Fill in invalid URL
    await page.getByLabel(/title/i).fill('Test Resource');
    await page.getByLabel(/content url/i).fill('not-a-valid-url');

    // Submit form
    await page.getByRole('button', { name: /create/i }).click();

    // Should show URL validation error
    await expect(page.getByText(/valid url/i)).toBeVisible();
  });

  test('validates minimum price', async ({ page }) => {
    await page.goto('/resources/new');

    // Fill in resource with paid access
    await page.getByLabel(/title/i).fill('Test Resource');
    await page.getByLabel(/content url/i).fill('https://example.com/content');
    await page.getByLabel(/paid/i).click();
    await page.getByLabel(/price/i).fill('0.25'); // Below $0.50 minimum

    // Submit form
    await page.getByRole('button', { name: /create/i }).click();

    // Should show price validation error
    await expect(page.getByText(/minimum.*\$0\.50/i)).toBeVisible();
  });
});

test.describe('Resource Editing', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
  });

  test('edit existing resource', async ({ page }) => {
    await page.goto('/resources');

    // Click on a resource to view it
    await page.getByText('Test Link Resource').click();

    // Click edit button
    await page.getByRole('button', { name: /edit/i }).click();

    // Should show edit form with pre-filled values
    const titleInput = page.getByLabel(/title/i);
    await expect(titleInput).toHaveValue('Test Link Resource');

    // Update title
    await titleInput.fill('Updated Resource Title');

    // Save changes
    await page.getByRole('button', { name: /save/i }).click();

    // Should show success message
    await expect(page.getByText(/resource updated/i)).toBeVisible();

    // Should show updated title
    await expect(page.getByText('Updated Resource Title')).toBeVisible();
  });

  test('cancel edit returns to resource view', async ({ page }) => {
    await page.goto('/resources');
    await page.getByText('Test Link Resource').click();
    await page.getByRole('button', { name: /edit/i }).click();

    // Make changes
    await page.getByLabel(/title/i).fill('Unsaved Changes');

    // Cancel
    await page.getByRole('button', { name: /cancel/i }).click();

    // Should return to view mode without changes
    await expect(page.getByText('Test Link Resource')).toBeVisible();
    await expect(page.queryByText('Unsaved Changes')).not.toBeVisible();
  });
});

test.describe('Resource Deletion', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
  });

  test('delete resource with confirmation', async ({ page }) => {
    await page.goto('/resources');

    // Click on a resource
    await page.getByText('Test Link Resource').click();

    // Click delete button
    await page.getByRole('button', { name: /delete/i }).click();

    // Should show confirmation dialog
    await expect(page.getByText(/are you sure/i)).toBeVisible();

    // Confirm deletion
    await page.getByRole('button', { name: /confirm/i }).click();

    // Should redirect to resource list
    await expect(page).toHaveURL('/resources');

    // Should show success message
    await expect(page.getByText(/resource deleted/i)).toBeVisible();

    // Resource should no longer appear
    await expect(page.queryByText('Test Link Resource')).not.toBeVisible();
  });

  test('cancel delete keeps resource', async ({ page }) => {
    await page.goto('/resources');
    await page.getByText('Test Link Resource').click();
    await page.getByRole('button', { name: /delete/i }).click();

    // Cancel deletion
    await page.getByRole('button', { name: /cancel/i }).click();

    // Resource should still exist
    await expect(page.getByText('Test Link Resource')).toBeVisible();
  });
});

test.describe('Resource Statistics', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
  });

  test('displays resource statistics', async ({ page }) => {
    await page.goto('/resources');

    // Click on a resource
    await page.getByText('Test Link Resource').click();

    // Should show statistics
    await expect(page.getByText(/views/i)).toBeVisible();
    await expect(page.getByText(/unique visitors/i)).toBeVisible();
  });

  test('displays revenue for paid resources', async ({ page }) => {
    await page.goto('/resources');

    // Click on paid resource
    await page.getByText('Premium Content').click();

    // Should show revenue
    await expect(page.getByText(/revenue/i)).toBeVisible();
  });
});

test.describe('Resource Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner.email, testUsers.owner.password);
  });

  test('filter by resource type', async ({ page }) => {
    await page.goto('/resources');

    // Filter by link type
    await page.getByLabel(/type/i).selectOption('link');

    // Should only show link resources
    // Verify filtered results
  });

  test('filter by access type', async ({ page }) => {
    await page.goto('/resources');

    // Filter by paid access
    await page.getByLabel(/access/i).selectOption('paid');

    // Should only show paid resources
  });

  test('search resources by title', async ({ page }) => {
    await page.goto('/resources');

    // Search
    await page.getByPlaceholder(/search/i).fill('Premium');

    // Should filter to matching resources
    await expect(page.getByText('Premium Content')).toBeVisible();
  });
});

test.describe('Resource Plan Limits', () => {
  test('free user cannot exceed resource limit', async ({ page }) => {
    await loginAsUser(page, testUsers.freeUser.email, testUsers.freeUser.password);
    await page.goto('/resources');

    // If already at limit (3 resources), create button should be disabled
    // or show upgrade prompt
    const createButton = page.getByRole('button', { name: /create/i });

    // Check if at limit
    const resourceCount = page.getByTestId('resource-count');
    const countText = await resourceCount.textContent();

    if (countText?.includes('3 / 3')) {
      // At limit - button should show upgrade
      await createButton.click();
      await expect(page.getByText(/upgrade.*create more/i)).toBeVisible();
    }
  });
});
