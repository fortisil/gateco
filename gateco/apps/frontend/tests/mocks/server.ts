/**
 * MSW server setup for testing.
 *
 * This server intercepts network requests during tests and returns
 * mock responses defined in handlers.ts.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the MSW server with default handlers
export const server = setupServer(...handlers);

/**
 * Setup MSW server for tests.
 *
 * Call this in your test setup file:
 * ```
 * import { setupMockServer } from './mocks/server';
 *
 * beforeAll(() => setupMockServer.listen());
 * afterEach(() => setupMockServer.resetHandlers());
 * afterAll(() => setupMockServer.close());
 * ```
 */
export const setupMockServer = {
  listen: () => server.listen({ onUnhandledRequest: 'warn' }),
  close: () => server.close(),
  resetHandlers: () => server.resetHandlers(),
  use: server.use.bind(server),
};

export { handlers };
