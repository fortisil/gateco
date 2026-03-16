"use client";

import Link from "next/link";
import {
  ArrowRight,
  Shield,
  Database,
  Layers,
  Search,
  FileCheck,
  Terminal,
} from "lucide-react";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { TestimonialsSection } from "@/components/ui/testimonials-section";
import HeroSection from "@/components/ui/hero-section";
import DisplayCards from "@/components/ui/display-cards";

const features = [
  {
    icon: Shield,
    title: "Deny-by-Default Retrieval",
    description:
      "Every query is checked against RBAC and ABAC policies before results are returned. No policy match means no data — your AI can't access what it shouldn't.",
  },
  {
    icon: Database,
    title: "9 Vector DB Connectors",
    description:
      "Works with pgvector, Pinecone, Qdrant, Weaviate, Milvus, Chroma, OpenSearch, Supabase, and Neon. Tier 1 connectors support full ingestion workflows.",
  },
  {
    icon: Layers,
    title: "Semantic Readiness (L0-L4)",
    description:
      "Five progressive levels from connection validation through chunk-level policy enforcement. Know exactly where your security posture stands.",
  },
  {
    icon: Search,
    title: "Classification Suggestions",
    description:
      "Scan your resources and get rule-based classification suggestions for sensitivity and domain. Review, approve, and apply — data labeling made practical.",
  },
  {
    icon: FileCheck,
    title: "Full Audit Trail",
    description:
      "25 event types covering every retrieval, policy change, and connector operation. Export as CSV/JSON or stream to your SIEM.",
  },
  {
    icon: Terminal,
    title: "SDK + CLI",
    description:
      "Python and TypeScript SDKs for programmatic access. gateco CLI for quick operations. Access Simulator for dry-run policy testing.",
  },
];

const howItWorksCards = [
  {
    icon: <Database className="size-4 text-primary-300" />,
    title: "Connect",
    description: "Point Gateco at your vector DB",
    date: "Step 1",
    iconClassName: "text-primary-500",
    titleClassName: "text-primary-500",
    className:
      "[grid-area:stack] hover:-translate-y-10 before:absolute before:w-[100%] before:outline-1 before:rounded-xl before:outline-border before:h-[100%] before:content-[''] before:bg-blend-overlay before:bg-background/50 grayscale-[100%] hover:before:opacity-0 before:transition-opacity before:duration-700 hover:grayscale-0 before:left-0 before:top-0",
  },
  {
    icon: <Shield className="size-4 text-primary-300" />,
    title: "Define Policies",
    description: "Set who can access what data",
    date: "Step 2",
    iconClassName: "text-primary-500",
    titleClassName: "text-primary-500",
    className:
      "[grid-area:stack] translate-x-16 translate-y-10 hover:-translate-y-1 before:absolute before:w-[100%] before:outline-1 before:rounded-xl before:outline-border before:h-[100%] before:content-[''] before:bg-blend-overlay before:bg-background/50 grayscale-[100%] hover:before:opacity-0 before:transition-opacity before:duration-700 hover:grayscale-0 before:left-0 before:top-0",
  },
  {
    icon: <Search className="size-4 text-primary-300" />,
    title: "Secure Retrieval",
    description: "Every query is permission-checked",
    date: "Step 3",
    iconClassName: "text-primary-500",
    titleClassName: "text-primary-500",
    className:
      "[grid-area:stack] translate-x-32 translate-y-20 hover:translate-y-10",
  },
];

const testimonials = [
  {
    author: {
      name: "Alex Rivera",
      handle: "CTO, DataForge AI",
      avatar:
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
    },
    text: "Gateco solved our biggest compliance concern overnight. We went from 'hope nobody asks about AI data access' to having a full audit trail in under a week.",
  },
  {
    author: {
      name: "Sarah Kim",
      handle: "Head of Engineering, NovaBridge",
      avatar:
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
    },
    text: "The deny-by-default approach was exactly what we needed. Our AI agents now only see what they're supposed to — no more worrying about data leakage in RAG.",
  },
  {
    author: {
      name: "Marcus Chen",
      handle: "VP of Security, Cloudshift",
      avatar:
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face",
    },
    text: "Plugging Gateco into our existing Pinecone setup took 20 minutes. The readiness levels give us a clear path to full chunk-level enforcement.",
  },
  {
    author: {
      name: "Elena Rodriguez",
      handle: "Lead Developer, Synthwave Labs",
      avatar:
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
    },
    text: "The Python SDK is a pleasure to use. Five lines of code and our retrieval pipeline is permission-aware. Classification suggestions saved us weeks of manual labeling.",
  },
  {
    author: {
      name: "James Okonkwo",
      handle: "Security Architect, TrustLayer",
      avatar:
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
    },
    text: "We evaluated three solutions for AI access governance. Gateco was the only one that didn't try to replace our vector DB — it just adds the security layer we needed.",
  },
];

