# CLAUDE.md — Gateco Project Guide

## What is Gateco?

Gateco is a **permission-aware retrieval layer for AI systems** — the security and permission middleware between AI agents and organizational knowledge. It gates access to digital resources with policy enforcement, identity-based access control, and auditability.

**Not** a vector database, RAG framework, or IAM replacement.

**Business model:** 3-tier SaaS (Free / Pro / Enterprise) with usage-based billing on "secured retrievals."

**Domain:** `gateco.ai` -- all public URLs and email addresses use this domain (e.g., `support@gateco.ai`, `enterprise@gateco.ai`).

**Pricing:** Free $0/mo (100 retrievals, 1 connector), Pro $49/mo (10K retrievals, 5 connectors), Enterprise $199/mo (unlimited).

---

## Repository Layout

Monorepo (npm workspaces) rooted at `gateco/`.

```
gateco/
├── apps/
│   ├── frontend/       # React 18 + Vite + TypeScript + Tailwind + shadcn/ui
│   ├── backend/        # FastAPI (Python 3.11+) + SQLAlchemy 2.0 async + Pydantic v2
│   └── website/        # Next.js 14 marketing site (SSR, MDX blog/docs)
├── packages/
│   ├── design-tokens/  # Shared design tokens
│   ├── ui/             # Shared UI components
│   ├── contracts/      # API contracts (OpenAPI spec + TS types, 51 paths)
│   ├── sdk-python/     # Python SDK (`gateco` on PyPI) + CLI
│   └── sdk-typescript/ # TypeScript SDK (`@gateco/sdk` on npm)
├── validation_harness/ # Integration verification framework (21 scenarios, 17 profiles)
├── docs/               # Architecture docs & implementation plans
├── docker-compose.yml  # Local dev: frontend + backend + PostgreSQL 16
└── package.json        # Root workspace config (@gateco/root)
```

---

## Tech Stack

| Layer | Stack |
|-------|-------|
| Frontend | React 18, Vite 5, TypeScript 5.4+, Tailwind CSS 3, Zustand, TanStack Query, react-router-dom 6, shadcn/ui (Radix + CVA), vitest, msw (opt-in via `VITE_MSW=true`), Playwright (E2E) |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0 (async), asyncpg, Pydantic v2, Alembic, pgvector, ruff, pytest-asyncio |
| Website | Next.js 14, TypeScript, Tailwind CSS, MDX |
| Database | PostgreSQL 16 + pgvector |
| Payments | Stripe |
| Auth | JWT (python-jose), OAuth 2.0 (Google, GitHub), bcrypt |
| SDKs | Python SDK (httpx, pydantic v2), TypeScript SDK (native fetch, zero deps) |
| CLI | `gateco` CLI (click, built into Python SDK) |
| CI | GitHub Actions (`.github/workflows/test.yml`) |

---

## Quick Start

```bash
# Root — install all JS workspace deps
cd gateco && npm install

# Backend dev (port 8000) — start first, frontend connects to it by default
cd apps/backend && pip install -r requirements.txt
# Create .env with DATABASE_URL, JWT_SECRET_KEY (see Environment Variables section)
uvicorn src.gateco.main:app --reload --port 8000

# Frontend dev (port 5173) — connects to real backend via Vite proxy
cd apps/frontend && npm run dev

# Frontend with mock data only (no backend needed)
cd apps/frontend && VITE_MSW=true npm run dev

# Website dev (port 3001)
cd apps/website && npm run dev

# All at once via Docker
docker-compose up
```

**Default seed credentials:** `admin@acmecorp.com` / `password123` (Sarah Chen)

---

## Key Commands

### Frontend (`apps/frontend/`)
| Command | Purpose |
|---------|---------|
| `npm run dev` | Vite dev server (5173) |
| `npm run build` | `tsc && vite build` → `dist/` |
| `npm test` | Vitest (run) |
| `npm run test:coverage` | Vitest with coverage |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |

