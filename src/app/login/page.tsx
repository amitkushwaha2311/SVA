"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Box, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/components/providers";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid credentials");
      }

      await login();
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#17130F] flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Subtle ambient luxury glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-[#F4D9A0]/5 blur-[120px] rounded-full pointer-events-none" />

      <div className="w-full max-w-sm space-y-8 relative z-10">
        <div className="flex flex-col items-center text-center">
          <div className="w-14 h-14 bg-[#211B16] border border-[#514236] rounded-2xl flex items-center justify-center mb-6 shadow-xl">
            <Box className="w-7 h-7 text-[#F4D9A0]" />
          </div>
          <h1 className="text-3xl font-serif tracking-tight text-[#F5EFE5]">Sign in to SVA</h1>
          <p className="text-xs font-mono text-[#B5AA9C] mt-2 tracking-wide uppercase">
            Semantic Verification &amp; Assurance
          </p>
        </div>

        <div className="bg-[#211B16] border border-[#514236] rounded-2xl p-7 shadow-2xl backdrop-blur-md">
          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                <p className="text-sm text-[#EF4444]">{error}</p>
              </div>
            )}
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#B5AA9C] uppercase tracking-widest block font-medium">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="developer@domain.com"
                className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-sm text-[#F5EFE5] placeholder:text-[#847768] outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all font-sans"
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-[#B5AA9C] uppercase tracking-widest block font-medium">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-sm text-[#F5EFE5] placeholder:text-[#847768] outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all font-sans"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#F4D9A0] text-[#17130F] font-semibold text-sm py-2.5 rounded-xl hover:bg-[#fae6bb] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6 shadow-md shadow-[#F4D9A0]/10 active:scale-95"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin text-[#17130F]" /> : "Sign In"}
            </button>
          </form>
        </div>

        <div className="text-center">
          <p className="text-sm text-[#B5AA9C]">
            Don't have an account? <Link href="/signup" className="text-[#F4D9A0] hover:underline font-medium ml-1">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
