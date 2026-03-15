import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ContactForm from '@/components/ContactForm';

export const metadata: Metadata = {
  title: 'Contact Us',
  description: 'Get in touch with the Gateco team for questions about our AI authorization and data security platform.',
};

export default function ContactPage() {
  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Contact Us
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Have questions about Gateco&apos;s identity-driven authorization for AI systems? Our team is here to help.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-4xl gap-12 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Send us a message</h2>
              <p className="mt-2 text-muted-foreground">
                Fill out the form and we will get back to you within 24 hours.
              </p>
              <div className="mt-8">
                <ContactForm />
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Other ways to reach us</h2>
              <div className="mt-6 space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Email</h3>
                  <p className="mt-1 text-muted-foreground">support@gateco.com</p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Response Time</h3>
                  <p className="mt-1 text-muted-foreground">
                    We typically respond within one business day. Enterprise customers receive priority support.
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Enterprise Inquiries</h3>
                  <p className="mt-1 text-muted-foreground">
                    For custom deployments, dedicated support, and volume licensing, reach out to our enterprise team at enterprise@gateco.com.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