### Backend (`apps/backend/`)
| Command | Purpose |
|---------|---------|
| `make dev` | uvicorn with `--reload` |
| `pytest -v` | All tests |
| `pytest --cov=src/gateco` | Tests with coverage |
| `ruff check src/ tests/` | Linting |
| `alembic upgrade head` | Run migrations |
| `alembic revision --autogenerate -m "msg"` | Create migration |

### Website (`apps/website/`)
| Command | Purpose |
|---------|---------|
| `npm run dev` | Next.js dev (3001) |
| `npm run build` | Production build |
| `npm test` | Tests |

The website has two lead capture forms (contact page form and newsletter signup in the footer) that POST to `/api/lead`, which forwards submissions to the `LEAD_WEBHOOK_URL` environment variable.

### Python SDK (`packages/sdk-python/`)
| Command | Purpose |
|---------|---------|
| `pip install -e ".[dev]"` | Install SDK with dev deps |
| `pytest -v` | Run SDK tests (94 tests) |
| `gateco --help` | CLI tool (installed with SDK) |
| `gateco suggest-classifications <connector_id>` | Scan connector resources and suggest classifications |

### TypeScript SDK (`packages/sdk-typescript/`)
| Command | Purpose |
|---------|---------|
| `npm install` | Install deps |
| `npm run build` | Compile TypeScript |
| `npm test` | Run SDK tests (37 tests) |
| `npm run typecheck` | Type check without emit |

### Root workspace
| Command | Purpose |
|---------|---------|
| `npm run dev` | Frontend + Website concurrently |
| `npm run dev:all` | Frontend + Website + Backend |
| `npm run test:all` | All JS tests + pytest |
| `npm run build` | Build all packages & apps |

---

## Environment Variables

### Backend
| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/gateco_db` | Required. Must use `asyncpg` driver |
| `JWT_SECRET_KEY` | `(min 32 chars)` | Required for auth |
| `ADMIN_TOKEN` | `(string)` | Admin API access |
| `DEBUG` | `true` | Dev mode |

### Frontend
| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `http://localhost:8000` | Optional. When unset, API calls use relative `/api` path (Vite proxy forwards to backend). Only needed in production or non-proxy setups |
| `VITE_MSW` | `true` | Optional. Set to `true` to enable Mock Service Worker for offline/mock development. Off by default — frontend hits the real backend |

Vite proxy: `/api` requests are forwarded to the backend automatically in dev mode. The API client defaults to relative `/api` when `VITE_API_URL` is not set.

### Website
| Variable | Example | Notes |
|----------|---------|-------|
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3001` | Optional. Fallback: `https://gateco.ai`. Used for SEO metadata, sitemap, robots.txt |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3000` | Optional. Link target for "Go to App" CTAs |
| `LEAD_WEBHOOK_URL` | `https://your-webhook-endpoint.com/leads` | Required for lead capture. Contact form and newsletter POST to `/api/lead` which forwards to this URL |

---

## Architecture Essentials

