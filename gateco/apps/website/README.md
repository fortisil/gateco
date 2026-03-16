# Gateco Website

Next.js 14 marketing website for [gateco.ai](https://gateco.ai) with SEO optimization, lead capture, and MDX content.

## Getting Started

```bash
# Install dependencies
npm install

# Run development server (port 3001)
npm run dev

# Build for production
npm run build

# Run production server
npm start
```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_SITE_URL` | `https://gateco.ai` | Base URL for SEO metadata, sitemap, robots.txt |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:3000` | Target URL for "Go to App" CTAs |
| `LEAD_WEBHOOK_URL` | (none) | Webhook endpoint for lead capture form submissions |

## SEO Features

- Server-side rendering (SSR)
- Auto-generated sitemap
- robots.txt configuration
- OpenGraph and Twitter meta tags
- Structured data support (Organization + SoftwareApplication + FAQ)

## Lead Capture

Two forms submit leads via `POST /api/lead` (server-side route that forwards to `LEAD_WEBHOOK_URL`):

- **Contact page form** (`/contact`) -- captures name, email, company, and message
- **Newsletter signup** (Footer) -- captures email with `source: "newsletter"`

Both forms include loading, success, and error states with client-side email validation.

## Project Structure

```
src/
  app/
    layout.tsx      # Root layout with metadata
    page.tsx        # Landing page (10 sections)
    pricing/        # Pricing page with comparison
    contact/        # Contact form (support@gateco.ai, enterprise@gateco.ai)
    terms/          # Terms of service
    privacy/        # Privacy policy
    docs/           # Documentation
    blog/           # Blog
    api/lead/       # Lead capture API route
    sitemap.ts      # Auto-generated sitemap
    robots.ts       # robots.txt config
  components/       # UI components (Header, Footer, JsonLd)
  lib/              # Utilities (metadata helpers)
content/
  blog/             # MDX blog posts
  docs/             # MDX documentation
```

## Development

- Port: 3001 (to avoid conflicts with frontend on 5173)
- Domain: `gateco.ai` (all fallback URLs and email addresses use this domain)
- All email addresses use `@gateco.ai` (support, enterprise, privacy, legal, security)
