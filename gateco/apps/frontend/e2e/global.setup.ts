/**
 * Global Setup for Playwright E2E Tests
 *
 * This setup runs once before all tests to:
 * - Seed test database
 * - Create test users
 * - Prepare authentication state
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL || 'http://localhost:3000';

  console.log('🔧 Running global E2E test setup...');

  // Check if the server is accessible
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Wait for the application to be ready
    console.log(`📡 Checking server at ${baseURL}...`);
    await page.goto(baseURL, { timeout: 30000 });
    console.log('✅ Server is accessible');

    // Seed test data via API if needed
    // This would typically call a test setup endpoint
    const apiBaseURL = process.env.API_URL || 'http://localhost:8000';

    if (process.env.SEED_TEST_DATA === 'true') {
      console.log('🌱 Seeding test data...');

      const response = await page.request.post(`${apiBaseURL}/api/v1/test/seed`, {
        headers: {
          'X-Test-Secret': process.env.TEST_SECRET || 'test-secret',
        },
        data: {
          seed_users: true,
          seed_organizations: true,
          seed_resources: true,
          seed_subscriptions: true,
        },
      });

      if (response.ok()) {
        console.log('✅ Test data seeded successfully');
      } else {
        console.log('⚠️ Test data seeding skipped or failed (non-critical)');
      }
    }

    // Create authenticated state for test users
    // This pre-authenticates users so tests can reuse auth state
    if (process.env.SAVE_AUTH_STATE === 'true') {
      console.log('🔐 Creating authenticated state...');

      // Login as test owner
      await page.goto(`${baseURL}/login`);
      await page.fill('[name="email"]', 'owner@test.com');
      await page.fill('[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');

      // Wait for login to complete
      await page.waitForURL('**/dashboard**', { timeout: 10000 });

      // Save authentication state
      await page.context().storageState({
        path: 'e2e/.auth/owner.json',
      });

      console.log('✅ Authentication state saved');
    }
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    // Don't throw - let tests fail individually
  } finally {
    await browser.close();
  }

  console.log('🎉 Global setup complete');
}

export default globalSetup;
