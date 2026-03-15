# Gateco Website

Next.js marketing website with SEO optimization.

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

## SEO Features

- Server-side rendering (SSR)
- Auto-generated sitemap
- robots.txt configuration
- OpenGraph and Twitter meta tags
- Structured data support (Organization + SoftwareApplication + FAQ)

## Project Structure

```
src/
  app/
    layout.tsx      # Root layout with metadata
    page.tsx        # Landing page (10 sections)
    pricing/        # Pricing page with comparison
    docs/           # Documentation
    blog/           # Blog
    sitemap.ts      # Auto-generated sitemap
    robots.ts       # robots.txt config
  components/       # UI components (Header, Footer, JsonLd)
  lib/              # Utilities
content/
  blog/             # MDX blog posts
  docs/             # MDX documentation
```

## Development

- Port: 3001 (to avoid conflicts with frontend on 5173)
- API URL: Configure via NEXT_PUBLIC_APP_URL