### Backend Structure
```
apps/backend/src/gateco/
├── main.py              # FastAPI app entry point (loads .env via dotenv before imports)
├── startup.py           # App initialization
├── routes/
│   ├── connectors.py    # Connector CRUD + suggest-classifications + apply-suggestions
│   └── ...              # Other API route handlers
├── services/
│   ├── retrieval_service.py              # Retrieval pipeline, metadata resolution hierarchy
│   ├── binding_service.py                # Policy binding + semantic readiness (L0-L4)
│   ├── connector_service.py              # Connector CRUD + metadata_resolution_mode validation
│   ├── connector_adapters.py             # Connector adapters (Postgres inline metadata support)
│   ├── retroactive_service.py            # Retroactive registration (any connector with list adapter)
│   ├── classification_suggestion_service.py  # Rule-based classification suggestion engine
│   ├── idp_adapters/                     # Identity provider adapters (real IAM integrations)
│   │   ├── __init__.py                   # ADAPTER_CLASSES registry + _is_stub_config helper
│   │   ├── base.py                       # BaseIDPAdapter, SyncResult, SyncedPrincipal, SyncedGroup
│   │   ├── stub.py                       # Stub adapter for testing without real IAM
│   │   ├── okta.py                       # Okta adapter (SSWS auth, Management API)
│   │   ├── azure.py                      # Azure Entra ID adapter (MS Graph API)
│   │   ├── aws.py                        # AWS IAM Identity Center adapter (Identity Store API)
│   │   └── gcp.py                        # GCP Cloud Identity adapter (Admin SDK)
│   └── ...                               # Other business logic services
├── schemas/
│   ├── connectors.py    # Connector schemas (incl. metadata_resolution_mode, validation constants)
│   ├── suggestions.py   # ClassificationSuggestion request/response schemas
│   └── ...              # Other Pydantic v2 schemas
├── utils/               # Utilities (seed, security, crypto, patch)
├── exceptions.py        # Custom exception handlers
├── middleware/
│   ├── admin_auth.py    # Admin token auth
│   ├── jwt_auth.py      # JWT bearer auth
│   ├── entitlement.py   # Plan entitlement checks
│   ├── observability.py # Request-id + timing
│   └── rate_limit.py    # Rate limiting (relaxed to 50 attempts when DEBUG=true)
└── database/
    ├── connection.py    # Async engine + session factory (uses pydantic-settings, not raw os.getenv)
    ├── settings.py      # DatabaseSettings (pydantic-settings, reads .env)
    ├── vector.py        # pgvector integration
    ├── enums.py         # Shared enums
    └── models/
        ├── base.py      # Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin, OrganizationScopedMixin
        ├── user.py
        ├── organization.py
        ├── session.py
        ├── oauth_account.py
        ├── resource.py      # GatedResource
        ├── connector.py     # Connector model (incl. metadata_resolution_mode column)
        ├── access_rule.py
        ├── invite.py
        ├── subscription.py  # Billing
        ├── payment.py
        ├── invoice.py
        ├── usage.py         # UsageLog
        ├── coupon.py
        └── stripe_event.py
```

**Backend patterns:**
- `main.py` calls `load_dotenv()` before any other imports to ensure `.env` values are available to pydantic-settings and all modules
- `connection.py` uses `DatabaseSettings` (pydantic-settings) for the DB URL, not raw `os.getenv()`
- Logging level is `DEBUG` when `DEBUG=true` in `.env`, otherwise `INFO`
- Rate limiter relaxes to 50 max attempts (from 5) when `DEBUG=true`
- Backend serializers ensure no `null` values for array/date fields that the frontend iterates over (use `[]` or safe defaults)
- Seed data uses identity `admin@acmecorp.com` / `password123` / `Sarah Chen`

**Metadata Resolution Hierarchy:**
The retrieval service resolves policy-relevant metadata via a 3-step fallback hierarchy (configured per-connector via `metadata_resolution_mode`):
1. **`inline`** -- metadata extracted from the vector payload itself (requires `metadata_columns` in connector search config)
2. **`sql_view`** -- metadata read from a structured SQL view (Postgres-family connectors only; uses validated identifiers, never raw SQL)
3. **`sidecar`** -- metadata fetched from Gateco's own sidecar store (default, always available)
4. **`auto`** -- tries all three in order: inline, then sql_view, then sidecar

All resolved metadata is wrapped in a `ResolvedPolicySubject` dataclass -- a unified model consumed by the policy engine regardless of which resolution source produced it. The audit trail records `metadata_resolution_mode_used` for observability.

