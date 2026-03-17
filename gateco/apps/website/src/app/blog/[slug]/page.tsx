import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

interface BlogPost {
  slug: string;
  title: string;
  date: string;
  author: string;
  readTime: string;
  tags: string[];
  excerpt: string;
  content: string[];
}

const posts: BlogPost[] = [
  {
    slug: 'the-rag-security-gap',
    title: 'The RAG Security Gap: Why Semantic Similarity Is Not Authorization',
    date: 'March 10, 2025',
    author: 'Gateco Team',
    readTime: '6 min read',
    tags: ['Security', 'RAG', 'Architecture'],
    excerpt:
      'Vector databases retrieve based on embedding similarity. They don\'t know who\'s asking. They don\'t check permissions. They just return the closest matches.',
    content: [
      'Your organization invested in SSO for identity, IAM for cloud resources, ACLs for file systems, and RBAC for applications. But when you deployed RAG, you created a new access surface that bypasses all of it.',
      'Here\'s the core problem: when a manager asks your AI copilot about compensation data, the vector database returns the most semantically relevant chunks — not the most appropriately authorized chunks. Semantic similarity does not equal permission to access.',
      'Traditional approaches like metadata filters in vector queries are a partial solution at best. They push authorization logic into application code, can\'t enforce deny-by-default, and leave no audit trail. What\'s needed is a dedicated permission-aware retrieval layer.',
      'Gateco sits between your AI agents and vector databases, enforcing RBAC and ABAC policies at retrieval time. Every query is checked against active policies before results are returned. No policy match means no data. Every decision is logged with full context — who requested it, what was allowed or denied, and which policy made the decision.',
      'The result is a retrieval pipeline where your AI agents only see what they\'re authorized to see, with a complete audit trail for compliance.',
    ],
  },
  {
    slug: 'introducing-gateco',
    title: 'Introducing Gateco: Permission-Aware Retrieval for AI Systems',
    date: 'February 24, 2025',
    author: 'Gateco Team',
    readTime: '5 min read',
    tags: ['Product', 'Launch'],
    excerpt:
      'Today we\'re launching Gateco — the security middleware between AI agents and organizational knowledge.',
    content: [
      'AI agents are increasingly accessing organizational knowledge through vector databases. But vector databases have no concept of authorization — they retrieve by semantic similarity alone. This gap puts sensitive data at risk.',
      'Gateco is a permission-aware retrieval layer that enforces access policies at retrieval time. It connects to 9 vector databases (pgvector, Pinecone, Qdrant, Weaviate, Milvus, Chroma, OpenSearch, Supabase, and Neon) and provides deny-by-default retrieval enforcement.',
      'The core workflow is straightforward: connect your vector database, define policies (RBAC or ABAC), and every retrieval is automatically checked. Outcomes are classified as Allowed, Partial (some results filtered), or Denied. Every decision is recorded in an immutable audit log with 25 event types.',
      'We designed Gateco around three principles. First, it\'s not a vector database or a RAG framework — it\'s the security layer that sits between your existing components. Second, deny-by-default means no data is returned without an explicit policy match. Third, auditability is built in from the start, not bolted on.',
      'Gateco is available today with a free tier (100 retrievals/month, 1 connector) and Pro ($49/month) and Enterprise ($199/month) plans for teams that need ABAC policies, Policy Studio, Access Simulator, SIEM integration, and more.',
    ],
  },
  {
    slug: 'semantic-readiness-levels',
    title: 'Understanding Semantic Readiness: L0 Through L4 Explained',
    date: 'February 10, 2025',
    author: 'Gateco Team',
    readTime: '7 min read',
    tags: ['Technical', 'Architecture'],
    excerpt:
      'Gateco assigns each connector a readiness level from L0 to L4 based on its security capability.',
    content: [
      'When you connect a vector database to Gateco, it starts at L0 (Not Ready). Your goal is to progressively move up through the readiness levels as you configure policies and metadata. Each level represents a real capability milestone, not a score.',
      'L0 (Not Ready) means the connector is created but not reachable — credentials may be invalid or the database is down. L1 (Connection Ready) means Gateco can authenticate and reach your vector database. This is confirmed when the test connection endpoint returns a successful health check with latency.',
      'L2 (Search Ready) means search and retrieval operations are functional. Your search configuration is set (dimensions, metric, index), and Gateco can execute queries against your vector database. At this level, coarse connector-level controls are possible.',
      'L3 (Resource Policy) is where real security begins. This requires active policies AND resource-level metadata resolution — meaning Gateco can determine the classification, sensitivity, and ownership of individual resources and enforce policies against them. You reach L3 by binding metadata to your resources (via sidecar registry, inline payload, or SQL view) and activating at least one policy.',
      'L4 (Chunk Policy) is the highest granularity. It requires chunk-level policy metadata — each individual vector has its own classification and sensitivity metadata that flows through policy evaluation. This is achievable with inline metadata mode (where each vector payload contains its own metadata) or SQL view mode (when the view returns per-vector-id metadata). Sidecar mode alone cannot reach L4 in the current architecture because sidecar metadata lives on GatedResource records, not individual chunks.',
      'Readiness is separate from coverage. Coverage is an operational metric (e.g., "85% of resources have metadata bound"). Readiness is a capability metric (e.g., "this connector CAN enforce chunk-level policies"). You can have L4 readiness with 10% coverage — the capability exists, you just haven\'t classified all your data yet.',
    ],
  },
  {
    slug: 'metadata-resolution-modes',
    title: 'Three Ways to Resolve Metadata: Sidecar, Inline, and SQL Views',
    date: 'January 28, 2025',
    author: 'Gateco Team',
    readTime: '8 min read',
    tags: ['Technical', 'Integration'],
    excerpt:
      'Gateco resolves policy-relevant metadata through a configurable 3-step hierarchy.',
    content: [
      'When Gateco evaluates a retrieval, it needs to know the classification, sensitivity, domain, and ownership of each result. This metadata determines which policies apply and whether the requesting principal is authorized. The question is: where does this metadata come from?',
      'Sidecar mode (the default) stores metadata in Gateco\'s own registry. You bind metadata to resources via the API, CLI, or classification suggestion workflow. This is the simplest approach — no changes to your vector database, full control over the metadata. The tradeoff is that metadata lives at the resource level, not per-chunk, so you can reach L3 but not L4 readiness.',
      'Inline mode extracts metadata directly from vector payloads. If your Pinecone vectors already have a "department" or "classification" field in their metadata, Gateco can use it. You configure a metadata_field_mapping that maps your payload keys to Gateco\'s schema (classification, sensitivity, domain, labels, owner_principal). Since each vector has its own metadata, inline mode can reach L4 readiness.',
      'SQL view mode queries a Postgres view for metadata. This is available for Postgres-family connectors only (pgvector, Supabase, Neon). You create a view in your database that joins vector IDs to their classification metadata, then point Gateco at it. All identifiers are validated against a strict regex — no raw SQL is ever passed through configuration. SQL view mode can reach L4 if the view returns per-vector-id rows.',
      'Auto mode tries all three in order: inline first (checking payload), then SQL view (if configured), then sidecar (always available). This is useful during migration — start with sidecar for quick setup, then gradually move to inline as you add metadata to your vector payloads.',
      'The resolution mode is configured per connector, so you can use different strategies for different databases. All resolved metadata is normalized into a unified ResolvedPolicySubject model before policy evaluation, regardless of which resolution mode produced it.',
    ],
  },
  {
    slug: 'getting-started-5-minutes',
    title: 'From Zero to Secured Retrieval in 5 Minutes',
    date: 'January 15, 2025',
    author: 'Gateco Team',
    readTime: '4 min read',
    tags: ['Tutorial', 'Getting Started'],
    excerpt:
      'Install the SDK, connect a vector database, create a policy, and execute your first secured retrieval.',
    content: [
      'Step 1: Install the SDK. Run pip install gateco-sdk, then authenticate: gateco login --email you@company.com --password secret. This stores credentials locally and you\'re ready to go.',
      'Step 2: Connect your vector database. Use the SDK or CLI to create a connector — Gateco supports pgvector, Pinecone, Qdrant, Weaviate, Milvus, Chroma, OpenSearch, Supabase, and Neon. For example: client.connectors.create(name="My Pinecone", type="pinecone", config={"api_key": "pk-...", "index_name": "knowledge"}). Then test it: client.connectors.test(connector.id) to verify connectivity.',
      'Step 3: Define a policy. Create an RBAC policy that allows specific roles to access specific data classifications. For example, allow the "engineering" role to access "internal" classified documents. Activate the policy to start enforcement.',
      'Step 4: Bind metadata to your resources. Use the classification suggestion engine (client.connectors.suggest_classifications) to scan your resources and get automatic suggestions, or bind metadata manually via the API. This tells Gateco what classification and sensitivity level each resource has.',
      'Step 5: Execute a secured retrieval. Call client.retrievals.execute(connector_id=..., principal_id=..., query_vector=..., top_k=10). Gateco evaluates all active policies, filters results to only what the principal is authorized to see, and returns the results. The audit log records the full decision trace.',
      'That\'s it. Your AI agent now only sees what it\'s supposed to see, with every retrieval logged for compliance.',
    ],
  },
  {
    slug: 'access-simulator-testing-policies',
    title: 'Test Before You Enforce: Using the Access Simulator',
    date: 'January 5, 2025',
    author: 'Gateco Team',
    readTime: '5 min read',
    tags: ['Tutorial', 'Pro Feature'],
    excerpt:
      'Dry-run policy evaluation to see exactly what a principal would be allowed or denied.',
    content: [
      'Deploying access policies to production is high-stakes. An overly restrictive policy could block legitimate AI use cases. An overly permissive one defeats the purpose. The Access Simulator (available on Pro and Enterprise plans) lets you test policies without affecting real retrievals.',
      'The simulator takes a principal ID and optionally a connector ID, then evaluates all active policies to show what the principal can and cannot access. The response includes matched resource count, allowed count, denied count, and a full trace of policy decisions with reasons.',
      'For example: result = client.simulator.run(principal_id="user_123", connector_id="conn_abc"). The traces show each resource, the decision (allowed/denied), and which policy rule matched or why access was denied. This lets you iterate on policies in a safe environment.',
      'A common workflow is: create policies in Draft state, run the simulator to verify behavior, adjust rules based on the traces, then activate. This is especially important for ABAC policies with complex attribute conditions — the simulator shows you exactly which conditions matched or failed.',
      'The simulator is also valuable for onboarding new team members or auditing existing access. Run a simulation for a new hire\'s principal ID to verify they have appropriate access from day one, or periodically simulate access for service accounts to catch permission drift.',
    ],
  },
  {
    slug: 'compliance-audit-trail',
    title: 'Building a Compliance-Ready AI System with Audit Trails',
    date: 'December 18, 2024',
    author: 'Gateco Team',
    readTime: '6 min read',
    tags: ['Compliance', 'Enterprise'],
    excerpt:
      'When auditors ask "who accessed what data through your AI system?", you need an answer.',
    content: [
      'As organizations deploy AI agents that access internal knowledge, regulators are asking pointed questions: Can you show who accessed what data? Can you prove your AI respects existing access controls? Can you produce an audit trail for a specific time period?',
      'Gateco logs every operation as an audit event with full context. Retrieval events record the requesting principal, connector, policy decision (allowed/denied), which policies matched, metadata resolution source, and timestamp. Policy lifecycle events track who created, modified, activated, or archived each policy.',
      'There are 25 event types grouped into categories: User events (login, logout, settings changes), Connector events (added, updated, tested, removed, sync), Policy events (created, updated, activated, archived, deleted), Retrieval events (allowed, denied with full trace), Data events (metadata bound, documents ingested), Identity Provider events (added, synced), and Pipeline events.',
      'On the Pro plan, you can export audit logs as CSV or JSON with date range and event type filtering. On Enterprise, you can stream audit events to your SIEM platform in real-time for integration with your existing security monitoring.',
      'The key principle is that audit data exists from day one — you don\'t need to configure logging or enable a feature. Every operation that flows through Gateco is automatically recorded. When an auditor asks "show me all retrieval events for this user in Q1", it\'s a single API call: client.audit.list(actor="user_123", event_types="retrieval_allowed,retrieval_denied", date_from="2025-01-01", date_to="2025-03-31").',
    ],
  },
];

