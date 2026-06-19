import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Set to false so TypeScript errors fail CI builds.
  // The nexus/page.tsx JSX depth exceeds tsc parser limits —
  // see PreviewScenesModal.tsx which extracts the nested modal.
  typescript: {
    ignoreBuildErrors: false,
  },
  experimental: {},
  async rewrites() {
    const apiUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
} as NextConfig;

export default nextConfig;