**Semantic Readiness Levels (L0-L4):**
`compute_policy_readiness()` in `binding_service.py` returns a semantic readiness level derived from connector **capability**, not coverage percentage (coverage is a separate operational metric):
| Level | Name | Meaning |
|-------|------|---------|
| L0 | Not Ready | No connection established |
| L1 | Connection Ready | Connector authenticated and reachable |
| L2 | Search Ready | Search/retrieval operations functional |
| L3 | Resource Policy | Resource-level policy bindings exist and active policies are configured |
| L4 | Chunk Policy | Chunk-level policy metadata available (highest granularity) |

**Retroactive Registration:**
Retroactive registration scans a connector's vector DB for unmanaged vectors and registers them as gated resources. It works for **any connector that has a `list_vector_ids` adapter** (defined in the `LISTERS` dict in `connector_adapters.py`), not just Tier 1 ingestion-capable connectors. This includes pgvector, Supabase, Neon, Qdrant, Pinecone, and any future connector with a lister adapter. The Qdrant lister gracefully returns `[]` on HTTP 404 (collection not found) instead of raising an error.

**Classification Suggestions:**
Rule-based MVP for suggesting data classifications on connector resources. Workflow: scan resources via keyword pattern matching, generate suggestions, admin reviews in UI, then applies accepted suggestions. Implemented in `classification_suggestion_service.py` with routes on the connector router (`POST /{connector_id}/suggest-classifications`, `POST /{connector_id}/apply-suggestions`).

**Model patterns:**
- All models inherit from `Base` (SQLAlchemy DeclarativeBase with UUID type mapping)
- Use `UUIDPrimaryKeyMixin` for UUID PKs (uuid4 default)
- Use `TimestampMixin` for `created_at` / `updated_at` (timezone-aware)
- Use `SoftDeleteMixin` for soft-delete (`.soft_delete()`, `.restore()`, `.is_deleted`)
- Use `OrganizationScopedMixin` for tenant-scoped models (FK -> organizations, indexed)
- Phased model organization: Phase 1 (Auth), Phase 2 (Resources), Phase 3 (Billing)

### Frontend Structure
```
apps/frontend/src/
├── main.tsx             # Entry point (MSW opt-in via VITE_MSW=true; cleans up stale SW when off)
├── App.tsx              # Root component
├── admin/               # DB setup wizard (admin panel)
├── api/
│   ├── client.ts        # API client (defaults to relative /api, uses Vite proxy)
│   ├── auth.ts          # Auth API (login, signup, exchangeCode for OAuth)
│   ├── connectors.ts    # Connectors CRUD + suggestClassifications() + applySuggestions()
│   ├── identity-providers.ts
│   ├── pipelines.ts
│   ├── policies.ts
│   ├── data-catalog.ts
│   ├── dashboard.ts
│   ├── billing.ts
│   └── queryKeys.ts     # TanStack Query key constants
├── components/
│   ├── auth/            # OAuth buttons, login/signup forms
│   ├── billing/         # PlanBadge, UsageMeter, UpgradeModal, EntitlementGate, PlanCard
│   ├── layout/          # AppShell (wraps Outlet in ErrorBoundary), Sidebar, TopNav, UserMenu
│   ├── shared/          # ErrorBoundary, StatusBadge, DataTable, EmptyState, etc.
│   └── ui/              # shadcn/ui primitives (button, card, input, badge, skeleton, dialog)
├── contexts/            # EntitlementContext
├── pages/               # Page components (dashboard, audit-log, access-simulator, etc.)
│   ├── connectors/
│   │   └── ConnectorsPage.tsx       # L0-L4 readiness badges, suggest-classifications button
│   └── SuggestionReviewDialog.tsx   # Dialog for reviewing/applying classification suggestions
├── types/
│   └── connector.ts     # MetadataResolutionMode, PolicyReadinessLevel (0-4), suggestion types
├── routes/              # Router config, ProtectedRoute
└── lib/utils.ts         # cn() utility
```

