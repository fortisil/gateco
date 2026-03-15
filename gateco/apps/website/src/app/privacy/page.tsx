import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'Gateco privacy policy. Learn how we collect, use, and protect your data.',
};

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <div className="mx-auto max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Privacy Policy
            </h1>
            <p className="mt-4 text-sm text-muted-foreground">
              Last updated: January 1, 2025
            </p>

            <div className="mt-12 space-y-10 text-muted-foreground leading-7">
              <section>
                <h2 className="text-xl font-semibold text-foreground">1. Information We Collect</h2>
                <p className="mt-3">
                  Gateco collects information you provide directly when you create an account, configure authorization policies, or contact our support team. This includes your name, email address, organization name, and billing information. We also collect usage data such as API call logs, policy configurations, and system performance metrics to improve our services.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">2. How We Use Your Information</h2>
                <p className="mt-3">
                  We use collected information to provide and maintain the Gateco platform, process transactions, send service-related communications, improve our AI authorization and security features, and comply with legal obligations. We do not sell your personal information to third parties.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">3. Data Sharing</h2>
                <p className="mt-3">
                  Gateco shares your information only with service providers who assist in operating our platform (such as cloud hosting and payment processing), when required by law, or with your explicit consent. All third-party providers are bound by data processing agreements that ensure the protection of your information.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">4. Data Security</h2>
                <p className="mt-3">
                  We implement industry-standard security measures including encryption at rest and in transit, regular security audits, access controls, and monitoring. As a data security platform, we apply the same rigorous standards to protecting your information that we help our customers implement for their AI systems.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">5. Cookies and Tracking</h2>
                <p className="mt-3">
                  Gateco uses essential cookies to maintain your session and preferences. We use analytics cookies to understand how our website and platform are used. You can manage cookie preferences through your browser settings. Our platform does not use third-party advertising trackers.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">6. Your Rights</h2>
                <p className="mt-3">
                  You have the right to access, correct, or delete your personal data. You can export your data at any time through your account settings. To exercise these rights or for any privacy-related inquiries, contact us at privacy@gateco.com. We will respond to requests within 30 days.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">7. Changes to This Policy</h2>
                <p className="mt-3">
                  We may update this privacy policy from time to time. We will notify you of material changes by posting the updated policy on our website and updating the &quot;Last updated&quot; date. Continued use of Gateco after changes constitutes acceptance of the revised policy.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground">8. Contact</h2>
                <p className="mt-3">
                  For questions about this privacy policy or our data practices, contact us at privacy@gateco.com or write to our Data Protection Officer at Gateco, Inc.
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
