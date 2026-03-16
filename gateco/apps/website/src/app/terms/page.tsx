import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'Gateco terms of service. Read the terms governing use of our AI authorization platform.',
};

export default function TermsPage() {
  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <div className="mx-auto max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Terms of Service
            </h1>
            <p className="mt-4 text-sm text-muted-foreground">
              Last updated: January 1, 2025
            </p>

            <div className="mt-12 space-y-10 text-muted-foreground leading-7">
              <section>
                <h2 className="text-xl font-semibold text-foreground">1. Acceptance of Terms</h2>
                <p className="mt-3">
                  By accessing or using the Gateco platform, you agree to be bound by these Terms of Service. If you are using Gateco on behalf of an organization, you represent that you have authority to bind that organization to these terms. If you do not agree, do not use the platform.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">2. Service Description</h2>
                <p className="mt-3">
                  Gateco provides an identity-driven authorization and data security platform for AI systems, including policy enforcement, audit logging, and access control management via APIs, SDKs, and a web dashboard. Service features and availability may vary by subscription plan.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">3. Accounts and Access</h2>
                <p className="mt-3">
                  You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account. You must provide accurate registration information and promptly update it if it changes. Notify us immediately of any unauthorized access at security@gateco.ai.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">4. Acceptable Use</h2>
                <p className="mt-3">
                  You agree not to use Gateco to violate any applicable law, infringe on intellectual property rights, transmit malicious code, attempt to gain unauthorized access to our systems, or interfere with the platform&apos;s operation. We reserve the right to suspend accounts that violate these terms.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">5. Intellectual Property</h2>
                <p className="mt-3">
                  Gateco and its licensors retain all rights to the platform, including software, documentation, and branding. Your subscription grants a limited, non-exclusive, non-transferable license to use the platform. You retain all rights to the data and configurations you create within Gateco.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">6. Limitation of Liability</h2>
                <p className="mt-3">
                  To the maximum extent permitted by law, Gateco shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the platform. Our total liability shall not exceed the fees paid by you in the twelve months preceding the claim.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">7. Termination</h2>
                <p className="mt-3">
                  Either party may terminate the agreement at any time. You may cancel your subscription through your account settings. We may suspend or terminate access for violation of these terms. Upon termination, you may export your data within 30 days, after which it will be deleted.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">8. Governing Law</h2>
                <p className="mt-3">
                  These terms shall be governed by and construed in accordance with the laws of the State of Delaware, United States, without regard to conflict of law principles. Any disputes shall be resolved in the courts of Delaware.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">9. Contact</h2>
                <p className="mt-3">
                  For questions about these terms, contact us at legal@gateco.ai or write to Gateco, Inc.
                </p>
              </section>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