**Frontend patterns:**
- Path alias: `@/` -> `src/` (configured in vite.config.ts + tsconfig.json)
- UI components use shadcn/ui conventions (Radix + CVA + tailwind-merge)
- Tailwind uses CSS custom properties for theming (`hsl(var(--primary))` pattern)
- Dark mode via `class` strategy
- Font: Inter
- **MSW is opt-in only** (`VITE_MSW=true`) -- by default the frontend connects to the real backend via Vite proxy
- **API response unwrapping** -- all API functions extract `.data` from the backend's `{ data: [...] }` envelope responses
- **ErrorBoundary** wraps the main content area in AppShell, keyed by `location.pathname` to reset on navigation
- **OAuth flow** uses auth code exchange pattern: frontend receives `code` param, calls `POST /auth/exchange` to get tokens
- **Connector readiness badges** -- ConnectorsPage displays L0-L4 semantic readiness with color-coded badges and tooltips explaining each level
- **Classification suggestion workflow** -- "Suggest Classifications" button on connector rows triggers scan, results shown in `SuggestionReviewDialog` for admin review and selective application

### Entitlement-Driven UI (Planned)
See `UI-Spec.md` for the complete frontend spec. Key concepts:
- All feature gating derives from a runtime `entitlements` object (fetched via `GET /me`)
- `EntitlementGate` component wraps any feature (disable/hide/replace modes)
- `UpgradeModal` is a shared component; content sourced from `planFeatures.ts` catalog
- `UsageMeter` shown on Dashboard + Billing page with plan-specific display rules
- No hardcoded plan behavior in screens

---

## Code Conventions

### TypeScript / Frontend
- **Strict mode** enabled (`noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`)
- `const` over `let`, no `var`
- camelCase for variables/functions, PascalCase for types/interfaces/components, UPPER_SNAKE_CASE for constants
- One main export per file
- JSDoc for public functions

### Python / Backend
- **ruff** for linting + formatting (line-length 100, rules: E, F, I, N, W)
- **pytest** with `asyncio_mode = "auto"`
- **pydantic-settings** for config (reads `.env`)
- Alembic migrations in `migrations/` directory (relative to `apps/backend/`)
- Docstrings on all classes and public functions

---

## CI / Testing

GitHub Actions workflow (`.github/workflows/test.yml`):
1. **Backend tests** — pytest with coverage against Postgres 16 service container
2. **Frontend tests** — lint + typecheck + vitest with coverage
3. **Website tests** — npm test
4. **E2E tests** — Playwright (Chromium), depends on backend + frontend passing
5. **Build check** — builds all packages + frontend + website
6. **Pinecone validation** — conditional on `PINECONE_API_KEY` secret; runs validation harness against real Pinecone cloud
7. **Okta validation** — conditional on `OKTA_API_TOKEN` secret; seeds Okta sandbox via `scripts/seed_okta.py`, runs validation harness against real Okta, tears down with `if: always()`

Branches: `main`, `develop`. PRs and pushes trigger CI.

### Validation Harness (`validation_harness/`)
| Command | Purpose |
|---------|---------|
| `pip install -e ".[dev]"` | Install harness with dev deps |
| `gateco-validate run -p profiles/local-dev.yaml` | Run all scenarios against local pgvector |
| `gateco-validate doctor -p profiles/local-dev.yaml` | Preflight connectivity check |
| `gateco-validate list-scenarios` | Show all 21 scenarios with deps |
| `pytest -v` | Run harness unit tests (71 tests) |

21 scenarios across 15 feature areas (health, auth, connectors, ingestion, retroactive, data_catalog, policies, retrievals, metadata_resolution, simulator, audit, readiness, dashboard, billing, identity_providers). Scenarios use capability-gated skips and cascading dependency skips (see `skip_taxonomy.py`).

