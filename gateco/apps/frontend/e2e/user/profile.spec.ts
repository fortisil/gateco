/**
 * E2E tests for user profile and settings management.
 *
 * Tests user profile viewing, editing, team management,
 * and account settings functionality.
 */

import { test, expect } from '@playwright/test';
import { testUsers, loginAsUser, logout } from '../fixtures/auth.fixture';

test.describe('User Profile', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test.describe('Profile View', () => {
    test('displays user profile information', async ({ page }) => {
      await page.goto('/settings/profile');

      await expect(page.getByRole('heading', { name: /profile/i })).toBeVisible();
      await expect(page.getByLabel(/name/i)).toHaveValue(testUsers.owner.name);
      await expect(page.getByLabel(/email/i)).toHaveValue(testUsers.owner.email);
    });

    test('displays organization information', async ({ page }) => {
      await page.goto('/settings/profile');

      await expect(page.getByText(/organization/i)).toBeVisible();
      await expect(page.getByText(/test organization/i)).toBeVisible();
    });

    test('shows user role badge', async ({ page }) => {
      await page.goto('/settings/profile');

      await expect(page.getByText(/owner/i)).toBeVisible();
    });

    test('displays avatar or initials', async ({ page }) => {
      await page.goto('/settings/profile');

      const avatar = page.getByTestId('user-avatar');
      await expect(avatar).toBeVisible();
    });
  });

  test.describe('Profile Editing', () => {
    test('allows updating display name', async ({ page }) => {
      await page.goto('/settings/profile');

      const nameInput = page.getByLabel(/name/i);
      await nameInput.clear();
      await nameInput.fill('Updated Name');

      await page.getByRole('button', { name: /save/i }).click();

      await expect(page.getByText(/profile updated/i)).toBeVisible();
    });

    test('validates name field', async ({ page }) => {
      await page.goto('/settings/profile');

      const nameInput = page.getByLabel(/name/i);
      await nameInput.clear();

      await page.getByRole('button', { name: /save/i }).click();

      await expect(page.getByText(/name is required/i)).toBeVisible();
    });

    test('allows uploading avatar', async ({ page }) => {
      await page.goto('/settings/profile');

      // Note: File upload testing with mock
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeAttached();
    });

    test('shows loading state during save', async ({ page }) => {
      await page.goto('/settings/profile');

      const nameInput = page.getByLabel(/name/i);
      await nameInput.fill('New Name');

      const saveButton = page.getByRole('button', { name: /save/i });
      await saveButton.click();

      // Button should show loading state briefly
      await expect(saveButton).toBeDisabled();
    });
  });

  test.describe('Password Change', () => {
    test('navigates to password change section', async ({ page }) => {
      await page.goto('/settings/security');

      await expect(
        page.getByRole('heading', { name: /change password/i })
      ).toBeVisible();
    });

    test('validates current password is required', async ({ page }) => {
      await page.goto('/settings/security');

      await page.getByLabel(/new password/i).first().fill('newpassword123');
      await page.getByLabel(/confirm password/i).fill('newpassword123');

      await page.getByRole('button', { name: /update password/i }).click();

      await expect(
        page.getByText(/current password is required/i)
      ).toBeVisible();
    });

    test('validates password confirmation matches', async ({ page }) => {
      await page.goto('/settings/security');

      await page.getByLabel(/current password/i).fill('currentpass');
      await page.getByLabel(/new password/i).first().fill('newpassword123');
      await page.getByLabel(/confirm password/i).fill('differentpassword');

      await page.getByRole('button', { name: /update password/i }).click();

      await expect(page.getByText(/passwords do not match/i)).toBeVisible();
    });

    test('validates password strength', async ({ page }) => {
      await page.goto('/settings/security');

      await page.getByLabel(/current password/i).fill('currentpass');
      await page.getByLabel(/new password/i).first().fill('weak');
      await page.getByLabel(/confirm password/i).fill('weak');

      await page.getByRole('button', { name: /update password/i }).click();

      await expect(
        page.getByText(/password must be at least 8 characters/i)
      ).toBeVisible();
    });
  });
});

