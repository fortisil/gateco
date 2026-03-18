import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://gateco.ai';

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: 'Gateco',
    template: '%s | Gateco',
  },
  description: 'Gateco is a permission-aware retrieval layer that sits between AI agents and vector databases.',
  keywords: ['gateco', 'web app', 'nextjs'],
  authors: [{ name: 'Gateco Team' }],
  creator: 'Gateco',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: BASE_URL,
    siteName: 'Gateco',
    title: 'Gateco',
    description: 'Gateco is a permission-aware retrieval layer that sits between AI agents and vector databases.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Gateco',
    description: 'Gateco is a permission-aware retrieval layer that sits between AI agents and vector databases.',
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: '48x48', type: 'image/x-icon' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: '/apple-touch-icon.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