**Profiles** (in `validation_harness/profiles/`):
- `local-dev.yaml` -- pgvector against local backend
- `ci-pgvector.yaml`, `ci-supabase.yaml`, `ci-neon.yaml`, `ci-qdrant.yaml`, `ci-pinecone.yaml` -- CI connector profiles
- `ci-okta.yaml`, `ci-azure.yaml`, `ci-aws-iam.yaml`, `ci-gcp.yaml` -- CI IDP profiles (pgvector + real IAM provider)
- `local-pinecone-local.yaml` -- Pinecone Local emulator (Docker, no API key)
- `local-pinecone.yaml`, `local-weaviate.yaml`, `local-milvus.yaml`, `local-chroma.yaml`, `local-opensearch.yaml` -- other local profiles

**Connector defaults** (`connector_defaults.py`): Per-connector search/ingestion config defaults for all 9 connector types. Use `get_search_config_defaults(type)` and `get_ingestion_config_defaults(type)` instead of hardcoding pgvector-specific config.

**Skip taxonomy** (`skip_taxonomy.py`): Machine-readable reasons for skips -- `UNSUPPORTED_CONNECTOR_CAPABILITY`, `UNSUPPORTED_CONNECTOR_TIER`, `MISSING_ENTITLEMENT`, `MISSING_EXTERNAL_CREDENTIALS`, `PROFILE_DISABLED_FEATURE`, `ENVIRONMENT_NOT_CONFIGURED`, `NOT_YET_SUPPORTED_BY_BACKEND`, `DEPENDENCY_FAILED`, `NO_TEST_DATA_AVAILABLE`.

**Cascading dependency skips**: When a scenario is skipped (e.g., s04/s05 ingestion skipped due to missing capability), downstream scenarios that depend on its test data are automatically skipped with `NO_TEST_DATA_AVAILABLE` instead of failing with assertion errors. Configured via `skip_when_dependency_skipped` on the `@scenario` decorator.

---

## Database

- PostgreSQL 16 with pgvector extension
- Connection string must use `postgresql+asyncpg://` scheme
- Docker compose provides local Postgres on port 5432 (user/pass: `postgres/postgres`, db: `gateco_db`)
- Alembic for schema migrations (`apps/backend/alembic.ini`, `migrations/` dir)
- All FKs use UUID; organization-scoped models cascade on org delete
- Notable migrations: `015_add_metadata_resolution_mode.py` adds `metadata_resolution_mode` column (String(20), default `"sidecar"`) to the connectors table

---

## Important Reference Docs

| Doc | Location | Purpose |
|-----|----------|---------|
| Architecture | `docs/ARCHITECTURE.md` | Full system topology, API contracts, auth model, data models |
| UI Spec | `UI-Spec.md` | Frontend entitlement gating, billing UI, pricing page spec |
| Implementation Plans | `docs/plans/` | Role-specific plans (backend, frontend, DB, QA, marketing, etc.) |
| Entitlement Gating | `docs/interaction-patterns/ENTITLEMENT_GATING.md` | Gating interaction patterns |
| LLM Context (short) | `apps/website/public/llms.txt` | Concise overview for LLMs per llms.txt convention |
| LLM Context (full) | `apps/website/public/llms-full.txt` | Comprehensive single-file context for LLM integrations |
| Validation Harness | `validation_harness/README.md` | Integration verification framework (21 scenarios, 17 profiles) |

---

## Common Pitfalls

