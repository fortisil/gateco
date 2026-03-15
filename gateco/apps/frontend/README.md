# gateco - Frontend

React frontend application built with Vite, Tailwind CSS, and TypeScript.

## Development

```bash
npm install
npm run dev
```

By default, the frontend connects to the **real backend** via the Vite dev proxy (`/api` -> `http://localhost:8000`). Make sure the backend is running.

To develop with mock data instead (no backend required), enable MSW:

```bash
VITE_MSW=true npm run dev
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server (port 5173) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm test` | Run tests |
| `npm run test:coverage` | Tests with coverage |
| `npm run lint` | Lint code |
| `npm run typecheck` | Type check |

## Structure

```
src/
  api/               # API client and endpoint functions
    client.ts        # Base HTTP client (apiGet, apiPost, apiPatch, apiDelete)
    auth.ts          # Auth endpoints (login, signup, exchangeCode)
    connectors.ts    # Connectors CRUD
    identity-providers.ts
    pipelines.ts
    policies.ts
    data-catalog.ts
    dashboard.ts
    billing.ts
    queryKeys.ts     # TanStack Query key constants
  components/
    auth/            # OAuth buttons, login/signup forms
    billing/         # PlanBadge, UsageMeter, UpgradeModal, EntitlementGate
    layout/          # AppShell, Sidebar, TopNav, UserMenu
    shared/          # ErrorBoundary, StatusBadge, DataTable, EmptyState
    ui/              # shadcn/ui primitives (button, card, input, badge, skeleton, dialog)
  contexts/          # EntitlementContext
  pages/             # Page components (dashboard, audit-log, access-simulator, etc.)
  routes/            # Router config, ProtectedRoute
  admin/             # DB setup wizard (admin panel)
  lib/utils.ts       # cn() utility
  App.tsx            # Root component
  main.tsx           # Entry point
```

## API Integration

The API client (`src/api/client.ts`) defaults to relative `/api` paths, which the Vite dev proxy forwards to the backend. This means **no environment variable is required** for local development.

For production or non-proxy setups, set:

```env
VITE_API_URL=http://your-backend-host:8000
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | (unset -- uses `/api` via proxy) | Backend API base URL. Only needed in production |
| `VITE_MSW` | (unset -- MSW disabled) | Set to `true` to enable Mock Service Worker |

### Response Envelope Convention

The backend wraps list responses in `{ data: [...] }`. All frontend API functions extract `.data` before returning, so page components receive plain arrays.

### OAuth Flow

OAuth uses the auth code exchange pattern:
1. User clicks OAuth button, redirected to provider
2. Provider redirects back with `?code=...`
3. `OAuthCallbackPage` reads the `code` param and calls `exchangeCode(code)` -> `POST /auth/exchange`
4. Backend returns access/refresh tokens

## Error Handling

An `ErrorBoundary` component wraps the main content area in `AppShell`. It is keyed by `location.pathname` so errors reset when the user navigates to a different page.

## Testing

```bash
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```
