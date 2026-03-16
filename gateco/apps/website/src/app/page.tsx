import type { Metadata } from "next";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import JsonLd from "@/components/JsonLd";
import HomeContent from "@/components/HomeContent";

export const metadata: Metadata = {
  title: "Gateco — Gate Your AI's Access to Knowledge",
  description:
    "Permission-aware retrieval layer for AI systems. Policy enforcement, identity-based access control, and auditability for RAG pipelines.",
  keywords: [
    "AI security",
    "RAG permissions",
    "vector database access control",
    "AI governance",
    "retrieval authorization",
  ],
};

const ORG_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Gateco",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://gateco.ai",
};

const PRODUCT_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Gateco",
  applicationCategory: "SecurityApplication",
  operatingSystem: "Web",
  description:
    "Permission-aware retrieval layer for AI systems with policy enforcement and audit trails.",
};

export default function HomePage() {
  return (
    <>
      <Header />
      <JsonLd schema={ORG_SCHEMA} />
      <JsonLd schema={PRODUCT_SCHEMA} />
      <main className="flex min-h-screen flex-col">
        <HomeContent />
      </main>
      <Footer />
    </>
  );
}
