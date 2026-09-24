import type { NextConfig } from "next";

const backendUrl =
  process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/auth/me/",
        destination: `${backendUrl}/auth/me`,
      },
      {
        source: "/api/auth/:path*",
        destination: `${backendUrl}/auth/:path*`,
      },
      {
        source: "/api/workspaces/:path*",
        destination: `${backendUrl}/workspaces/:path*`,
      },
      {
        source: "/api/v1/workspaces",
        destination: `${backendUrl}/api/v1/workspaces/`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },

  skipTrailingSlashRedirect: true,

  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;