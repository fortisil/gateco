import type { Metadata } from 'next';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://gateco.ai';

/**
 * Build page-level metadata with site-wide defaults
 *
 * @param title - Page title (combined with site name via template)
 * @param description - Page meta description
 * @param keywords - Additional page-specific keywords
 * @param path - Page path for canonical URL
 * @returns Next.js Metadata object
 */
export function buildMetadata({
  title,
  description,
  keywords = [],
  path = '/',
}: {
  title: string;
  description: string;
  keywords?: string[];
  path?: string;
}): Metadata {
  const url = `${BASE_URL}${path}`;
  const allKeywords = [...new Set(['gateco', 'web app', ...keywords])];

  return {
    title,
    description,
    keywords: allKeywords,
    alternates: {
      canonical: url,
    },
    openGraph: {
      title,
      description,
      url,
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
    },
  };
}
