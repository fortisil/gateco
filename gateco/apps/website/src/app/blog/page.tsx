import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Blog',
  description: 'Latest news, updates, and insights from the Gateco team on AI authorization and data security.',
};

const posts = [
  {
    title: 'Introducing Gateco: Identity-Driven Authorization for AI',
    date: 'January 15, 2025',
    author: 'Gateco Team',
    excerpt:
      'We built Gateco to solve a fundamental challenge in AI security: ensuring that AI systems only access data they are authorized to see. Traditional authorization frameworks were designed for human users clicking through web interfaces. But AI agents operate differently — they make thousands of API calls, process data in complex pipelines, and act autonomously. Gateco brings identity-driven authorization to this new paradigm, giving teams fine-grained control over what their AI systems can access, when, and why.',
  },
  {
    title: 'Why Identity-Driven Authorization Matters for RAG Systems',
    date: 'February 5, 2025',
    author: 'Gateco Team',
    excerpt:
      'Retrieval-Augmented Generation (RAG) is transforming how organizations use their internal knowledge. But with RAG comes a critical security question: how do you ensure the retrieval step respects existing access controls? Without proper authorization, a RAG system might surface confidential HR documents to any employee who asks the right question. Gateco integrates directly into your RAG pipeline, enforcing document-level permissions at retrieval time so that generated responses only draw from data the requesting user is authorized to see.',
  },
  {
    title: 'Getting Started with Gateco: A Practical Guide',
    date: 'February 20, 2025',
    author: 'Gateco Team',
    excerpt:
      'Setting up Gateco takes minutes, not weeks. In this guide, we walk through the three core steps: connecting your identity provider, defining your first authorization policy, and integrating Gateco into your AI application using our SDK. We cover common patterns for policy design, explain how audit logs work, and show how to test your policies before deploying to production. Whether you are securing a single AI agent or an enterprise-wide fleet, this guide gets you up and running quickly.',
  },
];

export default function BlogPage() {
  return (
    <>
      <Header />
      <main className="py-20 sm:py-32">
        <div className="container">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Blog
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              News, insights, and technical deep dives from the Gateco team.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-3xl space-y-12">
            {posts.map((post) => (
              <article
                key={post.title}
                className="rounded-lg border border-border bg-card p-8"
              >
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <time>{post.date}</time>
                  <span aria-hidden="true">&middot;</span>
                  <span>{post.author}</span>
                </div>
                <h2 className="mt-3 text-2xl font-semibold text-foreground">
                  {post.title}
                </h2>
                <p className="mt-4 text-muted-foreground leading-7">
                  {post.excerpt}
                </p>
              </article>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
