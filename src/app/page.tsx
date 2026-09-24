"use client";

import { AssuranceGraph } from "@/components/graph/AssuranceGraph";
import { AnalyzeModal } from "@/components/analysis/AnalyzeModal";
import { Shell } from "@/components/layout/Shell";
import {
  Box, ArrowRight, GitBranch, Plus, ExternalLink,
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
        <div className="flex items-center justify-center h-40">
          <div className="animate-pulse space-y-4 flex flex-col items-center">
            <div className="w-12 h-12 bg-[#12151A] rounded-lg border border-[#20242B]" />
            <div className="w-32 h-4 bg-[#12151A] rounded" />
          </div>
        </div>
      </Shell>
    );
  }

  // ── Authenticated but no workspace selected ─────────────────────────────────
  if (user && !activeWorkspace) {
    return (
      <div className="min-h-screen bg-[#08090B] flex items-center justify-center">
        <p className="text-[#5F6773] font-mono text-sm">Select a workspace to continue.</p>
      </div>
    );
  }

  const hasRepos = reposData && reposData.items.length > 0;

  // ── Public Landing Page / Empty State ───────────────────────────────────────
  if (!user || !hasRepos) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center p-6 mt-20">
          <div className="max-w-2xl text-center space-y-8">
            <div className="w-16 h-16 bg-[#12151A] border border-[#20242B] rounded-xl flex items-center justify-center mx-auto mb-12 shadow-2xl">
              <Box className="w-8 h-8 text-[#F5F7FA]" />
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl md:text-5xl font-sans tracking-tight text-[#F5F7FA] font-medium">
                Software that can prove<br />it understands your intent.
              </h1>
              <p className="text-[#8B93A1] text-lg leading-relaxed max-w-xl mx-auto font-sans">
                SVA traces software behavior back to human intent using provenance,
                semantic contracts, and independently verifiable evidence.
              </p>
            </div>

            <div className="pt-8">
              {!user ? (
                <Link
                  href="/login"
                  className="bg-[#F5F7FA] text-[#08090B] font-medium px-8 py-3 rounded-md hover:bg-white transition-colors inline-flex items-center gap-2 group"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              ) : (
                <button
                  onClick={() => setShowAnalyzeModal(true)}
                  className="bg-[#F5F7FA] text-[#08090B] font-medium px-8 py-3 rounded-md hover:bg-white transition-colors inline-flex items-center gap-2 group"
                >
                  Analyze Repository
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              )}
            </div>

            <div className="border border-[#20242B] bg-[#0D0F12] rounded-lg p-4 text-left w-full max-w-md mx-auto">
              <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-3">Security Notice</div>
              <p className="text-sm text-[#8B93A1] leading-relaxed">
                Repository contents are treated as <span className="text-[#F5F7FA] font-mono">UNTRUSTED DATA</span>.
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
      {/* Header row — uses negative margin to bleed to Shell's padding edges */}
      <div className="border-b border-[#20242B] -mx-6 -mt-6 px-6 py-4 mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-sm font-medium text-[#F5F7FA]">Repositories</h1>
          <p className="text-xs text-[#5F6773] font-mono mt-0.5">{reposData!.items.length} registered</p>
        </div>
        <button
          onClick={() => setShowAnalyzeModal(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-[#12151A] border border-[#20242B] hover:border-[#5F6773] rounded-md text-sm text-[#8B93A1] hover:text-[#F5F7FA] transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Repository
        </button>
      </div>

      {/* Repository cards */}
      <div className="grid gap-3 mb-6">
        {reposData!.items.map((repo) => (
          <div
            key={repo.id}
            className="relative border border-[#20242B] bg-[#0D0F12] rounded-lg hover:border-[#5F6773] transition-colors overflow-hidden"
          >
            {/* The primary navigation block covering the entire card */}
            <Link
              href={`/repositories/${repo.id}`}
              className="block h-full focus:outline-none focus:bg-[#12151A]"
              aria-label={`Open ${repo.name} repository`}
            >
              <div className="flex items-center justify-between px-5 pt-4 pb-10">
                <div className="flex items-center gap-4 min-w-0">
                  <GitBranch className="w-4 h-4 text-[#5F6773] shrink-0" />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-[#F5F7FA] truncate">{repo.name}</div>
                    {!repo.repository_identifier.startsWith("http") && (
                      <div className="text-[11px] font-mono text-[#5F6773] truncate mt-0.5">
                        {repo.repository_identifier}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[10px] font-mono text-[#5F6773] bg-[#12151A] border border-[#20242B] px-2 py-0.5 rounded">
                    {repo.provider_type || "git"}
                  </span>
                </div>
              </div>
            </Link>

            {/* The external URL placed absolutely over the bottom padding of the Link */}
            {repo.repository_identifier.startsWith("http") && (
              <div className="absolute bottom-3 left-5">
                <a
                  href={repo.repository_identifier}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-[#5F6773] hover:text-[#F5F7FA] hover:underline focus:outline-none focus:underline"
                  aria-label={`Open ${repo.name} on external host (opens in new tab)`}
                >
                  <ExternalLink className="w-3 h-3 shrink-0" />
                  {repo.repository_identifier}
                </a>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Assurance Graph */}
      <div className="border border-[#20242B] rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-[#20242B] flex items-center justify-between">
          <span className="text-sm font-medium text-[#F5F7FA]">Assurance Graph</span>
          <span className="text-[10px] font-mono text-[#5F6773]">Live</span>
        </div>
        <div className="h-[420px]">
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
