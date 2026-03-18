import type { Metadata } from 'next';
import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Documentation',
  description:
    'Gateco documentation. Learn how to integrate permission-aware retrieval into your AI systems with Python and TypeScript SDKs.',
};

const sections = [
  {
    id: 'quick-start',
    title: 'Quick Start',
    description:
      'Get permission-aware retrieval running in under five minutes. Install the SDK, connect your vector database, and execute your first secured retrieval.',
    subsections: [
      {
        title: 'Python',
        code: `pip install gateco-sdk`,
        example: `from gateco_sdk import GatecoClient

with GatecoClient("https://api.gateco.dev") as client:
    client.login("admin@company.com", "password")

    # Execute a permission-aware retrieval
    result = client.retrievals.execute(
        connector_id="conn_abc",
        principal_id="user_123",
        query_vector=[0.1, 0.2, 0.3, ...],
        top_k=10,
    )

    for item in result.results:
        print(item.vector_id, item.score)`,
      },
      {
        title: 'TypeScript',
        code: `npm install @gateco/sdk`,
        example: `import { GatecoClient } from "@gateco/sdk";

const client = new GatecoClient({
  baseUrl: "https://api.gateco.dev",
});
await client.login("admin@company.com", "password");

// Execute a permission-aware retrieval
const result = await client.retrievals.execute({
  connectorId: "conn_abc",
  principalId: "user_123",
  queryVector: [0.1, 0.2, 0.3],
  topK: 10,
});

for (const item of result.results) {
  console.log(item.vectorId, item.score);
}
client.close();`,
      },
      {
        title: 'CLI',
        code: `pip install gateco-sdk

# Login
gateco login --email admin@company.com --password secret

# Test your connector
gateco connectors test conn_abc

# Execute a retrieval
gateco retrieve --connector-id conn_abc \\
  --principal-id user_123 \\
  --vector-file embedding.json --top-k 10`,
      },
    ],
  },
  {
    id: 'core-concepts',
    title: 'Core Concepts',
    description:
      'Gateco is a permission-aware retrieval layer — the security middleware between your AI agents and vector databases. It enforces access policies at retrieval time using a deny-by-default model.',
    concepts: [
      {
        name: 'Connectors',
        detail:
          'Connections to your vector databases. Gateco supports 9 connectors: pgvector, Pinecone, Qdrant, Weaviate, Milvus, Chroma, OpenSearch, Supabase, and Neon. Tier 1 connectors (pgvector, Supabase, Neon, Pinecone, Qdrant) support full ingestion workflows.',
      },
      {
        name: 'Policies',
        detail:
          'Rules that determine who can access what data. Gateco supports RBAC (role-based), ABAC (attribute-based), and REBAC (relationship-based) policies. Policies have a lifecycle: Draft → Active → Archived. Only active policies are enforced.',
      },
      {
        name: 'Secured Retrievals',
        detail:
          'Permission-checked queries against your vector database. Every retrieval evaluates all active policies against the requesting principal and target resources. Outcomes are: Allowed (all results pass), Partial (some filtered), or Denied (no access).',
      },
      {
        name: 'Principals',
        detail:
          'The identities requesting access — users, service accounts, or AI agents. Principals are synced from your identity providers (Azure Entra ID, AWS IAM, Okta, GCP) or managed directly.',
      },
      {
        name: 'Gated Resources',
        detail:
          'Your vector data with security metadata attached — classification (public/internal/confidential/restricted), sensitivity (low/medium/high/critical), domain, and ownership. Resources are bound to connectors.',
      },
      {
        name: 'Readiness Levels (L0-L4)',
        detail:
          'A semantic measure of your security posture per connector. L0: Not connected. L1: Connection verified. L2: Search operational. L3: Resource-level policies active. L4: Chunk-level enforcement (highest granularity).',
      },
    ],
  },
  {
    id: 'connectors',
    title: 'Connectors',
    description:
      'Connect Gateco to your vector database. Each connector manages connection credentials, search configuration, and metadata resolution.',
    subsections: [
      {
        title: 'Create a Connector',
        example: `# Python
connector = client.connectors.create(
    name="Production Pinecone",
    type="pinecone",
    config={
        "api_key": "pk-...",
        "environment": "us-east-1",
        "index_name": "knowledge-base",
    },
)

# Test the connection
result = client.connectors.test(connector.id)
print(result.status, result.latency_ms)`,
      },
      {
        title: 'Supported Connectors',
        table: {
          headers: ['Connector', 'Type', 'Tier', 'Ingestion Support'],
          rows: [
            ['pgvector', 'pgvector', 'Tier 1', 'Full'],
            ['Supabase', 'supabase', 'Tier 1', 'Full'],
            ['Neon', 'neon', 'Tier 1', 'Full'],
            ['Pinecone', 'pinecone', 'Tier 1', 'Full'],
            ['Qdrant', 'qdrant', 'Tier 1', 'Full'],
            ['OpenSearch', 'opensearch', 'Tier 2', 'Retroactive only'],
            ['Weaviate', 'weaviate', 'Tier 2', 'Retroactive only'],
            ['Milvus', 'milvus', 'Tier 2', 'Retroactive only'],
            ['Chroma', 'chroma', 'Tier 2', 'Retroactive only'],
          ],
        },
      },
      {
        title: 'Metadata Resolution Modes',
        detail:
          'Gateco resolves policy-relevant metadata via a configurable hierarchy per connector:',
        list: [
          'sidecar (default) — Metadata managed in Gateco\'s own registry',
          'inline — Metadata extracted from vector payloads (requires metadata_field_mapping)',
          'sql_view — Metadata read from a Postgres view (Postgres-family connectors only)',
          'auto — Tries inline → sql_view → sidecar in order',
        ],
      },
    ],
  },
  {
    id: 'policies',
    title: 'Policies',
    description:
      'Define who can access what data through RBAC and ABAC policies. Policies are evaluated at every retrieval in a deny-by-default model.',
    subsections: [
      {
        title: 'Create a Policy',
        example: `# Python — RBAC policy with proper condition format
policy = client.policies.create(
    name="Engineering Data Access",
    type="rbac",
    effect="allow",
    description="Allow engineering team to access internal docs",
    resource_selectors=["connector_abc"],
    rules=[{
        "effect": "allow",
        "priority": 1,
        "description": "Engineers can access internal docs",
        "conditions": [
            # resource. prefix = check resource metadata
            {"field": "resource.classification", "operator": "lte", "value": "internal"},
            # principal. prefix = check requesting identity
            {"field": "principal.roles", "operator": "contains", "value": "engineer"},
        ],
    }],
)

# Activate the policy
client.policies.activate(policy.id)`,
      },
      {
        title: 'Policy Lifecycle',
        detail: 'Policies go through three states:',
        list: [
          'Draft — Created but not enforced. Safe to edit and test.',
          'Active — Enforced on all retrievals. Use the Access Simulator (Pro) to test before activating.',
          'Archived — Retained for audit history but no longer enforced.',
        ],
      },
      {
        title: 'Policy Condition Fields',
        detail: 'Condition fields MUST be prefixed with resource. or principal. — bare field names silently resolve against the principal, not the resource.',
        list: [
          'Resource fields: resource.classification, resource.sensitivity, resource.domain, resource.labels, resource.encryption_mode',
          'Principal fields: principal.roles, principal.groups, principal.attributes.*',
          'Operators: eq, ne, in, contains, lte (ordered level comparison), gte (ordered level comparison)',
          'WARNING: Bare field names (e.g., "classification" without prefix) check principal attributes, not resource metadata',
          'Deny policy gotcha: when a deny policy\'s selectors match but no rules match, the policy-level effect=deny fires. Add a catch-all allow rule to deny only specific conditions.',
        ],
      },
    ],
  },
  {
    id: 'ingestion',
    title: 'Ingestion',
    description:
      'Ingest documents with security metadata attached. Available for Tier 1 connectors (pgvector, Supabase, Neon, Pinecone, Qdrant).',
    subsections: [
      {
        title: 'Single Document',
        example: `response = client.ingest.document(
    connector_id="conn_abc",
    external_resource_id="doc-quarterly-report",
    text="Q4 2025 financial results...",
    classification="confidential",
    sensitivity="high",
    domain="finance",
    labels=["quarterly", "financial"],
    owner_principal_id="user_cfo",
)
print(f"Ingested {response.chunk_count} chunks")`,
      },
      {
        title: 'Batch Ingestion',
        example: `response = client.ingest.batch(
    connector_id="conn_abc",
    records=[
        {
            "external_resource_id": "doc-001",
            "text": "First document content...",
            "classification": "internal",
        },
        {
            "external_resource_id": "doc-002",
            "text": "Second document content...",
            "classification": "public",
        },
    ],
)
print(f"Ingested {response.total_chunks} total chunks")`,
      },
      {
        title: 'CLI Ingestion',
        example: `# Single file
gateco ingest report.txt --connector-id conn_abc \\
  --classification confidential --sensitivity high

# Batch directory
gateco ingest-batch ./documents --connector-id conn_abc \\
  --glob "*.md"`,
      },
    ],
  },
  {
    id: 'classification',
    title: 'Classification Suggestions',
    description:
      'Automatically scan your connector resources and get rule-based classification suggestions. Review suggestions, then apply the ones you approve.',
    subsections: [
      {
        title: 'Suggest & Apply',
        example: `# Scan resources and get suggestions
suggestions = client.connectors.suggest_classifications(
    connector_id="conn_abc",
    scan_limit=1000,
    sample_size=10,
)

for s in suggestions.suggestions:
    print(f"{s.resource_key}: {s.suggested_classification} "
          f"({s.confidence:.0%}) — {s.reasoning}")

# Apply approved suggestions
result = client.connectors.apply_suggestions(
    connector_id="conn_abc",
    suggestions=suggestions.suggestions,
)
print(f"Applied {result.applied}, created {result.resources_created} resources")`,
      },
      {
        title: 'Classification Levels',
        table: {
          headers: ['Classification', 'Sensitivity Levels', 'Example'],
          rows: [
            ['Public', 'Low', 'Blog posts, FAQs, product docs'],
            ['Internal', 'Medium', 'Wiki pages, onboarding materials'],
            ['Confidential', 'High', 'HR records, employee data'],
            ['Restricted', 'Critical', 'Financial reports, legal contracts'],
          ],
        },
      },
    ],
  },
  {
    id: 'simulator',
    title: 'Access Simulator',
    description:
      'Dry-run policy evaluation to test what a principal can access before going live. Available on Pro and Enterprise plans.',
    subsections: [
      {
        title: 'Run a Simulation',
        example: `# Python
result = client.simulator.run(
    principal_id="user_123",
    connector_id="conn_abc",
)

print(f"Matched: {result.matched_count}")
print(f"Allowed: {result.allowed_count}")
print(f"Denied: {result.denied_count}")

for trace in result.traces:
    print(f"  {trace.resource_id}: {trace.decision} — {trace.reason}")`,
      },
    ],
  },
  {
    id: 'audit',
    title: 'Audit Trail',
    description:
      'Every operation is logged with 25 event types covering retrievals, policy changes, connector operations, ingestion, and more. Export as CSV/JSON (Pro) or stream to your SIEM (Enterprise).',
    subsections: [
      {
        title: 'Query Audit Events',
        example: `# List recent retrieval events
page = client.audit.list(
    event_types="retrieval_allowed,retrieval_denied",
    per_page=50,
)

for event in page.items:
    print(f"{event.event_type} by {event.actor} at {event.created_at}")

# Export (Pro tier)
export = client.audit.export_csv(
    date_from="2025-01-01",
    date_to="2025-03-31",
    format="csv",
)`,
      },
      {
        title: 'Event Types',
        detail: 'Audit events are grouped into categories:',
        list: [
          'User — login, logout, settings_changed',
          'Connector — added, updated, tested, removed, sync events',
          'Policy — created, updated, activated, archived, deleted',
          'Retrieval — allowed, denied (with full policy trace)',
          'Data — metadata_bound, document_ingested, batch_ingested',
          'Identity Provider — added, updated, removed, synced',
          'Pipeline — created, updated, run, error',
        ],
      },
    ],
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    description:
      'The Gateco REST API provides 50+ endpoints across 17 route modules. All endpoints require JWT authentication (obtained via login) or a static API key. Requests and responses use JSON.',
    subsections: [
      {
        title: 'Authentication',
        example: `# Login to get JWT tokens
curl -X POST https://api.gateco.dev/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"admin@company.com","password":"secret"}'

# Use the access token
curl https://api.gateco.dev/api/connectors \\
  -H "Authorization: Bearer <access_token>"`,
      },
      {
        title: 'Key Endpoints',
        table: {
          headers: ['Method', 'Path', 'Description'],
          rows: [
            ['POST', '/api/auth/login', 'Authenticate and get tokens'],
            ['GET', '/api/connectors', 'List connectors'],
            ['POST', '/api/connectors', 'Create connector'],
            ['POST', '/api/connectors/:id/test', 'Test connectivity'],
            ['POST', '/api/connectors/:id/bind', 'Bind metadata to resources'],
            ['POST', '/api/connectors/:id/suggest-classifications', 'Get classification suggestions'],
            ['POST', '/api/connectors/:id/apply-suggestions', 'Apply approved suggestions'],
            ['GET', '/api/policies', 'List policies'],
            ['POST', '/api/policies', 'Create policy'],
            ['POST', '/api/policies/:id/activate', 'Activate a policy'],
            ['POST', '/api/retrievals/execute', 'Execute secured retrieval'],
            ['GET', '/api/retrievals', 'List past retrievals'],
            ['POST', '/api/ingest/document', 'Ingest single document'],
            ['POST', '/api/ingest/batch', 'Batch ingest documents'],
            ['POST', '/api/simulator/run', 'Run access simulation (Pro)'],
            ['GET', '/api/audit-log', 'List audit events'],
            ['POST', '/api/audit-log/export', 'Export audit log (Pro)'],
            ['GET', '/api/identity-providers', 'List identity providers'],
            ['POST', '/api/retroactive/register', 'Register existing vectors'],
          ],
        },
      },
      {
        title: 'Rate Limits & Plan Limits',
        table: {
          headers: ['Resource', 'Free', 'Pro', 'Enterprise'],
          rows: [
            ['Secured retrievals/mo', '100', '10,000', 'Unlimited'],
            ['Connectors', '1', '5', 'Unlimited'],
            ['Identity providers', '1', '3', 'Unlimited'],
            ['Policies', '3', 'Unlimited', 'Unlimited'],
            ['Team members', '1', '10', 'Unlimited'],
          ],
        },
      },
    ],
  },
  {
    id: 'identity-providers',
    title: 'Identity Providers',
    description:
      'Sync principals from your existing identity infrastructure. Gateco supports four identity provider types.',
    subsections: [
      {
        title: 'Supported Providers',
        table: {
          headers: ['Provider', 'Type Value', 'Tier'],
          rows: [
            ['Azure Entra ID', 'azure_entra_id', 'Pro+'],
            ['AWS IAM', 'aws_iam', 'Pro+'],
            ['Okta', 'okta', 'Pro+'],
            ['GCP', 'gcp', 'Pro+'],
          ],
        },
      },
      {
        title: 'Configure a Provider',
        example: `# Python
idp = client.identity_providers.create(
    name="Company Okta",
    type="okta",
    config={
        "domain": "company.okta.com",
        "api_token": "...",
    },
)

# Sync principals from the provider
client.identity_providers.sync(idp.id)`,
      },
    ],
  },
];