export async function generateStaticParams() {
  return posts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const post = posts.find((p) => p.slug === params.slug);
  if (!post) return { title: 'Post Not Found' };
  return {
    title: post.title,
    description: post.excerpt,
  };
}

export default function BlogPostPage({
  params,
}: {
  params: { slug: string };
}) {
  const post = posts.find((p) => p.slug === params.slug);
  if (!post) notFound();

  // Find adjacent posts for navigation
  const idx = posts.indexOf(post);
  const prevPost = idx < posts.length - 1 ? posts[idx + 1] : null;
  const nextPost = idx > 0 ? posts[idx - 1] : null;

  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <article className="mx-auto max-w-3xl">
            {/* Back link */}
            <Link
              href="/blog"
              className="group mb-8 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
              Back to blog
            </Link>

            {/* Header */}
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <time>{post.date}</time>
              <span aria-hidden="true">&middot;</span>
              <span>{post.readTime}</span>
              <span aria-hidden="true">&middot;</span>
              <span>{post.author}</span>
            </div>
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              {post.title}
            </h1>
            <div className="mt-4 flex flex-wrap gap-2">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>

            {/* Content */}
            <div className="mt-10 space-y-6">
              {post.content.map((paragraph, i) => (
                <p
                  key={i}
                  className="text-base leading-8 text-muted-foreground"
                >
                  {paragraph}
                </p>
              ))}
            </div>

            {/* Divider */}
            <hr className="my-12 border-border" />

            {/* Post navigation */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {prevPost && (
                <Link
                  href={`/blog/${prevPost.slug}`}
                  className="rounded-lg border border-border p-4 hover:bg-muted/50 transition-colors"
                >
                  <p className="text-xs text-muted-foreground">&larr; Previous</p>
                  <p className="mt-1 text-sm font-medium text-foreground">
                    {prevPost.title}
                  </p>
                </Link>
              )}
              {nextPost && (
                <Link
                  href={`/blog/${nextPost.slug}`}
                  className="rounded-lg border border-border p-4 hover:bg-muted/50 transition-colors sm:text-right"
                >
                  <p className="text-xs text-muted-foreground">Next &rarr;</p>
                  <p className="mt-1 text-sm font-medium text-foreground">
                    {nextPost.title}
                  </p>
                </Link>
              )}
            </div>

            {/* CTA */}
            <div className="mt-12 rounded-lg bg-muted/50 p-8 text-center">
              <h2 className="text-xl font-semibold text-foreground">
                Ready to secure your AI retrieval?
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Start with the free tier — 100 retrievals/month, no credit card required.
              </p>
              <div className="mt-4 flex justify-center gap-3">
                <a
                  href={`${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:5173'}/login`}
                  className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-500 transition-colors"
                >
                  Get started
                </a>
                <Link
                  href="/docs"
                  className="rounded-lg border border-border px-5 py-2.5 text-sm font-semibold text-foreground hover:bg-muted transition-colors"
                >
                  Read the docs
                </Link>
              </div>
            </div>
          </article>
        </div>
      </main>
      <Footer />
    </>
  );
}
