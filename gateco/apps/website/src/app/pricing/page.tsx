'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check, X } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import FaqSection from '@/components/FaqSection';

const tiers = [
  {
    name: 'Free',
    monthlyPrice: 0,
    yearlyPrice: 0,
    description: 'Get started with basic AI retrieval security for individual projects.',
    limits: [
      '100 secured retrievals/mo',
      '1 connector',
      '1 identity provider',
      '3 policies',
      '1 team member',
    ],
    features: [
      'RBAC policies',
      'Basic audit log',
      'Community support',
    ],
    cta: 'Start Free',
    ctaHref: '/contact',
    featured: false,
  },
  {
    name: 'Pro',
    monthlyPrice: 49,
    yearlyPrice: 490,
    description: 'Advanced controls and extended auditability for growing teams.',
    limits: [
      '10,000 secured retrievals/mo',
      '5 connectors',
      '3 identity providers',
      'Unlimited policies',
      '10 team members',
      '$0.50/retrieval overage',
    ],
    features: [
      'Everything in Free',
      'ABAC policies',
      'Policy Studio',
      'Policy versioning',
      'Access Simulator',
      'Vendor IAM providers',
      'Advanced analytics',
      'Audit export',
      'Priority support',
    ],
    cta: 'Upgrade to Pro',
    ctaHref: '/contact',
    featured: true,
  },
  {
    name: 'Enterprise',
    monthlyPrice: 199,
    yearlyPrice: 1990,
    description: 'Full-featured security, compliance, and dedicated support for organizations.',
    limits: [
      'Unlimited secured retrievals',
      'Unlimited connectors',
      'Unlimited identity providers',
      'Unlimited policies',
      'Unlimited team members',
    ],
    features: [
      'Everything in Pro',
      'SIEM integration',
      'Content Reference Mode',
      'Custom KMS',
      'SSO & SCIM',
      'Private Data Plane',
      'Dedicated account manager',
      'Custom SLAs',
    ],
    cta: 'Contact Sales',
    ctaHref: '/contact',
    featured: false,
  },
];

const comparisonFeatures = [
  { name: 'Secured retrievals/mo', free: '100', pro: '10,000', enterprise: 'Unlimited' },
  { name: 'Connectors', free: '1', pro: '5', enterprise: 'Unlimited' },
  { name: 'Identity providers', free: '1', pro: '3', enterprise: 'Unlimited' },
  { name: 'Policies', free: '3', pro: 'Unlimited', enterprise: 'Unlimited' },
  { name: 'Team members', free: '1', pro: '10', enterprise: 'Unlimited' },
  { name: 'RBAC policies', free: true, pro: true, enterprise: true },
  { name: 'ABAC policies', free: false, pro: true, enterprise: true },
  { name: 'Policy Studio', free: false, pro: true, enterprise: true },
  { name: 'Policy versioning', free: false, pro: true, enterprise: true },
  { name: 'Access Simulator', free: false, pro: true, enterprise: true },
  { name: 'Vendor IAM providers', free: false, pro: true, enterprise: true },
  { name: 'Advanced analytics', free: false, pro: true, enterprise: true },
  { name: 'Audit export', free: false, pro: true, enterprise: true },
  { name: 'SIEM integration', free: false, pro: false, enterprise: true },
  { name: 'Content Reference Mode', free: false, pro: false, enterprise: true },
  { name: 'Custom KMS', free: false, pro: false, enterprise: true },
  { name: 'SSO & SCIM', free: false, pro: false, enterprise: true },
  { name: 'Private Data Plane', free: false, pro: false, enterprise: true },
];

const pricingFaq = [
  {
    question: 'Can I switch plans later?',
    answer: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect on your next billing cycle.',
  },
  {
    question: 'Is there a free trial?',
    answer: 'Yes, all paid plans come with a 14-day free trial. No credit card required.',
  },
  {
    question: 'What happens if I exceed my retrieval limit?',
    answer: 'On the Pro plan, additional retrievals are charged at $0.50 per retrieval. On the Free plan, retrievals are paused until the next billing cycle. Enterprise plans have no limits.',
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards, PayPal, and bank transfers for enterprise plans.',
  },
  {
    question: 'What connectors are supported?',
    answer: 'Gateco supports 9 vector databases: pgvector, Supabase, Neon, Pinecone, Qdrant, OpenSearch, Weaviate, Milvus, and Chroma. Tier 1 connectors (pgvector, Supabase, Neon, Pinecone, Qdrant) support full ingestion workflows.',
  },
];

