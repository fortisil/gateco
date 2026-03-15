'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import FaqSection from '@/components/FaqSection';

const tiers = [
  {
    name: 'Free',
    price: '$0',
    period: 'per month',
    description: 'Essential AI security for small teams and evaluation.',
    features: [
      'Basic policy enforcement',
      'Limited audit log retention',
      'Community support'
    ],
    cta: 'Start Free',
    featured: false,
  },
  {
    name: 'Pro',
    price: '$49',
    period: 'per month',
    description: 'Advanced controls and extended auditability for growing teams.',
    features: [
      'All Free features',
      'Extended audit log retention',
      'Priority support',
      'Custom integrations'
    ],
    cta: 'Upgrade to Pro',
    featured: true,
  },
  {
    name: 'Enterprise',
    price: 'Contact Us',
    period: '/month',
    description: 'Custom security, compliance, and support for enterprise environments.',
    features: [
      'All Pro features',
      'Unlimited audit logs',
      'Dedicated account manager',
      'Custom SLAs',
      'Enterprise SSO & compliance'
    ],
    cta: 'Request Demo',
    featured: false,
  }
];

const pricingFaq = [
  { question: 'Can I switch plans later?', answer: 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect on your next billing cycle.' },
  { question: 'Is there a free trial?', answer: 'Yes, all paid plans come with a 14-day free trial. No credit card required.' },
  { question: 'What payment methods do you accept?', answer: 'We accept all major credit cards, PayPal, and bank transfers for enterprise plans.' }
];

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
              Choose the plan that works best for you. All plans include a 14-day free trial.
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
                  Save 20%
                </span>
              </span>
            </div>
          </div>

          {/* Tier Cards */}
          <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-8 lg:max-w-5xl lg:grid-cols-3">
            {tiers.map((tier) => (
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
                    {tier.price === 'Custom' || tier.price === 'Free'
                      ? tier.price
                      : annual
                        ? `$${Math.round(parseFloat(tier.price.replace('$', '')) * 0.8)}`
                        : tier.price}
                  </span>
                  {tier.period && tier.price !== 'Custom' && tier.price !== 'Free' && (
                    <span className="text-sm text-muted-foreground">
                      {annual ? '/month, billed annually' : tier.period}
                    </span>
                  )}
                </p>
                <ul className="mt-8 space-y-4">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex text-sm text-muted-foreground">
                      <Check className="h-5 w-5 flex-shrink-0 text-primary-600" />
                      <span className="ml-3">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`mt-8 w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors ${
                    tier.featured
                      ? 'bg-primary-600 text-white hover:bg-primary-500 shadow-lg shadow-primary-600/25'
                      : 'bg-card text-foreground border border-border hover:bg-muted'
                  }`}
                >
                  {tier.cta}
                </button>
              </div>
            ))}
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
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Basic policy enforcement</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Limited audit log retention</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Community support</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">All Free features</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Extended audit log retention</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Priority support</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Custom integrations</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">All Pro features</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Unlimited audit logs</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                  </tr>
                  <tr className="border-b border-border">
                    <td className="py-3 pr-4 font-medium text-foreground">Dedicated account manager</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center text-muted-foreground">&mdash;</td>
                    <td className="px-4 py-3 text-center"><Check className="mx-auto h-5 w-5 text-primary-600" /></td>
                  </tr>
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
              Contact our sales team for enterprise pricing, custom contracts, and dedicated support.
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
