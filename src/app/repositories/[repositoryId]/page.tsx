"use client";

import { useWorkspace } from "@/components/providers";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { GitBranch, GitCommitHorizontal, Play, ExternalLink, Box, Activity } from "lucide-react";
import { useState, use, useEffect } from "react";
import { AnalyzeModal } from "@/components/analysis/AnalyzeModal";

export default function RepositoryPage({ params }: { params: Promise<{ repositoryId: string }> }) {
  const { activeWorkspace } = useWorkspace();
  const [showAnalyzeModal, setShowAnalyzeModal] = useState(false);
  const resolvedParams = use(params);
  const repositoryId = resolvedParams.repositoryId;

  const { data: repo, isLoading: isRepoLoading } = useQuery({
    queryKey: ["repository", repositoryId, activeWorkspace?.id],
    enabled: !!activeWorkspace?.id && !!repositoryId,
    queryFn: () =>
      apiFetch<any>(`/v1/repositories/${repositoryId}?workspace_id=${activeWorkspace!.id}`),
    retry: false,
  });

  const { data: analysesData, isLoading: isAnalysesLoading, refetch: refetchAnalyses } = useQuery({
    queryKey: ["analyses", repositoryId, activeWorkspace?.id],
    enabled: !!activeWorkspace?.id && !!repositoryId,
    queryFn: () =>
      apiFetch<{ analyses: any[] }>(
        `/v1/analyses/?workspace_id=${activeWorkspace!.id}&repository_id=${repositoryId}`
      ).catch(() => ({ analyses: [] })),
    retry: false,
  });

  if (!activeWorkspace || isRepoLoading) {
    return (
      <Shell>
        <div className="flex-1 flex items-center justify-center h-full">
          <div className="animate-pulse space-y-4 flex flex-col items-center">
            <div className="w-12 h-12 bg-[#2A221B] rounded-xl border border-[#514236]" />
            <div className="w-32 h-4 bg-[#2A221B] rounded-md" />
          </div>
        </div>
      </Shell>
    );
  }

  if (!repo) {
    return (
      <Shell>
        <div className="flex-1 flex flex-col items-center justify-center h-full space-y-4 p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mx-auto mb-2">
            <Box className="w-8 h-8 text-[#847768]" />
          </div>
          <h2 className="text-2xl font-serif text-[#F5EFE5]">Repository Not Found</h2>
          <p className="text-[#B5AA9C] max-w-sm text-sm">The requested repository does not exist or you lack access to it.</p>
        </div>
      </Shell>
    );
  }

  const sortedAnalyses = analysesData?.analyses
    ? [...analysesData.analyses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    : [];
  
  const latestAnalysis = sortedAnalyses.length > 0 ? sortedAnalyses[0] : null;

  return (
    <Shell>
      <div className="flex flex-col h-full space-y-6">
        {/* Header */}
        <div className="border-b border-[#514236] -mx-6 md:-mx-8 -mt-6 md:-mt-8 px-6 md:px-8 py-5 shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#211B16]/50">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center shrink-0">
                <GitBranch className="w-4 h-4 text-[#F4D9A0]" />
              </div>
              <h1 className="text-xl md:text-2xl font-serif text-[#F5EFE5] font-medium tracking-wide">{repo.name}</h1>
              <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                {repo.source_type || "git"}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs md:text-sm text-[#847768] font-mono">
              {repo.repository_identifier.startsWith('http') ? (
                <a 
                  href={repo.repository_identifier} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="hover:text-[#F4D9A0] hover:underline flex items-center gap-1.5 transition-colors"
                >
                  {repo.repository_identifier}
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              ) : (
                <span>{repo.repository_identifier}</span>
              )}
            </div>
          </div>
          <button
            onClick={() => setShowAnalyzeModal(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#F4D9A0] text-[#17130F] hover:bg-[#fae6bb] rounded-xl text-sm font-semibold transition-all shadow-md shadow-[#F4D9A0]/10 active:scale-95 shrink-0 self-start sm:self-auto"
          >
            <Play className="w-4 h-4 fill-current" />
            Analyze Repository
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto space-y-8">
          <div>
            <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-3 font-medium">Assurance Snapshot</div>
            <h2 className="text-base font-serif text-[#F5EFE5] mb-4">Latest Analysis</h2>
            
            {isAnalysesLoading ? (
              <div className="animate-pulse w-full h-36 bg-[#211B16] border border-[#514236] rounded-2xl" />
            ) : !latestAnalysis ? (
              <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-10 text-center flex flex-col items-center shadow-xl">
                <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-4">
                  <Activity className="w-7 h-7 text-[#847768]" />
                </div>
                <h3 className="text-[#F5EFE5] font-serif text-lg mb-1">No Analyses Yet</h3>
                <p className="text-[#B5AA9C] text-sm max-w-md leading-relaxed">
                  This repository has not been analyzed in the current workspace. Start an analysis to extract intents, generate contracts, and verify evidence.
                </p>
              </div>
            ) : (
              <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-2xl">
                <div className="px-6 py-4.5 border-b border-[#514236] flex items-center justify-between bg-[#2A221B]/40">
                  <div className="flex items-center gap-3">
                    <span className={`w-2.5 h-2.5 rounded-full ${latestAnalysis.status === 'COMPLETED' ? 'bg-[#10B981]' : latestAnalysis.status === 'FAILED' ? 'bg-[#EF4444]' : 'bg-[#F59E0B] animate-pulse'}`} />
                    <span className="text-sm font-medium font-mono text-[#F5EFE5]">
                      {latestAnalysis.status}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-[#847768]">
                    {new Date(latestAnalysis.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="px-6 py-5 grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Analysis ID</div>
                    <div className="text-sm font-mono text-[#F5EFE5] truncate" title={latestAnalysis.id}>{latestAnalysis.id}</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Commit</div>
                    <div className="text-sm font-mono text-[#F4D9A0] flex items-center gap-1.5 truncate">
                      <GitCommitHorizontal className="w-3.5 h-3.5 text-[#847768] shrink-0" />
                      {latestAnalysis.commit_id ? latestAnalysis.commit_id.substring(0, 7) : "N/A"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Duration</div>
                    <div className="text-sm font-mono text-[#F5EFE5]">
                      {latestAnalysis.completed_at 
                        ? `${Math.round((new Date(latestAnalysis.completed_at).getTime() - new Date(latestAnalysis.started_at).getTime()) / 1000)}s` 
                        : "In progress"}
                    </div>
                  </div>
                </div>
                
                {latestAnalysis.status === 'FAILED' && (
                  <div className="px-6 py-3.5 border-t border-[#EF4444]/30 bg-[#EF4444]/10">
                    <p className="text-xs text-[#EF4444] font-mono">
                      This analysis failed during execution. Historical provenance from previous analyses may not apply to this state.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* History */}
          {sortedAnalyses.length > 1 && (
             <div className="space-y-4">
               <h2 className="text-base font-serif text-[#F5EFE5]">Analysis History</h2>
               <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden divide-y divide-[#514236] shadow-xl">
                 {sortedAnalyses.slice(1).map(analysis => (
                   <div key={analysis.id} className="px-6 py-3.5 flex items-center justify-between hover:bg-[#2A221B]/40 transition-colors">
                     <div className="flex items-center gap-4">
                       <span className={`w-2 h-2 rounded-full ${analysis.status === 'COMPLETED' ? 'bg-[#10B981]' : analysis.status === 'FAILED' ? 'bg-[#EF4444]' : 'bg-[#847768]'}`} />
                       <span className="text-xs font-mono text-[#F4D9A0] w-20">{analysis.commit_id?.substring(0, 7) || 'N/A'}</span>
                       <span className="text-sm font-medium text-[#F5EFE5]">{analysis.status}</span>
                     </div>
                     <div className="text-xs font-mono text-[#847768]">
                       {new Date(analysis.created_at).toLocaleDateString()}
                     </div>
                   </div>
                 ))}
               </div>
             </div>
          )}
        </div>
      </div>

      {showAnalyzeModal && (
        <AnalyzeModal
          workspaceId={activeWorkspace.id}
          repositoryId={repositoryId}
          onClose={() => setShowAnalyzeModal(false)}
          onSuccess={() => { setShowAnalyzeModal(false); refetchAnalyses(); }}
        />
      )}
    </Shell>
  );
}
