import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // LLM operations (CV extraction, gap analysis) can take 30-60s+;
    // Next.js dev proxy defaults to 30s which causes ECONNRESET mid-request.
    proxyTimeout: Number(process.env.PROXY_TIMEOUT_MS ?? 300000),
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8001";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
