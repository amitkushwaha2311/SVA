"use client";

import { AssuranceGraph } from "@/components/graph/AssuranceGraph";
import { AnalyzeModal } from "@/components/analysis/AnalyzeModal";
import { Shell } from "@/components/layout/Shell";
import {
  Box, ArrowRight, GitBranch, Plus, ExternalLink, ShieldCheck, Sparkles,
  FileText, Scale, Eye, CheckCircle2, ShieldAlert, Cpu, Lock, CheckCircle
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useAuth } from "@/components/providers";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Repository {
  id: string;
  name: string;
  provider_type: string | null;
  repository_identifier: string;
  created_at: string;
}

export default function Dashboard() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const { activeWorkspace } = useWorkspace();
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const router = useRouter();

  const { data: reposData, isLoading, refetch: refetchRepos } = useQuery({
    queryKey: ["repositories", activeWorkspace?.id],
    enabled: !!activeWorkspace?.id && !!user,
    queryFn: () =>
      apiFetch<{ items: Repository[] }>(
        `/v1/orchestration/repositories?workspace_id=${activeWorkspace!.id}`
      ).catch(() => ({ items: [] })),
    retry: false,
  });

  // ── Auth Loading State ───────────────────────────────────────────────────────
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-[#17130F] flex items-center justify-center p-6 text-[#F5EFE5]">
        <div className="animate-pulse space-y-4 flex flex-col items-center">
          <div className="w-12 h-12 bg-[#2A221B] rounded-xl border border-[#514236] flex items-center justify-center">
            <Box className="w-6 h-6 text-[#F4D9A0] opacity-80" />
          </div>
          <div className="w-32 h-3 bg-[#2A221B] rounded-md" />
        </div>
      </div>
    );
  }

  // ── Public Marketing Landing Page (Unauthenticated) ─────────────────────────
  if (!user) {
    return (
      <div className="min-h-screen w-full bg-[#17130F] text-[#F5EFE5] flex flex-col overflow-x-hidden selection:bg-[#F4D9A0]/20 selection:text-[#F4D9A0]">
        {/* Public Header / Navigation */}
        <header className="border-b border-[#514236]/60 bg-[#17130F]/90 backdrop-blur-md sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-[#2A221B] border border-[#514236] flex items-center justify-center group-hover:border-[#F4D9A0]/50 transition-colors shadow-inner">
                <Box className="w-4 h-4 text-[#F4D9A0]" />
              </div>
              <div className="flex flex-col">
                <span className="font-serif text-lg tracking-wider font-semibold text-[#F5EFE5] leading-none">SVA</span>
                <span className="text-[9px] font-mono text-[#B5AA9C] tracking-widest uppercase mt-0.5">Assurance</span>
              </div>
            </Link>

            <nav className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-sm font-medium text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors px-3 py-1.5"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="text-sm font-medium px-4 py-2 rounded-xl bg-[#2A221B] border border-[#514236] text-[#F5EFE5] hover:border-[#F4D9A0]/60 hover:text-[#F4D9A0] transition-all shadow-sm"
              >
                Create Account
              </Link>
            </nav>
          </div>
        </header>

        {/* Public Hero & Marketing Content */}
        <main className="w-full flex flex-col">
          {/* Hero Section with Video Background */}
          <section className="w-full flex flex-col items-center justify-center px-4 pt-20 pb-16 md:pt-28 md:pb-24 border-b border-[#514236]/30 relative overflow-hidden">
            {/* Background Video with Gradient Scrim */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover opacity-25 motion-reduce:hidden"
                src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260418_080021_d598092b-c4c2-4e53-8e46-94cf9064cd50.mp4"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-[#17130F]/90 via-[#17130F]/80 to-[#17130F]" />
            </div>

            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[#F4D9A0]/5 blur-[140px] rounded-full pointer-events-none" />

            <div className="max-w-3xl text-center space-y-8 relative z-10">
              {/* Elegant Emblem */}
              <div className="relative inline-block mx-auto mb-2">
                <div className="absolute inset-0 bg-[#F4D9A0]/10 rounded-2xl blur-xl" />
                <div className="relative w-16 h-16 bg-[#211B16] border border-[#514236] rounded-2xl flex items-center justify-center mx-auto shadow-2xl">
                  <Box className="w-8 h-8 text-[#F4D9A0]" />
                </div>
              </div>

              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#514236] bg-[#2A221B]/80 text-[#F4D9A0] text-xs font-mono tracking-widest uppercase">
                  <Sparkles className="w-3.5 h-3.5 text-[#F4D9A0]" />
                  Semantic Verification Engine
                </div>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif tracking-tight text-[#F5EFE5] leading-[1.12]">
                  Software that can prove<br />
                  <span className="italic text-[#F4D9A0]">it understands your intent.</span>
                </h1>
                <p className="text-[#B5AA9C] text-base md:text-lg leading-relaxed max-w-xl mx-auto font-sans">
                  SVA traces software behavior back to human intent using rigorous provenance,
                  semantic contracts, and independently verifiable behavioral evidence.
                </p>
              </div>

              <div className="pt-2">
                <Link
                  href="/login"
                  className="bg-[#F4D9A0] text-[#17130F] font-semibold px-8 py-3.5 rounded-xl hover:bg-[#fae6bb] transition-all inline-flex items-center gap-2.5 group shadow-lg shadow-[#F4D9A0]/10 active:scale-95"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>

              <div className="border border-[#514236] bg-[#211B16] rounded-xl p-5 text-left w-full max-w-md mx-auto shadow-xl">
                <div className="text-[10px] font-mono text-[#C8792C] uppercase tracking-widest mb-2 flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Security Notice
                </div>
                <p className="text-sm text-[#B5AA9C] leading-relaxed">
                  Repository contents are treated as <span className="text-[#F5EFE5] font-mono font-medium">UNTRUSTED DATA</span>.
                  No repository code is executed during static analysis. Evidence is independently verified.
                </p>
              </div>
            </div>
          </section>

          {/* 1. Assurance Metrics Strip */}
          <section className="w-full border-b border-[#514236]/40 bg-[#211B16]/50 py-10 px-6 relative">
            <div className="max-w-6xl mx-auto space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                <div className="p-4 rounded-xl border border-[#514236]/50 bg-[#17130F]/60 backdrop-blur-sm">
                  <div className="font-serif text-3xl md:text-4xl text-[#F4D9A0] font-semibold">100%</div>
                  <div className="text-xs font-mono text-[#F5EFE5] uppercase tracking-wider mt-1.5 font-medium">Deterministic Proofs</div>
                  <div className="text-[11px] text-[#B5AA9C] mt-1 font-sans">Strict deduction; zero probabilistic leaps.</div>
                </div>
                <div className="p-4 rounded-xl border border-[#514236]/50 bg-[#17130F]/60 backdrop-blur-sm">
                  <div className="font-serif text-3xl md:text-4xl text-[#F5EFE5] font-semibold">6 States</div>
                  <div className="text-xs font-mono text-[#F5EFE5] uppercase tracking-wider mt-1.5 font-medium">Decision Matrix</div>
                  <div className="text-[11px] text-[#B5AA9C] mt-1 font-sans">Formal taxonomy from PROVEN to UNKNOWN.</div>
                </div>
                <div className="p-4 rounded-xl border border-[#514236]/50 bg-[#17130F]/60 backdrop-blur-sm">
                  <div className="font-serif text-3xl md:text-4xl text-[#F4D9A0] font-semibold">SHA-256</div>
                  <div className="text-xs font-mono text-[#F5EFE5] uppercase tracking-wider mt-1.5 font-medium">Cryptographic Evidence</div>
                  <div className="text-[11px] text-[#B5AA9C] mt-1 font-sans">Immutable hash sealing for audit trails.</div>
                </div>
                <div className="p-4 rounded-xl border border-[#514236]/50 bg-[#17130F]/60 backdrop-blur-sm">
                  <div className="font-serif text-3xl md:text-4xl text-[#F5EFE5] font-semibold">Air-Gapped</div>
                  <div className="text-xs font-mono text-[#F5EFE5] uppercase tracking-wider mt-1.5 font-medium">Zero Execution Risk</div>
                  <div className="text-[11px] text-[#B5AA9C] mt-1 font-sans">Static analysis isolates untrusted repos.</div>
                </div>
              </div>
              <div className="text-center">
                <p className="text-[11px] font-mono text-[#847768] tracking-wide">
                  Qualified Assurance Guarantee: Candidate mappings alone are never counted as behavioral proof.
                </p>
              </div>
            </div>
          </section>

          {/* 2. Core Capabilities Section with Video Background */}
          <section className="w-full py-24 px-6 border-b border-[#514236]/30 relative overflow-hidden">
            {/* Background Video */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover opacity-20 motion-reduce:hidden"
                src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260418_094631_d30ab262-45ee-4b7d-99f3-5d5848c8ef13.mp4"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-[#17130F] via-[#17130F]/85 to-[#17130F]" />
            </div>

            <div className="max-w-6xl mx-auto space-y-12 relative z-10">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">Core Capabilities</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  Architectural Pillars of Semantic Assurance
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  SVA bridges the divide between what software is expected to do and observable behavioral evidence.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div className="border border-[#514236] bg-[#211B16]/90 backdrop-blur-md rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl group">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0] group-hover:scale-105 transition-transform">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2 py-0.5 rounded-full uppercase">
                      Intent Discovery
                    </span>
                    <h3 className="text-xl font-serif text-[#F5EFE5]">Specification &amp; AST Analysis</h3>
                    <p className="text-sm text-[#B5AA9C] leading-relaxed">
                      Extracts latent developer intent across source code, docstrings, commit history, and interfaces into unified semantic intermediate representations.
                    </p>
                  </div>
                </div>

                <div className="border border-[#514236] bg-[#211B16]/90 backdrop-blur-md rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl group">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0] group-hover:scale-105 transition-transform">
                    <Scale className="w-6 h-6" />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2 py-0.5 rounded-full uppercase">
                      Contract Compiler
                    </span>
                    <h3 className="text-xl font-serif text-[#F5EFE5]">Formal Semantic Contracts</h3>
                    <p className="text-sm text-[#B5AA9C] leading-relaxed">
                      Compiles human requirements and ambiguous invariants into mathematically rigorous obligations ready for automated verification.
                    </p>
                  </div>
                </div>

                <div className="border border-[#514236] bg-[#211B16]/90 backdrop-blur-md rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl group">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0] group-hover:scale-105 transition-transform">
                    <Eye className="w-6 h-6" />
                  </div>
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2 py-0.5 rounded-full uppercase">
                      Evidence Ledger
                    </span>
                    <h3 className="text-xl font-serif text-[#F5EFE5]">Provenance &amp; Attestation</h3>
                    <p className="text-sm text-[#B5AA9C] leading-relaxed">
                      Binds behavioral artifacts, traces, and invariant proofs with cryptographic hashes, guaranteeing tamper-proof audit trails.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 3. Verification Decision Matrix Section */}
          <section className="w-full py-24 px-6 border-b border-[#514236]/30 bg-[#211B16]/20">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">Decision Matrix</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  Deterministic Verification States
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  SVA classifies every requirement and obligation into an unambiguous formal decision state.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
                <div className="border border-[#10B981]/30 bg-[#10B981]/5 rounded-xl p-5 space-y-2 hover:border-[#10B981]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#10B981] font-semibold tracking-wider">PROVEN</span>
                    <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Formal mathematical proof or deterministic test execution established without contradicting behavioral evidence.
                  </p>
                </div>

                <div className="border border-[#06B6D4]/30 bg-[#06B6D4]/5 rounded-xl p-5 space-y-2 hover:border-[#06B6D4]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#06B6D4] font-semibold tracking-wider">SUPPORTED</span>
                    <CheckCircle className="w-4 h-4 text-[#06B6D4]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Empirical behavioral evidence confirms that implementation satisfies the contract, pending full formal proof.
                  </p>
                </div>

                <div className="border border-[#EF4444]/30 bg-[#EF4444]/5 rounded-xl p-5 space-y-2 hover:border-[#EF4444]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#EF4444] font-semibold tracking-wider">VIOLATED</span>
                    <ShieldAlert className="w-4 h-4 text-[#EF4444]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Observable behavioral evidence explicitly contradicts a formal obligation, boundary, or invariant.
                  </p>
                </div>

                <div className="border border-[#F59E0B]/30 bg-[#F59E0B]/5 rounded-xl p-5 space-y-2 hover:border-[#F59E0B]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#F59E0B] font-semibold tracking-wider">INCONCLUSIVE</span>
                    <Cpu className="w-4 h-4 text-[#F59E0B]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Static candidate mappings or ambiguous test outputs cannot definitively prove or disprove the obligation.
                  </p>
                </div>

                <div className="border border-[#C084FC]/30 bg-[#C084FC]/5 rounded-xl p-5 space-y-2 hover:border-[#C084FC]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#C084FC] font-semibold tracking-wider">STALE</span>
                    <GitBranch className="w-4 h-4 text-[#C084FC]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Source code has evolved since evidence was collected; re-evaluation and trace synchronization is required.
                  </p>
                </div>

                <div className="border border-[#9CA3AF]/30 bg-[#9CA3AF]/5 rounded-xl p-5 space-y-2 hover:border-[#9CA3AF]/50 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#9CA3AF] font-semibold tracking-wider">UNKNOWN</span>
                    <Box className="w-4 h-4 text-[#9CA3AF]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Requirement registered but awaiting contract compilation or behavioral evidence harvest in the environment.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* 4. The Verification Lifecycle / Workflow */}
          <section className="w-full py-24 px-6 border-b border-[#514236]/30">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">Workflow</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  The Verification Lifecycle
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  From repository ingestion to cryptographic assurance in four deterministic stages.
                </p>
              </div>

              <div className="grid md:grid-cols-4 gap-6">
                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3 hover:border-[#F4D9A0]/40 transition-colors">
                  <span className="text-xs font-mono text-[#F4D9A0] font-medium">01 / INGEST</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Repository Parsing</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Untrusted code is strictly parsed into an abstract syntax tree within an air-gapped environment.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3 hover:border-[#F4D9A0]/40 transition-colors">
                  <span className="text-xs font-mono text-[#F4D9A0] font-medium">02 / SYNTHESIZE</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Intent Extraction</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Semantic requirements are compiled into formal contracts with unambiguous invariants.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3 hover:border-[#F4D9A0]/40 transition-colors">
                  <span className="text-xs font-mono text-[#F4D9A0] font-medium">03 / HARVEST</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Evidence Binding</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Behavioral traces and execution artifacts are hashed and bound to contracts with full provenance.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3 hover:border-[#F4D9A0]/40 transition-colors">
                  <span className="text-xs font-mono text-[#F4D9A0] font-medium">04 / ASSURE</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Proof Topology</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Assurance graphs map verified invariants to intent, surfacing drift and violations immediately.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* 5. Enterprise Security Architecture Section */}
          <section className="w-full py-24 px-6 border-b border-[#514236]/30 bg-[#211B16]/30">
            <div className="max-w-4xl mx-auto border border-[#514236] bg-[#211B16] rounded-2xl p-8 md:p-12 shadow-2xl space-y-6">
              <div className="flex items-center gap-3 text-[#F4D9A0]">
                <Lock className="w-6 h-6" />
                <span className="text-xs font-mono tracking-widest uppercase font-medium">Air-Gapped Security Architecture</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-serif text-[#F5EFE5]">
                Built for High-Assurance Enterprise Environments
              </h2>
              <p className="text-sm text-[#B5AA9C] leading-relaxed">
                Repository contents are never executed in the host environment. SVA enforces a fail-closed architecture where missing or tampered evidence results in an explicit non-proven state rather than assumed compliance.
              </p>
              <div className="grid sm:grid-cols-3 gap-4 pt-4 border-t border-[#514236]">
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5] font-medium">Untrusted Data Isolation</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">Zero arbitrary code execution</div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5] font-medium">Cryptographic Lineage</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">SHA-256 evidence sealing</div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5] font-medium">Continuous Drift Guard</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">Automated divergence detection</div>
                </div>
              </div>
            </div>
          </section>

          {/* 6. Final Call to Action Section */}
          <section className="w-full py-24 px-6 text-center relative overflow-hidden">
            <div className="max-w-2xl mx-auto space-y-6 relative z-10">
              <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                Ready to Verify Software Intent?
              </h2>
              <p className="text-sm md:text-base text-[#B5AA9C] leading-relaxed font-sans">
                Start evaluating repository semantics, compile formal contracts, and guarantee behavioral evidence today.
              </p>
              <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/login"
                  className="w-full sm:w-auto bg-[#F4D9A0] text-[#17130F] font-semibold px-8 py-3.5 rounded-xl hover:bg-[#fae6bb] transition-all inline-flex items-center justify-center gap-2.5 group shadow-lg shadow-[#F4D9A0]/10 active:scale-95"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  href="/signup"
                  className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#2A221B] border border-[#514236] text-[#F5EFE5] hover:border-[#F4D9A0]/60 hover:text-[#F4D9A0] transition-all inline-flex items-center justify-center font-medium"
                >
                  Create Account
                </Link>
              </div>
            </div>
          </section>
        </main>

        {/* 7. Cinematic Footer */}
        <footer className="relative w-full border-t border-[#514236]/60 bg-[#17130F] overflow-hidden">
          {/* Lower Background Video & Poster Fallback */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <video
              autoPlay
              loop
              muted
              playsInline
              poster="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20261014_121838_c97d0940-f430-4304-8573-4f47ee44f447.png"
              className="absolute inset-0 w-full h-full object-cover object-bottom opacity-35 motion-reduce:hidden"
              src="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/4d01c727-d9c5-47c8-a778-35a451ffd39f.mp4"
            />
            <img
              src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20261014_121838_c97d0940-f430-4304-8573-4f47ee44f447.png"
              alt="Meadow backdrop"
              className="absolute inset-0 w-full h-full object-cover object-bottom opacity-25 hidden motion-reduce:block"
            />
            {/* Soft pale-lavender mist fade adapted to dark SVA palette */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  "linear-gradient(180deg, #17130F 0%, rgba(23,19,15,0.92) 25%, rgba(32,26,38,0.7) 60%, rgba(225,215,245,0.12) 85%, rgba(23,19,15,0.95) 100%)",
              }}
            />
          </div>

          <div className="relative z-10 max-w-6xl mx-auto px-6 pt-16 pb-12 flex flex-col justify-between">
            {/* Top Row: Brand & 3 Link Columns */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-10 pb-12 border-b border-[#514236]/40">
              {/* Brand Summary */}
              <div className="md:col-span-2 space-y-4">
                <Link href="/" className="flex items-center gap-2.5 group">
                  <div className="w-9 h-9 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center group-hover:border-[#F4D9A0]/50 transition-colors shadow-inner">
                    <Box className="w-5 h-5 text-[#F4D9A0]" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-serif text-xl tracking-wider font-semibold text-[#F5EFE5] leading-none">
                      SVA
                    </span>
                    <span className="text-[10px] font-mono text-[#B5AA9C] tracking-widest uppercase mt-0.5">
                      Assurance
                    </span>
                  </div>
                </Link>
                <p className="text-xs md:text-sm text-[#B5AA9C] leading-relaxed max-w-sm font-sans">
                  Continuous semantic verification, cryptographic evidence ledgers, and formal contracts for software codebases.
                </p>
                <div className="pt-2">
                  <span className="inline-flex items-center gap-2 text-xs font-mono text-[#10B981] bg-[#10B981]/10 border border-[#10B981]/30 px-3 py-1 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block animate-pulse" />
                    All Systems Operational
                  </span>
                </div>
              </div>

              {/* Column 1: Product */}
              <div className="space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">
                  Product
                </div>
                <ul className="space-y-2 text-xs font-mono">
                  <li>
                    <Link href="/intent" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Intent Discovery
                    </Link>
                  </li>
                  <li>
                    <Link href="/contracts" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Semantic Contracts
                    </Link>
                  </li>
                  <li>
                    <Link href="/evidence" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Evidence Ledger
                    </Link>
                  </li>
                  <li>
                    <Link href="/verification" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Assurance Verification
                    </Link>
                  </li>
                  <li>
                    <Link href="/drift" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Drift Monitor
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Column 2: Resources */}
              <div className="space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">
                  Resources
                </div>
                <ul className="space-y-2 text-xs font-mono">
                  <li>
                    <Link href="/ambiguity" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Ambiguity Resolution
                    </Link>
                  </li>
                  <li>
                    <Link href="/security" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Security Architecture
                    </Link>
                  </li>
                  <li>
                    <Link href="/activity" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      System Activity
                    </Link>
                  </li>
                  <li>
                    <a
                      href="https://github.com/amitkushwaha2311/SVA"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors inline-flex items-center gap-1"
                    >
                      GitHub Repository
                      <ExternalLink className="w-3 h-3 opacity-70" />
                    </a>
                  </li>
                </ul>
              </div>

              {/* Column 3: Company & Access */}
              <div className="space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest font-medium">
                  Company
                </div>
                <ul className="space-y-2 text-xs font-mono">
                  <li>
                    <Link href="/login" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Analyze Repository
                    </Link>
                  </li>
                  <li>
                    <Link href="/signup" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Create Account
                    </Link>
                  </li>
                  <li>
                    <Link href="/login" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Sign In
                    </Link>
                  </li>
                  <li>
                    <Link href="/security" className="text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors">
                      Threat Isolation
                    </Link>
                  </li>
                </ul>
              </div>
            </div>

            {/* Giant Translucent SVA Wordmark */}
            <div className="w-full text-center pointer-events-none select-none my-6 md:my-10 overflow-hidden leading-none">
              <span className="font-serif text-[100px] sm:text-[150px] md:text-[210px] font-bold tracking-[0.22em] text-[#F5EFE5]/[0.04] uppercase inline-block">
                SVA
              </span>
            </div>

            {/* Bottom Bar: Copyright & Security Note */}
            <div className="pt-6 border-t border-[#514236]/30 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#847768]">
              <div>
                © 2026 SVA Semantic Verification &amp; Assurance. All rights reserved.
              </div>
              <div className="flex items-center gap-4">
                <span>Zero arbitrary code execution.</span>
                <span className="text-[#514236]">|</span>
                <span>Fail-closed verification runtime.</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    );
  }

  // ── Authenticated: Workspace Selection Missing ──────────────────────────────
  if (!activeWorkspace) {
    return (
      <Shell>
        <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] p-8 text-center space-y-4">
          <div className="w-16 h-16 bg-[#211B16] border border-[#514236] rounded-2xl flex items-center justify-center mx-auto shadow-xl">
            <Box className="w-8 h-8 text-[#F4D9A0] opacity-80" />
          </div>
          <div className="space-y-2 max-w-sm">
            <h2 className="font-serif text-2xl text-[#F5EFE5]">No Workspace Selected</h2>
            <p className="text-[#B5AA9C] font-mono text-xs leading-relaxed">
              Select or create a workspace from the header dropdown above to view repositories and assurance metrics.
            </p>
          </div>
        </div>
      </Shell>
    );
  }

  // ── Authenticated: Repository Loading State ─────────────────────────────────
  if (isLoading) {
    return (
      <Shell>
        <div className="flex items-center justify-center h-48">
          <div className="animate-pulse space-y-4 flex flex-col items-center">
            <div className="w-12 h-12 bg-[#2A221B] rounded-xl border border-[#514236]" />
            <div className="w-32 h-4 bg-[#2A221B] rounded-md" />
          </div>
        </div>
      </Shell>
    );
  }

  const hasRepos = reposData && reposData.items.length > 0;

  const handleAnalyzeClick = () => {
    if (activeWorkspace) {
      setShowAnalyzeModal(true);
    }
  };

  // ── Authenticated: Empty State (No Repositories Yet) ────────────────────────
  if (!hasRepos) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center px-4 py-12 md:py-16">
          <div className="max-w-2xl text-center space-y-8">
            {/* Elegant Emblem */}
            <div className="relative inline-block mx-auto mb-2">
              <div className="absolute inset-0 bg-[#F4D9A0]/10 rounded-2xl blur-xl" />
              <div className="relative w-16 h-16 bg-[#211B16] border border-[#514236] rounded-2xl flex items-center justify-center mx-auto shadow-2xl">
                <Box className="w-8 h-8 text-[#F4D9A0]" />
              </div>
            </div>

            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#514236] bg-[#2A221B]/80 text-[#F4D9A0] text-xs font-mono tracking-widest uppercase">
                <Sparkles className="w-3.5 h-3.5 text-[#F4D9A0]" />
                Semantic Verification Engine
              </div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif tracking-tight text-[#F5EFE5] leading-[1.12]">
                Software that can prove<br />
                <span className="italic text-[#F4D9A0]">it understands your intent.</span>
              </h1>
              <p className="text-[#B5AA9C] text-base md:text-lg leading-relaxed max-w-xl mx-auto font-sans">
                SVA traces software behavior back to human intent using rigorous provenance,
                semantic contracts, and independently verifiable behavioral evidence.
              </p>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleAnalyzeClick}
                className="bg-[#F4D9A0] text-[#17130F] font-semibold px-8 py-3.5 rounded-xl hover:bg-[#fae6bb] transition-all inline-flex items-center gap-2.5 group shadow-lg shadow-[#F4D9A0]/10 active:scale-95"
              >
                Analyze Repository
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

            <div className="border border-[#514236] bg-[#211B16] rounded-xl p-5 text-left w-full max-w-md mx-auto shadow-xl">
              <div className="text-[10px] font-mono text-[#C8792C] uppercase tracking-widest mb-2 flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5" />
                Security Notice
              </div>
              <p className="text-sm text-[#B5AA9C] leading-relaxed">
                Repository contents are treated as <span className="text-[#F5EFE5] font-mono font-medium">UNTRUSTED DATA</span>.
                No repository code is executed during static analysis. Evidence is independently verified.
              </p>
            </div>
          </div>

          {showAnalyzeModal && activeWorkspace && (
            <AnalyzeModal
              workspaceId={activeWorkspace.id}
              onClose={() => setShowAnalyzeModal(false)}
              onSuccess={() => { setShowAnalyzeModal(false); refetchRepos(); }}
            />
          )}
        </div>
      </Shell>
    );
  }

  // ── Authenticated: Dashboard with Repositories ──────────────────────────────
  return (
    <Shell>
      {/* Header row */}
      <div className="border-b border-[#514236] -mx-6 md:-mx-8 -mt-6 md:-mt-8 px-6 md:px-8 py-5 mb-8 flex items-center justify-between bg-[#211B16]/50">
        <div>
          <h1 className="text-xl font-serif text-[#F5EFE5] tracking-wide">Repositories</h1>
          <p className="text-xs text-[#B5AA9C] font-mono mt-0.5">{reposData!.items.length} registered repositories</p>
        </div>
        <button
          onClick={handleAnalyzeClick}
          className="flex items-center gap-2 px-4 py-2 bg-[#2A221B] border border-[#514236] hover:border-[#F4D9A0]/50 rounded-xl text-sm font-medium text-[#F5EFE5] hover:text-[#F4D9A0] transition-all shadow-sm"
        >
          <Plus className="w-4 h-4 text-[#F4D9A0]" />
          Add Repository
        </button>
      </div>

      {/* Repository cards */}
      <div className="grid gap-4 mb-8">
        {reposData!.items.map((repo) => (
          <div
            key={repo.id}
            className="relative border border-[#514236] bg-[#211B16] rounded-xl hover:border-[#F4D9A0]/50 transition-all hover:shadow-lg hover:shadow-[#F4D9A0]/5 overflow-hidden group"
          >
            {/* The primary navigation block covering the entire card */}
            <Link
              href={`/repositories/${repo.id}`}
              className="block h-full focus:outline-none focus:bg-[#2A221B]/40"
              aria-label={`Open ${repo.name} repository`}
            >
              <div className="flex items-center justify-between px-6 pt-5 pb-10">
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-[#2A221B] border border-[#514236] flex items-center justify-center shrink-0 group-hover:border-[#F4D9A0]/50 transition-colors">
                    <GitBranch className="w-4 h-4 text-[#F4D9A0]" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-base font-medium text-[#F5EFE5] truncate group-hover:text-[#F4D9A0] transition-colors">{repo.name}</div>
                    {!repo.repository_identifier.startsWith("http") && (
                      <div className="text-xs font-mono text-[#B5AA9C] truncate mt-0.5">
                        {repo.repository_identifier}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2.5 py-1 rounded-full uppercase tracking-wider">
                    {repo.provider_type || "git"}
                  </span>
                </div>
              </div>
            </Link>

            {/* The external URL placed absolutely over the bottom padding of the Link */}
            {repo.repository_identifier.startsWith("http") && (
              <div className="absolute bottom-3.5 left-6">
                <a
                  href={repo.repository_identifier}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-mono text-[#847768] hover:text-[#F4D9A0] hover:underline focus:outline-none focus:underline transition-colors"
                  aria-label={`Open ${repo.name} on external host (opens in new tab)`}
                >
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                  {repo.repository_identifier}
                </a>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Assurance Graph */}
      <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-6 py-4 border-b border-[#514236] bg-[#2A221B]/40 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="font-serif text-base font-medium text-[#F5EFE5]">Assurance Graph</span>
            <span className="text-[10px] font-mono text-[#B5AA9C] bg-[#211B16] border border-[#514236] px-2 py-0.5 rounded">Semantic Topology</span>
          </div>
          <span className="text-[10px] font-mono text-[#10B981] bg-[#10B981]/10 border border-[#10B981]/30 px-2 py-0.5 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
            Live
          </span>
        </div>
        <div className="h-[460px]">
          <AssuranceGraph />
        </div>
      </div>

      {showAnalyzeModal && activeWorkspace && (
        <AnalyzeModal
          workspaceId={activeWorkspace.id}
          onClose={() => setShowAnalyzeModal(false)}
          onSuccess={() => { setShowAnalyzeModal(false); refetchRepos(); }}
        />
      )}
    </Shell>
  );
}
