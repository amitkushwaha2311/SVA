import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Explicit rule: /api/auth/me/ (with trailing slash) -> backend without trailing slash
      // This ensures if the browser hits /me/, it proxies to /auth/me instead of /auth/me/
      // and avoids the FastAPI 307 redirect back to /auth/me
      {
        source: "/api/auth/me/",
        destination: "http://127.0.0.1:8000/auth/me",
      },
      {
        source: "/api/auth/:path*",
        destination: "http://127.0.0.1:8000/auth/:path*",
      },
      {
        source: "/api/workspaces/:path*",
        destination: "http://127.0.0.1:8000/workspaces/:path*",
      },
      // Explicit rule: /api/v1/workspaces (no trailing slash) → backend with trailing slash
      // Prevents a 307 from FastAPI leaking the absolute backend URL to the browser.
      {
        source: "/api/v1/workspaces",
        destination: "http://127.0.0.1:8000/api/v1/workspaces/",
      },
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  skipTrailingSlashRedirect: true,
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