type SectionData = (typeof sections)[number];

function CodeBlock({ code, className = '' }: { code: string; className?: string }) {
  return (
    <pre className={`overflow-x-auto rounded-md bg-foreground/5 p-4 text-sm leading-6 ${className}`}>
      <code>{code}</code>
    </pre>
  );
}

function DataTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border">
            {headers.map((h) => (
              <th key={h} className="py-2 pr-4 text-left font-medium text-foreground">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-border">
              {row.map((cell, j) => (
                <td key={j} className="py-2 pr-4 text-muted-foreground font-mono text-xs">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SectionCard({ section }: { section: SectionData }) {
  return (
    <div id={section.id} className="scroll-mt-24 rounded-lg border border-border bg-card p-8">
      <h2 className="text-2xl font-semibold text-foreground">{section.title}</h2>
      <p className="mt-3 leading-7 text-muted-foreground">{section.description}</p>

      {/* Concepts list */}
      {'concepts' in section && section.concepts && (
        <div className="mt-6 space-y-4">
          {section.concepts.map((c) => (
            <div key={c.name} className="rounded-md border border-border p-4">
              <h3 className="font-semibold text-foreground">{c.name}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{c.detail}</p>
            </div>
          ))}
        </div>
      )}

      {/* Subsections */}
      {'subsections' in section && section.subsections && (
        <div className="mt-6 space-y-6">
          {section.subsections.map((sub) => (
            <div key={sub.title}>
              <h3 className="text-lg font-medium text-foreground">{sub.title}</h3>
              {'detail' in sub && sub.detail && (
                <p className="mt-2 text-sm text-muted-foreground">{sub.detail}</p>
              )}
              {'list' in sub && sub.list && (
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {sub.list.map((item, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-primary-600 mt-0.5">&#8226;</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              )}
              {'code' in sub && sub.code && <CodeBlock code={sub.code} className="mt-3" />}
              {'example' in sub && sub.example && <CodeBlock code={sub.example} className="mt-3" />}
              {'table' in sub && sub.table && (
                <div className="mt-3">
                  <DataTable headers={sub.table.headers} rows={sub.table.rows} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocsPage() {
  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Documentation
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Everything you need to integrate permission-aware retrieval into your AI systems.
            </p>
          </div>

          {/* Table of Contents */}
          <nav className="mx-auto mt-10 max-w-3xl rounded-lg border border-border bg-card p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              On this page
            </h2>
            <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
              {sections.map((s) => (
                <li key={s.id}>
                  <Link
                    href={`#${s.id}`}
                    className="text-sm text-primary-600 hover:text-primary-500 hover:underline"
                  >
                    {s.title}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Sections */}
          <div className="mx-auto mt-10 max-w-3xl space-y-10">
            {sections.map((section) => (
              <SectionCard key={section.id} section={section} />
            ))}
          </div>

          {/* Footer CTA */}
          <div className="mx-auto mt-16 max-w-3xl rounded-lg bg-muted/50 p-8 text-center">
            <h2 className="text-xl font-semibold text-foreground">Need help?</h2>
            <p className="mt-2 text-muted-foreground">
              Check out the{' '}
              <Link href="https://github.com/fortisil/gateco" className="text-primary-600 hover:underline">
                GitHub repository
              </Link>{' '}
              for source code and examples, or{' '}
              <Link href="/contact" className="text-primary-600 hover:underline">
                contact us
              </Link>{' '}
              for support.
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Building with an AI coding assistant?{' '}
              <Link href="/llms-full.txt" className="text-primary-600 hover:underline">
                llms-full.txt
              </Link>{' '}
              provides LLM-friendly context for integration.
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
