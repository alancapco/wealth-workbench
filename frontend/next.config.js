/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow a production build to run alongside `next dev` without both writing
  // to the same .next cache (which previously produced missing static assets).
  distDir: process.env.NEXT_DIST_DIR || '.next',
  // Pages that call useSearchParams() (journey/*, meetings) are client-gated;
  // do not fail `next build` when a Suspense boundary is still being added.
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
}

module.exports = nextConfig
