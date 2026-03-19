# Gateco Validation Harness

Integration verification framework that exercises Gateco end-to-end across connectors, IAM, policies, retrievals, and reporting. Produces structured reports showing cumulative readiness and coverage.

## Quick Start

```bash
# Install
cd gateco/validation_harness
pip install -e ".[dev]"

# Preflight check
gateco-validate doctor --profile profiles/local-dev.yaml

# Run all scenarios
gateco-validate run --profile profiles/local-dev.yaml --format all

# Run specific scenarios
gateco-validate run -p profiles/local-dev.yaml -s s00_health,s01_auth

# Run by feature area
gateco-validate run -p profiles/local-dev.yaml -f auth
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `run` | Execute validation scenarios |
| `list-scenarios` | Show all registered scenarios with deps |
| `list-features` | Show feature areas |
| `list-capabilities --connector <type>` | Show connector capabilities |
| `status` | Cumulative coverage matrix |
| `report [run_id]` | View past run report |
| `compare --run-a X --run-b Y` | Diff two runs |
| `cleanup-only -p <profile>` | Delete vh- resources only |
| `rerun-failed --from-run <id> -p <profile>` | Retry failed scenarios |
| `doctor -p <profile>` | Preflight connectivity check |

## Scenarios

21 scenarios across 15 feature areas:

| ID | Name | Feature | Requires |
|----|------|---------|----------|
| s00 | Health Check | health | - |
| s01 | Authentication | auth | s00 |
| s02 | Connector Lifecycle | connectors | s01 |
| s03 | Connector Config | connectors | s02 |
| s04 | Single Ingestion | ingestion | s02 + direct_ingestion cap |
| s05 | Batch Ingestion | ingestion | s04 + batch_ingestion cap |
| s06 | Retroactive Register | retroactive | s02 + retroactive cap |
| s07 | Data Catalog | data_catalog | s02 |
| s08 | Policy Lifecycle | policies | s02 |
| s09 | Retrieval Allowed | retrievals | s08; cascading skip if s05 skipped |
| s10 | Retrieval Denied | retrievals | s08; cascading skip if s05 skipped |
| s11 | Retrieval Partial | retrievals | s08; cascading skip if s05 skipped |
| s12 | Metadata Resolution | metadata_resolution | s08 |
| s13 | Simulator | simulator | s08 + simulator cap |
| s14 | Audit Trail | audit | s01 |
| s15 | Coverage Readiness | readiness | s01 |
| s16 | Dashboard | dashboard | s01 |
| s17 | Billing Read-Only | billing | s01 |
| s18 | IDP Lifecycle | identity_providers | s01 |
| s19 | Principal-Scoped Policies | policies | s18 |
| s20 | Principal-Based Retrieval | retrievals | s19; cascading skip if s05 skipped |

## Profiles

Profiles are YAML files with environment variable interpolation (`${VAR:-default}`):

```yaml
profile_name: local-dev
base_url: "${GATECO_BASE_URL:-http://localhost:8000}"
credentials:
  email: "${GATECO_EMAIL:-admin@acmecorp.com}"
  password: "${GATECO_PASSWORD:-password123}"
connector:
  type: pgvector
features:
  auth: true
  ingestion: true
  # ... toggle feature areas