test.describe('Team Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test.describe('Team Members List', () => {
    test('displays team members', async ({ page }) => {
      await page.goto('/settings/team');

      await expect(
        page.getByRole('heading', { name: /team members/i })
      ).toBeVisible();

      // Should show at least the current user
      await expect(page.getByText(testUsers.owner.email)).toBeVisible();
    });

    test('shows member roles', async ({ page }) => {
      await page.goto('/settings/team');

      // Check role badges are visible
      await expect(page.getByText(/owner/i).first()).toBeVisible();
    });

    test('shows invite button for owners', async ({ page }) => {
      await page.goto('/settings/team');

      await expect(
        page.getByRole('button', { name: /invite/i })
      ).toBeVisible();
    });
  });

  test.describe('Invite Members', () => {
    test('opens invite modal', async ({ page }) => {
      await page.goto('/settings/team');

      await page.getByRole('button', { name: /invite/i }).click();

      await expect(
        page.getByRole('dialog', { name: /invite team member/i })
      ).toBeVisible();
    });

    test('validates email format', async ({ page }) => {
      await page.goto('/settings/team');

      await page.getByRole('button', { name: /invite/i }).click();

      await page.getByLabel(/email/i).fill('invalid-email');
      await page.getByRole('button', { name: /send invite/i }).click();

      await expect(page.getByText(/invalid email/i)).toBeVisible();
    });

    test('allows selecting role for invite', async ({ page }) => {
      await page.goto('/settings/team');

      await page.getByRole('button', { name: /invite/i }).click();

      const roleSelect = page.getByLabel(/role/i);
      await expect(roleSelect).toBeVisible();

      await roleSelect.click();
      await expect(page.getByRole('option', { name: /admin/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /member/i })).toBeVisible();
    });

    test('sends invite successfully', async ({ page }) => {
      await page.goto('/settings/team');

      await page.getByRole('button', { name: /invite/i }).click();

      await page.getByLabel(/email/i).fill('newmember@example.com');
      await page.getByLabel(/role/i).click();
      await page.getByRole('option', { name: /member/i }).click();

      await page.getByRole('button', { name: /send invite/i }).click();

      await expect(page.getByText(/invite sent/i)).toBeVisible();
    });
  });

  test.describe('Member Permissions', () => {
    test('admin cannot see invite button', async ({ page }) => {
      await logout(page);
      await loginAsUser(page, testUsers.admin);

      await page.goto('/settings/team');

      // Admins should not be able to invite (only owners)
      await expect(
        page.getByRole('button', { name: /invite/i })
      ).not.toBeVisible();
    });

    test('member has limited team view', async ({ page }) => {
      await logout(page);
      await loginAsUser(page, testUsers.member);

      await page.goto('/settings/team');

      // Members should see team but not manage it
      await expect(page.getByText(testUsers.owner.email)).toBeVisible();
      await expect(
        page.getByRole('button', { name: /remove/i })
      ).not.toBeVisible();
    });
  });

  test.describe('Remove Members', () => {
    test('owner can remove team members', async ({ page }) => {
      await page.goto('/settings/team');

      // Find a member row (not the owner)
      const memberRow = page.locator('[data-testid="team-member-row"]').filter({
        hasText: testUsers.member.email,
      });

      await memberRow.getByRole('button', { name: /remove/i }).click();

      // Confirm removal
      await expect(
        page.getByRole('dialog', { name: /remove member/i })
      ).toBeVisible();
      await page.getByRole('button', { name: /confirm/i }).click();

      await expect(page.getByText(/member removed/i)).toBeVisible();
    });

    test('cannot remove self', async ({ page }) => {
      await page.goto('/settings/team');

      const ownerRow = page.locator('[data-testid="team-member-row"]').filter({
        hasText: testUsers.owner.email,
      });

      // Remove button should not be present for own row
      await expect(
        ownerRow.getByRole('button', { name: /remove/i })
      ).not.toBeVisible();
    });
  });
});

