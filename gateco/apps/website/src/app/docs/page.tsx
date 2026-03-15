import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Documentation',
  description: 'Gateco documentation. Learn how to integrate identity-driven authorization into your AI systems.',
};

const sections = [
  {
    title: 'Quick Start',
    description:
      'Get Gateco running in your project in under five minutes. Install the SDK, configure your identity provider, and enforce your first policy.',
    code: `npm install @gateco/sdk

import { Gateco } from '@gateco/sdk';

const gateco = new Gateco({
  apiKey: process.env.GATECO_API_KEY,
});

// Check authorization before data access
const decision = await gateco.authorize({
  subject: user.id,
  action: 'read',
  resource: 'documents/confidential',
});

if (decision.allowed) {
  // Proceed with data retrieval
}`,
  },
  {
    title: 'Core Concepts',
    description:
      'Gateco is built around three primitives: Subjects (who is requesting access), Actions (what operation is being performed), and Resources (what data is being accessed). Policies define rules that map these primitives to allow or deny decisions. Every authorization decision is recorded in an immutable audit log, giving you full visibility into how your AI systems interact with sensitive data.',
  },
  {
    title: 'API Reference',
    description:
      'The Gateco REST API provides endpoints for authorization checks, policy management, audit log queries, and identity provider configuration. All endpoints require authentication via API key. Requests and responses use JSON. Rate limits are based on your subscription plan: Free tier allows 1,000 checks per minute, Pro allows 10,000, and Enterprise has configurable limits.',
  },
  {
    title: 'SDK Integration',
    description:
      'Official SDKs are available for Node.js, Python, and Go. Each SDK provides typed authorization checks, middleware for popular frameworks (Express, FastAPI, Gin), and helpers for RAG pipeline integration. The SDKs handle retries, connection pooling, and local policy caching for low-latency decisions.',
  },
  {
    title: 'Deployment Guide',
    description:
      'Gateco can be used as a managed cloud service or self-hosted in your infrastructure. The cloud service requires no setup beyond API key configuration. For self-hosted deployments, we provide Docker images and Helm charts. This guide covers both options, including high-availability configurations, database requirements, and network security recommendations.',
  },
];

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
              Everything you need to integrate Gateco into your AI systems.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-3xl space-y-10">
            {sections.map((section) => (
              <div
                key={section.title}
                className="rounded-lg border border-border bg-card p-8"
              >
                <h2 className="text-2xl font-semibold text-foreground">
                  {section.title}
                </h2>
                <p className="mt-3 text-muted-foreground leading-7">
                  {section.description}
                </p>
                {section.code && (
                  <pre className="mt-6 overflow-x-auto rounded-md bg-foreground/5 p-4 text-sm leading-6">
                    <code>{section.code}</code>
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