```

### Available Profiles

| Profile | Connector | Mode | Notes |
|---------|-----------|------|-------|
| `local-dev.yaml` | pgvector | Local | Default local development |
| `ci-pgvector.yaml` | pgvector | CI | GitHub Actions service container |
| `ci-supabase.yaml` | supabase | CI | Emulated (local Postgres) |
| `ci-neon.yaml` | neon | CI | Emulated (local Postgres) |
| `ci-qdrant.yaml` | qdrant | CI | Real Qdrant container |
| `ci-pinecone.yaml` | pinecone | CI (conditional) | Real Pinecone cloud, requires `PINECONE_API_KEY` secret |
| `ci-okta.yaml` | pgvector + Okta IDP | CI (conditional) | Real Okta sandbox, requires `OKTA_DOMAIN` + `OKTA_API_TOKEN` secrets |
| `ci-azure.yaml` | pgvector + Azure IDP | CI (conditional) | Real Azure Entra ID, requires `AZURE_*` secrets |
| `ci-aws-iam.yaml` | pgvector + AWS IDP | CI (conditional) | Real AWS IAM Identity Center, requires `AWS_*` secrets |
| `ci-gcp.yaml` | pgvector + GCP IDP | CI (conditional) | Real GCP Cloud Identity, requires `GCP_*` secrets |
| `local-pinecone-local.yaml` | pinecone | Emulator | Pinecone Local (Docker), no API key needed |
| `local-pinecone.yaml` | pinecone | Local | Requires Pinecone credentials |
| `local-weaviate.yaml` | weaviate | Local | Weaviate container |
| `local-milvus.yaml` | milvus | Local | Milvus container |
| `local-chroma.yaml` | chroma | Local | Chroma container |
| `local-opensearch.yaml` | opensearch | Local | OpenSearch container |

## Reports

- **Console**: Rich terminal tables with color-coded status
- **JSON**: Full `run_result.json` + `created_resources.json` manifest
- **Markdown**: 9-section report (summary, scenarios, features, readiness, regression, coverage)

## Skip Taxonomy

Scenarios can be skipped for machine-readable reasons (see `skip_taxonomy.py`):

| Reason | Meaning |
|--------|---------|
| `unsupported_connector_capability` | Connector lacks required capability (e.g., `direct_ingestion`) |
| `unsupported_connector_tier` | Connector tier does not support the feature |
| `missing_entitlement` | Plan entitlement not available |
| `missing_external_credentials` | External service credentials not configured |
| `profile_disabled_feature` | Feature area disabled in profile YAML |
| `environment_not_configured` | Required environment setup missing |
| `not_yet_supported_by_backend` | Backend has not implemented the feature yet |
| `dependency_failed` | A required dependency scenario failed |
| `no_test_data_available` | A dependency was skipped, so test data it would have created does not exist |

### Cascading Dependency Skips

When a scenario is skipped (e.g., s04/s05 ingestion skipped because the connector lacks `direct_ingestion` capability), downstream scenarios that depend on the test data it would have created are automatically skipped with `NO_TEST_DATA_AVAILABLE`. This prevents false assertion failures.

Configure via `skip_when_dependency_skipped` on the `@scenario` decorator:

```python
@scenario(
    id="s09",
    name="Retrieval Allowed",
    depends_on=["s08_policy_lifecycle"],
    skip_when_dependency_skipped=["s05_ingest_batch"],
)
```

## Connector Config Defaults

Per-connector-type search and ingestion config defaults are centralized in `connector_defaults.py`. All 9 connector types have search config defaults; ingestion config defaults exist for connectors that support direct ingestion (pgvector, supabase, neon, pinecone).

Helper functions:
- `get_search_config_defaults(connector_type)` -- returns search config dict
- `get_ingestion_config_defaults(connector_type)` -- returns ingestion config dict

Scenarios s03 and s04 use these helpers instead of hardcoding pgvector-specific configuration.

## Verified Results

| Connector | Pass | Skip | Notes |
|-----------|------|------|-------|
| pgvector | 21/21 | 0 | Full pass |
| supabase (emulated) | 21/21 | 0 | Full pass |
| neon (emulated) | 21/21 | 0 | Full pass |
| qdrant | 13/21 | 8 | s04/s05 capability-gated; s09/s10/s11/s20 cascading skip |
| okta (real sandbox) | 13/21 | 5 | s04 ingestion fail; s05/s09/s10/s11/s20 cascading skip |
| Unit tests | 71/71 | 0 | Includes `TestConnectorDefaultsParity` (3 tests), `TestProfileAdapterRouting` (24 tests) |

## Scripts

Helper scripts for CI and local testing live in `scripts/`:

| Script | Purpose |
|--------|---------|
| `seed_okta.py` | Provision 5 `vh-*` test users + 2 groups in an Okta sandbox (SSWS auth). Supports `--teardown` flag. Used by CI before/after Okta validation. |

```bash
# Seed Okta test data
python scripts/seed_okta.py --domain dev-12345678.okta.com --api-token 00abc...

# Tear down after validation
python scripts/seed_okta.py --domain dev-12345678.okta.com --api-token 00abc... --teardown
```

## Architecture

```
CLI (Click) → Engine (orchestrator) → Scenarios (registered functions)
                                          ↓
                                    EvidenceCapturingTransport
                                          ↓
                                    AsyncGatecoClient (SDK)
                                          ↓
                                    Gateco Backend (FastAPI)
```

## Tests

```bash
cd gateco/validation_harness
pytest -v
```