export default function HomeContent() {
  return (
    <>
      {/* Hero Section */}
      <HeroSection
        kicker="Permission-aware retrieval for AI"
        title={
          <>
            Gate your AI&apos;s
            <br />
            <span className="text-primary-600">access to knowledge</span>
          </>
        }
        subtitle="The security middleware between AI agents and your organizational data. Policy enforcement, identity-based access control, and full auditability for every retrieval."
        primaryCta={{ label: "Start for free", href: "/pricing" }}
        secondaryCta={{ label: "Read the docs", href: "/docs" }}
      />

      {/* Features Section */}
      <section id="features" className="py-20 sm:py-28">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Security that works with your stack
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Gateco sits between your AI agents and vector databases — enforcing
              policies at retrieval time without changing your existing
              architecture.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-6xl">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className="group relative rounded-2xl border border-border bg-card p-8 transition-all hover:shadow-lg"
                  >
                    <GlowingEffect
                      spread={40}
                      glow
                      disabled={false}
                      proximity={64}
                      inactiveZone={0.01}
                      borderWidth={2}
                    />
                    <div className="relative z-10">
                      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                        <Icon className="h-5 w-5 text-primary-600" />
                      </div>
                      <h3 className="text-lg font-semibold text-foreground">
                        {feature.title}
                      </h3>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-muted/30 py-20 sm:py-28">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Three steps to secure retrieval
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              No infrastructure changes required. Connect, configure, and
              enforce — your AI agents keep working, now with permission
              boundaries.
            </p>
          </div>
          <div className="mx-auto mt-16 flex items-center justify-center">
            <div className="w-full max-w-3xl">
              <DisplayCards cards={howItWorksCards} />
            </div>
          </div>
        </div>
      </section>

      {/* SDK Code Preview */}
      <section className="py-20 sm:py-28">
        <div className="container">
          <div className="mx-auto max-w-4xl">
            <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
              <div>
                <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  Integrate in minutes
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Python and TypeScript SDKs make permission-aware retrieval a
                  one-liner. The CLI handles everything else.
                </p>
                <div className="mt-6 flex gap-3">
                  <Link
                    href="/docs"
                    className="rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-500 transition-colors"
                  >
                    View SDK docs
                  </Link>
                  <Link
                    href="https://github.com/fortisil/gateco"
                    className="group flex items-center gap-1 rounded-lg border border-border px-5 py-2.5 text-sm font-semibold text-foreground hover:bg-muted transition-colors"
                  >
                    GitHub
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </Link>
                </div>
              </div>
              <div className="overflow-hidden rounded-xl border border-border bg-[#1e1e2e] p-6 font-mono text-sm leading-relaxed">
                <div className="flex gap-2 pb-4">
                  <div className="h-3 w-3 rounded-full bg-red-500/60" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
                  <div className="h-3 w-3 rounded-full bg-green-500/60" />
                </div>
                <pre className="text-gray-300">
                  <code>{`from gateco import GatecoClient

client = GatecoClient(api_key="gk_...")

# Permission-aware retrieval
results = client.retrieve(
    connector_id="conn_abc",
    query_vector=embedding,
    identity="user@company.com",
    top_k=10,
)
# Only returns vectors the user
# is authorized to access`}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <TestimonialsSection
        title="Trusted by engineering teams"
        description="Teams building AI products use Gateco to ship with confidence — knowing their retrieval pipelines enforce the right access boundaries."
        testimonials={testimonials}
      />

      {/* Pricing Teaser */}
      <section className="py-20 sm:py-28">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Start free, scale as your AI retrieval needs grow.
            </p>
          </div>
          <div className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-3">
            <div className="rounded-2xl border border-border bg-card p-6 text-center">
              <h3 className="text-lg font-semibold text-foreground">Free</h3>
              <p className="mt-2 text-3xl font-bold text-foreground">$0</p>
              <p className="text-sm text-muted-foreground">per month</p>
              <ul className="mt-4 space-y-2 text-left text-sm text-muted-foreground">
                <li>1 connector</li>
                <li>100 retrievals/mo</li>
                <li>RBAC policies</li>
                <li>Community support</li>
              </ul>
            </div>
            <div className="rounded-2xl border-2 border-primary-600 bg-card p-6 text-center ring-1 ring-primary-600/20">
              <div className="mb-2 inline-block rounded-full bg-primary-100 px-3 py-0.5 text-xs font-semibold text-primary-700">
                Most popular
              </div>
              <h3 className="text-lg font-semibold text-foreground">Pro</h3>
              <p className="mt-2 text-3xl font-bold text-foreground">$49</p>
              <p className="text-sm text-muted-foreground">per month</p>
              <ul className="mt-4 space-y-2 text-left text-sm text-muted-foreground">
                <li>5 connectors</li>
                <li>10,000 retrievals/mo</li>
                <li>ABAC policies + Policy Studio</li>
                <li>Priority support</li>
              </ul>
            </div>
            <div className="rounded-2xl border border-border bg-card p-6 text-center">
              <h3 className="text-lg font-semibold text-foreground">
                Enterprise
              </h3>
              <p className="mt-2 text-3xl font-bold text-foreground">$199</p>
              <p className="text-sm text-muted-foreground">per month</p>
              <ul className="mt-4 space-y-2 text-left text-sm text-muted-foreground">
                <li>Unlimited everything</li>
                <li>SSO & SCIM</li>
                <li>SIEM integration</li>
                <li>Private Data Plane</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 text-center">
            <Link
              href="/pricing"
              className="text-sm font-semibold text-primary-600 hover:text-primary-500"
            >
              View full pricing details{" "}
              <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-700 py-20 sm:py-28">
        <div className="container text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Start securing your AI retrieval today
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            Free tier available. No credit card required. Connect your first
            vector DB in under 5 minutes.
          </p>
          <div className="mt-8 flex items-center justify-center gap-x-4">
            <Link
              href="/pricing"
              className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-primary-600 shadow-lg hover:bg-primary-50 transition-colors"
            >
              Start for free
            </Link>
            <Link
              href="/contact"
              className="rounded-lg border border-primary-300 px-6 py-3 text-sm font-semibold text-white hover:bg-primary-500 transition-colors"
            >
              Talk to sales
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
