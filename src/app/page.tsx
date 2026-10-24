"use client";

import { AssuranceGraph } from "@/components/graph/AssuranceGraph";
import { AnalyzeModal } from "@/components/analysis/AnalyzeModal";
import { Shell } from "@/components/layout/Shell";
import {
  Box, ArrowRight, GitBranch, Plus, ExternalLink, ShieldCheck, Sparkles,
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
    enabled: !!activeWorkspace?.id,
    queryFn: () =>
      apiFetch<{ items: Repository[] }>(
        `/v1/orchestration/repositories?workspace_id=${activeWorkspace!.id}`
      ).catch(() => ({ items: [] })),
    retry: false,
  });

  // ── Loading ────────────────────────────────────────────────────────────────
  if (isAuthLoading || (user && isLoading && activeWorkspace)) {
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

  // ── Authenticated but no workspace selected ─────────────────────────────────
  if (user && !activeWorkspace) {
    return (
      <div className="min-h-screen bg-[#17130F] flex items-center justify-center p-6">
        <div className="bg-[#211B16] border border-[#514236] rounded-2xl p-8 max-w-sm text-center space-y-4 shadow-xl">
          <Box className="w-8 h-8 text-[#F4D9A0] mx-auto opacity-80" />
          <h2 className="font-serif text-xl text-[#F5EFE5]">No Workspace Selected</h2>
          <p className="text-[#B5AA9C] font-mono text-xs">Select or create a workspace to continue.</p>
        </div>
      </div>
    );
  }

  const hasRepos = reposData && reposData.items.length > 0;

  // ── Public Landing Page / Empty State ───────────────────────────────────────
  if (!user || !hasRepos) {
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
              {!user ? (
                <Link
                  href="/login"
                  className="bg-[#F4D9A0] text-[#17130F] font-semibold px-8 py-3.5 rounded-xl hover:bg-[#fae6bb] transition-all inline-flex items-center gap-2.5 group shadow-lg shadow-[#F4D9A0]/10 active:scale-95"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              ) : (
                <button
                  onClick={() => setShowAnalyzeModal(true)}
                  className="bg-[#F4D9A0] text-[#17130F] font-semibold px-8 py-3.5 rounded-xl hover:bg-[#fae6bb] transition-all inline-flex items-center gap-2.5 group shadow-lg shadow-[#F4D9A0]/10 active:scale-95"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              )}
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

  // ── Dashboard with repositories ────────────────────────────────────────────
  return (
    <Shell>
      {/* Header row */}
      <div className="border-b border-[#514236] -mx-6 md:-mx-8 -mt-6 md:-mt-8 px-6 md:px-8 py-5 mb-8 flex items-center justify-between bg-[#211B16]/50">
        <div>
          <h1 className="text-xl font-serif text-[#F5EFE5] tracking-wide">Repositories</h1>
          <p className="text-xs text-[#B5AA9C] font-mono mt-0.5">{reposData!.items.length} registered repositories</p>
        </div>
        <button
          onClick={() => setShowAnalyzeModal(true)}
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
