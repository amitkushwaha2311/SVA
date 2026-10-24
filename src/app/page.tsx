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
          {/* Hero Section */}
          <section className="w-full flex flex-col items-center justify-center px-4 pt-20 pb-16 md:pt-28 md:pb-24 border-b border-[#514236]/30 relative overflow-hidden">
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

          {/* Metrics & Highlights Strip */}
          <section className="w-full border-b border-[#514236]/40 bg-[#211B16]/40 py-8 px-6">
            <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="font-serif text-2xl md:text-3xl text-[#F4D9A0]">100%</div>
                <div className="text-xs font-mono text-[#B5AA9C] uppercase tracking-wider mt-1">Deterministic Proofs</div>
              </div>
              <div>
                <div className="font-serif text-2xl md:text-3xl text-[#F5EFE5]">6 States</div>
                <div className="text-xs font-mono text-[#B5AA9C] uppercase tracking-wider mt-1">Decision Matrix</div>
              </div>
              <div>
                <div className="font-serif text-2xl md:text-3xl text-[#F4D9A0]">SHA-256</div>
                <div className="text-xs font-mono text-[#B5AA9C] uppercase tracking-wider mt-1">Cryptographic Evidence</div>
              </div>
              <div>
                <div className="font-serif text-2xl md:text-3xl text-[#F5EFE5]">Air-Gapped</div>
                <div className="text-xs font-mono text-[#B5AA9C] uppercase tracking-wider mt-1">Zero Execution Risk</div>
              </div>
            </div>
          </section>

          {/* Architectural Pillars Section */}
          <section className="w-full py-20 px-6 border-b border-[#514236]/30">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest">Core Capabilities</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  Architectural Pillars of Semantic Assurance
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  SVA bridges the divide between what software is expected to do and observable behavioral evidence.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0]">
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

                <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0]">
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

                <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-7 space-y-4 hover:border-[#F4D9A0]/50 transition-all shadow-xl">
                  <div className="w-12 h-12 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center text-[#F4D9A0]">
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

          {/* Verification Decision Matrix Section */}
          <section className="w-full py-20 px-6 border-b border-[#514236]/30 bg-[#211B16]/20">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest">Decision Matrix</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  Deterministic Verification States
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  SVA classifies every requirement and obligation into an unambiguous formal decision state.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-5">
                <div className="border border-[#10B981]/30 bg-[#10B981]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#10B981] font-semibold tracking-wider">PROVEN</span>
                    <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Formal mathematical proof established without contradicting behavioral evidence.
                  </p>
                </div>

                <div className="border border-[#06B6D4]/30 bg-[#06B6D4]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#06B6D4] font-semibold tracking-wider">SUPPORTED</span>
                    <CheckCircle className="w-4 h-4 text-[#06B6D4]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Empirical behavioral evidence confirms that implementation satisfies the contract.
                  </p>
                </div>

                <div className="border border-[#EF4444]/30 bg-[#EF4444]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#EF4444] font-semibold tracking-wider">VIOLATED</span>
                    <ShieldAlert className="w-4 h-4 text-[#EF4444]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Observable behavioral evidence explicitly contradicts a formal obligation or invariant.
                  </p>
                </div>

                <div className="border border-[#F59E0B]/30 bg-[#F59E0B]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#F59E0B] font-semibold tracking-wider">INCONCLUSIVE</span>
                    <Cpu className="w-4 h-4 text-[#F59E0B]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Insufficient or contradictory evidence prevents deterministic verification.
                  </p>
                </div>

                <div className="border border-[#C084FC]/30 bg-[#C084FC]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#C084FC] font-semibold tracking-wider">STALE</span>
                    <GitBranch className="w-4 h-4 text-[#C084FC]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Source code has evolved since evidence was collected; re-evaluation is required.
                  </p>
                </div>

                <div className="border border-[#9CA3AF]/30 bg-[#9CA3AF]/5 rounded-xl p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[#9CA3AF] font-semibold tracking-wider">UNKNOWN</span>
                    <Box className="w-4 h-4 text-[#9CA3AF]" />
                  </div>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Requirement registered but awaiting contract compilation and evidence harvest.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* The Verification Lifecycle / How It Works */}
          <section className="w-full py-20 px-6 border-b border-[#514236]/30">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="text-center max-w-2xl mx-auto space-y-3">
                <div className="text-xs font-mono text-[#F4D9A0] uppercase tracking-widest">Workflow</div>
                <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                  The Verification Lifecycle
                </h2>
                <p className="text-sm md:text-base text-[#B5AA9C] font-sans">
                  From repository ingestion to cryptographic assurance in four deterministic stages.
                </p>
              </div>

              <div className="grid md:grid-cols-4 gap-6">
                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3">
                  <span className="text-xs font-mono text-[#F4D9A0]">01 / INGEST</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Repository Parsing</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Untrusted code is strictly parsed into an abstract syntax tree within an air-gapped environment.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3">
                  <span className="text-xs font-mono text-[#F4D9A0]">02 / SYNTHESIZE</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Intent Extraction</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Semantic requirements are compiled into formal contracts with unambiguous invariants.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3">
                  <span className="text-xs font-mono text-[#F4D9A0]">03 / HARVEST</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Evidence Binding</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Behavioral traces and execution artifacts are hashed and bound to contracts with full provenance.
                  </p>
                </div>

                <div className="border border-[#514236] bg-[#211B16] rounded-xl p-6 space-y-3">
                  <span className="text-xs font-mono text-[#F4D9A0]">04 / ASSURE</span>
                  <h4 className="text-lg font-serif text-[#F5EFE5]">Proof Topology</h4>
                  <p className="text-xs text-[#B5AA9C] leading-relaxed">
                    Assurance graphs map verified invariants to intent, surfacing drift and violations immediately.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Enterprise Security Section */}
          <section className="w-full py-20 px-6 border-b border-[#514236]/30 bg-[#211B16]/30">
            <div className="max-w-4xl mx-auto border border-[#514236] bg-[#211B16] rounded-2xl p-8 md:p-12 shadow-2xl space-y-6">
              <div className="flex items-center gap-3 text-[#F4D9A0]">
                <Lock className="w-6 h-6" />
                <span className="text-xs font-mono tracking-widest uppercase">Air-Gapped Security Architecture</span>
              </div>
              <h2 className="text-2xl md:text-3xl font-serif text-[#F5EFE5]">
                Built for High-Assurance Enterprise Environments
              </h2>
              <p className="text-sm text-[#B5AA9C] leading-relaxed">
                Repository contents are never executed in the host environment. SVA enforces a fail-closed architecture where missing or tampered evidence results in an explicit non-proven state rather than assumed compliance.
              </p>
              <div className="grid sm:grid-cols-3 gap-4 pt-4 border-t border-[#514236]">
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5]">Untrusted Data Isolation</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">Zero arbitrary code execution</div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5]">Cryptographic Lineage</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">SHA-256 evidence sealing</div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs font-serif text-[#F5EFE5]">Continuous Drift Guard</div>
                  <div className="text-[11px] font-mono text-[#B5AA9C]">Automated divergence detection</div>
                </div>
              </div>
            </div>
          </section>

          {/* Final Call to Action Section */}
          <section className="w-full py-20 px-6 text-center">
            <div className="max-w-2xl mx-auto space-y-6">
              <h2 className="text-3xl md:text-4xl font-serif text-[#F5EFE5]">
                Ready to Verify Software Intent?
              </h2>
              <p className="text-sm md:text-base text-[#B5AA9C] leading-relaxed">
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

        {/* Comprehensive Public Footer */}
        <footer className="border-t border-[#514236]/60 bg-[#17130F] py-12 px-6">
          <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-[#2A221B] border border-[#514236] flex items-center justify-center">
                <Box className="w-3.5 h-3.5 text-[#F4D9A0]" />
              </div>
              <span className="font-serif text-base text-[#F5EFE5]">SVA Assurance</span>
              <span className="text-[10px] font-mono text-[#B5AA9C]">v2.0</span>
            </div>

            <div className="flex items-center gap-6 text-xs font-mono text-[#B5AA9C]">
              <Link href="/login" className="hover:text-[#F5EFE5] transition-colors">Sign In</Link>
              <Link href="/signup" className="hover:text-[#F5EFE5] transition-colors">Create Account</Link>
              <span className="text-[#514236]">|</span>
              <span className="text-[#10B981] flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] inline-block animate-pulse" />
                All Systems Operational
              </span>
            </div>

            <div className="text-xs font-mono text-[#847768]">
              © 2026 SVA Semantic Verification &amp; Assurance.
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