- Backend `DATABASE_URL` **must** use `postgresql+asyncpg://`, not `postgresql://`
- Frontend proxy only works in dev mode -- production needs proper API URL config via `VITE_API_URL`
- `npm ci` at root installs all workspace deps; individual `cd apps/X && npm install` is not needed for JS apps
- Backend Python deps are separate -- `pip install -r apps/backend/requirements.txt`
- pgvector extension must be enabled in Postgres before running migrations
- Tailwind config uses CSS variables for colors -- do not use raw color values
- **MSW is off by default** -- if you need mock data for frontend-only development, set `VITE_MSW=true`. When MSW is off, stale service workers are automatically cleaned up
- **Backend API responses are enveloped** -- list endpoints return `{ data: [...] }`. All frontend API functions must extract `.data` from the response before returning
- **OAuth callback expects `code` param** -- the frontend `OAuthCallbackPage` reads a `code` query parameter and exchanges it via `POST /auth/exchange`, not raw token params
- **Do not use `os.getenv("DATABASE_URL")` directly in backend code** -- use `DatabaseSettings` from pydantic-settings to read config; `main.py` loads `.env` via `dotenv` at startup
- **`metadata_resolution_mode` is validated per connector type** -- `sql_view` mode is only valid for Postgres-family connectors (defined in `POSTGRES_FAMILY_TYPES`). The backend rejects invalid combinations via `_validate_metadata_resolution_mode()`. Valid modes: `sidecar`, `inline`, `sql_view`, `auto`
- **SQL view identifiers must be validated, never raw SQL** -- the `sql_view` metadata resolution mode uses structured config with validated identifiers (table/column names). Never pass raw SQL strings in connector configuration
- **Readiness level is semantic, not coverage** -- `policy_readiness_level` (L0-L4) reflects connector capability progression, not a percentage. Do not conflate it with coverage metrics, which are a separate operational dimension
- **Classification suggestions are rule-based MVP** -- the suggestion engine uses keyword pattern matching, not ML. Suggestions always require admin review before application. Both SDK clients and the CLI expose this workflow
- **Policy condition fields require `resource.` or `principal.` prefix** -- bare field names (e.g., `classification`) silently resolve against the principal, not the resource. Always use `resource.classification`, `resource.sensitivity`, `resource.domain`, `resource.labels`, `resource.encryption_mode` for resource checks. Use `principal.roles`, `principal.groups`, `principal.attributes.*` for principal checks. Backend: `policy_engine.py:132-137`
- **Deny policies apply default effect when no rules match** -- if a deny policy's selectors match but none of its rules match, the policy-level `effect=deny` fires (`policy_engine.py:79`). To deny only specific conditions, add a catch-all allow rule at lowest priority
- **Website domain is `gateco.ai`** -- all public URLs, email addresses, and SEO metadata use `gateco.ai` (not `gateco.com`). Fallback URLs in metadata/sitemap/robots default to `https://gateco.ai`
- **Website lead capture requires `LEAD_WEBHOOK_URL`** -- both the contact form and newsletter signup POST to `/api/lead` which forwards to the `LEAD_WEBHOOK_URL` env var. Without it, form submissions will fail silently on the server side
- **Retroactive registration is not Tier 1 restricted** -- it works for any connector that has a `list_vector_ids` adapter in `LISTERS` (connector_adapters.py), not just ingestion-capable Tier 1 connectors. Do not gate retroactive registration on `TIER_1_CONNECTORS`
- **Qdrant lister returns `[]` on 404** -- when the Qdrant collection does not exist yet, `_list_qdrant_ids` returns an empty list instead of raising an error. This allows retroactive registration to run gracefully on new connectors
- **Validation harness scenarios without test data should SKIP, not fail** -- if a dependency scenario was skipped (e.g., ingestion skipped for capability reasons), downstream scenarios that need its data must use `skip_when_dependency_skipped` to cascade the skip with `NO_TEST_DATA_AVAILABLE` reason
- **AWS IDP adapter maps `UserType` to `department`** -- AWS IAM Identity Center has no native department field. The adapter reads `UserType` as `department` in `attributes` (Gateco test convention). Seed scripts and test data must set `UserType` for department-based policy tests to work
- **Okta CI validation requires seed data** -- the `scripts/seed_okta.py` script provisions 5 `vh-*` test users and 2 groups in the Okta sandbox before running validation. Teardown runs with `if: always()` to clean up even on failure. Requires `OKTA_DOMAIN` and `OKTA_API_TOKEN` secrets
- **Update `llms.txt` and `llms-full.txt`** in `apps/website/public/` when SDK methods, API endpoints, connector types, or plan limits change
