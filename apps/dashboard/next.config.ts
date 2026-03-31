import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  server: {
    allowedHosts: ["149.104.110.122.sslip.io"],
  },
  async rewrites() {
    const apiUrl = process.env.API_INTERNAL_URL || "http://api:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
} as NextConfig;

export default nextConfig;
