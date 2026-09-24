"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Box, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/components/providers";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // POST /api/auth/signup → proxied via Next.js rewrite →
      // backend POST /auth/signup (the actual registration endpoint)
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          display_name: displayName,
          workspace_name: workspaceName,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }

      // Signup already creates a session cookie — re-hydrate auth state
      await login();
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#08090B] flex flex-col justify-center items-center p-6">
      <div className="w-full max-w-sm space-y-8">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-[#12151A] border border-[#20242B] rounded-lg flex items-center justify-center mb-6">
            <Box className="w-6 h-6 text-[#F5F7FA]" />
          </div>
          <h1 className="text-2xl font-sans tracking-tight text-[#F5F7FA]">Create an Account</h1>
          <p className="text-sm font-mono text-[#5F6773] mt-2">Semantic Verification &amp; Assurance</p>
        </div>

        <div className="bg-[#0D0F12] border border-[#20242B] rounded-lg p-6 shadow-2xl">
          <form onSubmit={handleSignup} className="space-y-4">
            {error && (
              <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                <p className="text-sm text-[#EF4444]">{error}</p>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest block">Display Name</label>
              <input
                id="signup-display-name"
                type="text"
                required
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                className="w-full bg-[#12151A] border border-[#20242B] rounded px-3 py-2 text-sm text-[#F5F7FA] outline-none focus:border-[#5F6773] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest block">Email</label>
              <input
                id="signup-email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-[#12151A] border border-[#20242B] rounded px-3 py-2 text-sm text-[#F5F7FA] outline-none focus:border-[#5F6773] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest block">Password</label>
              <input
                id="signup-password"
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-[#12151A] border border-[#20242B] rounded px-3 py-2 text-sm text-[#F5F7FA] outline-none focus:border-[#5F6773] transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest block">Workspace Name</label>
              <input
                id="signup-workspace-name"
                type="text"
                required
                value={workspaceName}
                onChange={e => setWorkspaceName(e.target.value)}
                className="w-full bg-[#12151A] border border-[#20242B] rounded px-3 py-2 text-sm text-[#F5F7FA] outline-none focus:border-[#5F6773] transition-colors"
              />
            </div>

            <button
              id="signup-submit"
              type="submit"
              disabled={loading}
              className="w-full bg-[#F5F7FA] text-[#08090B] font-medium text-sm py-2 rounded hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign Up"}
            </button>
          </form>
        </div>

        <div className="text-center">
          <p className="text-sm text-[#5F6773]">
            Already have an account? <Link href="/login" className="text-[#F5F7FA] hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