function formatPrice(price: number) {
  return price === 0 ? '$0' : `$${price}`;
}

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);

  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          {/* Header */}
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Simple, transparent pricing
            </h1>
            <p className="mt-6 text-lg text-muted-foreground">
              Choose the plan that works best for you. All paid plans include a 14-day free trial.
            </p>

            {/* Monthly/Annual Toggle */}
            <div className="mt-8 flex items-center justify-center gap-3">
              <span className={`text-sm font-medium ${!annual ? 'text-foreground' : 'text-muted-foreground'}`}>
                Monthly
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={annual}
                onClick={() => setAnnual(!annual)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  annual ? 'bg-primary-600' : 'bg-muted'
                }`}
              >
                <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${
                  annual ? 'translate-x-5' : 'translate-x-0'
                }`} />
              </button>
              <span className={`text-sm font-medium ${annual ? 'text-foreground' : 'text-muted-foreground'}`}>
                Annual
                <span className="ml-1.5 inline-block rounded-full bg-primary-100 px-2 py-0.5 text-xs font-semibold text-primary-700">
                  Save ~17%
                </span>
              </span>
            </div>
          </div>

          {/* Tier Cards */}
          <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-8 lg:max-w-5xl lg:grid-cols-3">
            {tiers.map((tier) => {
              const displayPrice = annual
                ? Math.round(tier.yearlyPrice / 12)
                : tier.monthlyPrice;

              return (
                <div
                  key={tier.name}
                  className={`relative rounded-2xl p-8 transition-shadow hover:shadow-lg ${
                    tier.featured
                      ? 'border-2 border-primary-600 bg-card shadow-lg'
                      : 'border border-border bg-card'
                  }`}
                >
                  {tier.featured && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                      <span className="rounded-full bg-primary-600 px-4 py-1 text-sm font-semibold text-white">
                        Most Popular
                      </span>
                    </div>
                  )}
                  <h2 className="text-lg font-semibold text-foreground">
                    {tier.name}
                  </h2>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {tier.description}
                  </p>
                  <p className="mt-6">
                    <span className="text-4xl font-bold text-foreground">
                      {formatPrice(displayPrice)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {annual ? '/mo, billed annually' : '/month'}
                    </span>
                  </p>
                  {annual && tier.yearlyPrice > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatPrice(tier.yearlyPrice)}/year
                    </p>
                  )}

                  {/* Limits */}
                  <div className="mt-6 border-t border-border pt-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Limits
                    </p>
                    <ul className="mt-3 space-y-2">
                      {tier.limits.map((limit) => (
                        <li key={limit} className="flex text-sm text-muted-foreground">
                          <span className="mr-2 text-primary-600">&#8226;</span>
                          {limit}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Features */}
                  <ul className="mt-6 space-y-3 border-t border-border pt-4">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex text-sm text-muted-foreground">
                        <Check className="h-5 w-5 flex-shrink-0 text-primary-600" />
                        <span className="ml-3">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={tier.ctaHref}
                    className={`mt-8 block w-full rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition-colors ${
                      tier.featured
                        ? 'bg-primary-600 text-white hover:bg-primary-500 shadow-lg shadow-primary-600/25'
                        : 'bg-card text-foreground border border-border hover:bg-muted'
                    }`}
                  >
                    {tier.cta}
                  </Link>
                </div>
              );
            })}
          </div>

          {/* Feature Comparison */}
          <div className="mx-auto mt-20 max-w-5xl">
            <h2 className="text-2xl font-bold text-foreground text-center">
              Compare plans
            </h2>
            <div className="mt-8 overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-4 pr-4 text-left font-medium text-muted-foreground">Feature</th>
                    <th className="px-4 py-4 text-center font-medium text-foreground">Free</th>
                    <th className="px-4 py-4 text-center font-medium text-foreground">Pro</th>
                    <th className="px-4 py-4 text-center font-medium text-foreground">Enterprise</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonFeatures.map((feature) => (
                    <tr key={feature.name} className="border-b border-border">
                      <td className="py-3 pr-4 font-medium text-foreground">{feature.name}</td>
                      {(['free', 'pro', 'enterprise'] as const).map((tier) => {
                        const value = feature[tier];
                        return (
                          <td key={tier} className="px-4 py-3 text-center">
                            {typeof value === 'boolean' ? (
                              value ? (
                                <Check className="mx-auto h-5 w-5 text-primary-600" />
                              ) : (
                                <X className="mx-auto h-5 w-5 text-muted-foreground/40" />
                              )
                            ) : (
                              <span className="text-sm text-muted-foreground">{value}</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pricing FAQ */}
          <div className="mx-auto mt-20 max-w-3xl">
            <h2 className="text-2xl font-bold text-foreground text-center">
              Pricing FAQ
            </h2>
            <FaqSection items={pricingFaq} />
          </div>

          {/* Enterprise CTA */}
          <div className="mx-auto mt-20 max-w-2xl rounded-2xl bg-muted/50 p-8 text-center sm:p-12">
            <h2 className="text-2xl font-bold text-foreground">
              Need a custom plan?
            </h2>
            <p className="mt-4 text-muted-foreground">
              Contact our sales team for custom contracts, volume discounts, and dedicated support beyond our standard Enterprise plan.
            </p>
            <Link
              href="/contact"
              className="mt-6 inline-block rounded-lg border border-primary-600 px-6 py-3 text-sm font-semibold text-primary-600 hover:bg-primary-50 transition-colors"
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