test.describe('Account Settings', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test.describe('Notification Preferences', () => {
    test('displays notification settings', async ({ page }) => {
      await page.goto('/settings/notifications');

      await expect(
        page.getByRole('heading', { name: /notifications/i })
      ).toBeVisible();
    });

    test('allows toggling email notifications', async ({ page }) => {
      await page.goto('/settings/notifications');

      const emailToggle = page.getByRole('switch', {
        name: /email notifications/i,
      });
      await expect(emailToggle).toBeVisible();

      await emailToggle.click();
      await expect(page.getByText(/preferences saved/i)).toBeVisible();
    });
  });

  test.describe('Organization Settings', () => {
    test('displays organization name', async ({ page }) => {
      await page.goto('/settings/organization');

      await expect(page.getByLabel(/organization name/i)).toBeVisible();
    });

    test('allows updating organization name', async ({ page }) => {
      await page.goto('/settings/organization');

      const nameInput = page.getByLabel(/organization name/i);
      await nameInput.clear();
      await nameInput.fill('Updated Org Name');

      await page.getByRole('button', { name: /save/i }).click();

      await expect(page.getByText(/organization updated/i)).toBeVisible();
    });

    test('shows current plan information', async ({ page }) => {
      await page.goto('/settings/organization');

      await expect(page.getByText(/current plan/i)).toBeVisible();
    });
  });

  test.describe('Danger Zone', () => {
    test('shows delete account option', async ({ page }) => {
      await page.goto('/settings/account');

      await expect(
        page.getByRole('heading', { name: /danger zone/i })
      ).toBeVisible();
      await expect(
        page.getByRole('button', { name: /delete account/i })
      ).toBeVisible();
    });

    test('requires confirmation for account deletion', async ({ page }) => {
      await page.goto('/settings/account');

      await page.getByRole('button', { name: /delete account/i }).click();

      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible();
      await expect(
        dialog.getByText(/this action cannot be undone/i)
      ).toBeVisible();

      // Should require typing confirmation
      await expect(
        dialog.getByPlaceholder(/type "delete" to confirm/i)
      ).toBeVisible();
    });

    test('prevents deletion without confirmation text', async ({ page }) => {
      await page.goto('/settings/account');

      await page.getByRole('button', { name: /delete account/i }).click();

      const dialog = page.getByRole('dialog');
      const confirmButton = dialog.getByRole('button', {
        name: /delete account/i,
      });

      // Button should be disabled without confirmation
      await expect(confirmButton).toBeDisabled();
    });
  });
});

test.describe('API Keys', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, testUsers.owner);
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });

  test('displays API keys section', async ({ page }) => {
    await page.goto('/settings/api-keys');

    await expect(page.getByRole('heading', { name: /api keys/i })).toBeVisible();
  });

  test('allows creating new API key', async ({ page }) => {
    await page.goto('/settings/api-keys');

    await page.getByRole('button', { name: /create key/i }).click();

    await page.getByLabel(/key name/i).fill('Test API Key');
    await page.getByRole('button', { name: /create/i }).click();

    // Should show the new key (only shown once)
    await expect(page.getByText(/copy your api key/i)).toBeVisible();
    await expect(page.getByTestId('api-key-value')).toBeVisible();
  });

  test('allows revoking API key', async ({ page }) => {
    await page.goto('/settings/api-keys');

    // Assuming there's an existing key
    const keyRow = page.locator('[data-testid="api-key-row"]').first();

    if (await keyRow.isVisible()) {
      await keyRow.getByRole('button', { name: /revoke/i }).click();

      await expect(
        page.getByRole('dialog', { name: /revoke api key/i })
      ).toBeVisible();
      await page.getByRole('button', { name: /confirm/i }).click();

      await expect(page.getByText(/api key revoked/i)).toBeVisible();
    }
  });

  test('shows key last used date', async ({ page }) => {
    await page.goto('/settings/api-keys');

    const keyRow = page.locator('[data-testid="api-key-row"]').first();

    if (await keyRow.isVisible()) {
      await expect(keyRow.getByText(/last used/i)).toBeVisible();
    }
  });
});
