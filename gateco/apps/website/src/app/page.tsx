import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, Database, Shield, Star } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import JsonLd from '@/components/JsonLd';


export const metadata: Metadata = {
  title: 'Welcome',
  description: 'Welcome to Gateco',
};

const ORG_SCHEMA = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'Gateco',
  url: process.env.NEXT_PUBLIC_SITE_URL || 'https://gateco.com',
};

const PRODUCT_SCHEMA = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Gateco',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
};


const ICON_MAP: Record<string, React.ElementType> = {
  Database,
  Star,
  Shield,
};

const features = [
                {
                  title: 'Vector DB agnostic',
                  description: 'Vector DB agnostic',
                  icon: 'Database',
                },
                {
                  title: 'Embedding & chunking agnostic',
                  description: 'Embedding & chunking agnostic',
                  icon: 'Star',
                },
                {
                  title: 'Identity-driven, not prompt-driven',
                  description: 'Identity-driven, not prompt-driven',
                  icon: 'Star',
                },
                {
                  title: 'Late-binding authorization',
                  description: 'Late-binding authorization',
                  icon: 'Shield',
                },
                {
                  title: 'Retroactive permission changes',
                  description: 'Retroactive permission changes',
                  icon: 'Shield',
                },
                {
                  title: 'Bypass yields no meaning',
                  description: 'Bypass yields no meaning',
                  icon: 'Star',
                }
];

export default function HomePage() {
  return (
    <>
      <Header />
      <JsonLd schema={ORG_SCHEMA} />
      <JsonLd schema={PRODUCT_SCHEMA} />
      <main className="flex min-h-screen flex-col">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-primary-50/30 py-24 sm:py-36">
          <div className="container">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
                Gateco
              </h1>

              <p className="mt-6 text-lg leading-8 text-muted-foreground">
                Gateco is a permission-aware retrieval layer that sits between AI agents and vector databases.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-4">
                <Link
                  href="/pricing"
                  className="rounded-lg bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 hover:bg-primary-500 transition-all hover:shadow-primary-600/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  Get started
                </Link>
                <Link
                  href="/docs"
                  className="group flex items-center gap-1 text-sm font-semibold text-foreground hover:text-primary-600 transition-colors"
                >
                  Learn more
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </div>

            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 sm:py-28">
          <div className="container">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Everything you need
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Gateco is a permission-aware retrieval layer that sits between AI agents and vector databases.
              </p>
            </div>
            <div className="mx-auto mt-16 max-w-5xl">
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
                {features.map((feature) => {
                  const Icon = ICON_MAP[feature.icon] || Star;
                  return (
                    <div
                      key={feature.title}
                      className="group rounded-2xl border border-border bg-card p-8 transition-all hover:shadow-lg hover:-translate-y-1"
                    >
                      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100">
                        <Icon className="h-5 w-5 text-primary-600" />
                      </div>
                      <h3 className="text-lg font-semibold text-foreground">
                        {feature.title}
                      </h3>
                      <p className="mt-2 text-muted-foreground">{feature.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

      {/* How It Works */}
      <section className="bg-muted/50 py-20 sm:py-28">
        <div className="container">
          <h2 className="text-center text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            How it works
          </h2>
          <div className="mx-auto mt-16 grid max-w-4xl grid-cols-1 gap-12 md:grid-cols-3">
              <div className="relative text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-600 text-lg font-bold text-white">
                  1
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">Sign Up</h3>
                <p className="mt-2 text-muted-foreground">Create your account in seconds</p>
              </div>
              <div className="relative text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-600 text-lg font-bold text-white">
                  2
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">Configure</h3>
                <p className="mt-2 text-muted-foreground">Set up your workspace to match your needs</p>
              </div>
              <div className="relative text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-600 text-lg font-bold text-white">
                  3
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">Deploy</h3>
                <p className="mt-2 text-muted-foreground">Go live and start seeing results</p>
              </div>
          </div>
        </div>
      </section>

      {/* Pricing Teaser */}
      <section className="bg-muted/50 py-20 sm:py-28">
        <div className="container">
          <h2 className="text-center text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Simple, transparent pricing
          </h2>
          <div className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-3">
              <div className="rounded-2xl border border-border bg-card p-6 text-center">
                <h3 className="text-lg font-semibold text-foreground">Free</h3>
                <p className="mt-2 text-3xl font-bold text-foreground">$0</p>
                <p className="text-sm text-muted-foreground">per month</p>
                <p className="mt-2 text-sm text-muted-foreground">Essential AI security for small teams and evaluation.</p>
              </div>
              <div className="rounded-2xl border border-primary-600 ring-2 ring-primary-600 bg-card p-6 text-center">
                <h3 className="text-lg font-semibold text-foreground">Pro</h3>
                <p className="mt-2 text-3xl font-bold text-foreground">$49</p>
                <p className="text-sm text-muted-foreground">per month</p>
                <p className="mt-2 text-sm text-muted-foreground">Advanced controls and extended auditability for growing teams.</p>
              </div>
              <div className="rounded-2xl border border-border bg-card p-6 text-center">
                <h3 className="text-lg font-semibold text-foreground">Enterprise</h3>
                <p className="mt-2 text-3xl font-bold text-foreground">Contact Us</p>
                
                <p className="mt-2 text-sm text-muted-foreground">Custom security, compliance, and support for enterprise environments.</p>
              </div>
          </div>
          <div className="mt-8 text-center">
            <Link
              href="/pricing"
              className="text-sm font-semibold text-primary-600 hover:text-primary-500"
            >
              View full pricing <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        </div>
      </section>

        {/* Final CTA Section */}
        <section className="bg-gradient-to-br from-primary-600 to-primary-700 py-20 sm:py-28">
          <div className="container text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to get started?
            </h2>
            <p className="mt-4 text-lg text-primary-100">
              Start building today.
            </p>
            <div className="mt-8 flex items-center justify-center gap-x-4">
              <Link
                href="/pricing"
                className="rounded-lg bg-white px-6 py-3 text-sm font-semibold text-primary-600 shadow-lg hover:bg-primary-50 transition-colors"
              >
                Get started
              </Link>
              <Link
                href="/docs"
                className="rounded-lg border border-primary-300 px-6 py-3 text-sm font-semibold text-white hover:bg-primary-500 transition-colors"
              >
                Learn more
              </Link>
            </div>

          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
