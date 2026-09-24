"use client";

import { useWorkspace } from "@/components/providers";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { GitBranch, GitCommitHorizontal, Play, ExternalLink, Box, Activity } from "lucide-react";
import { useState, use } from "react";
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
        `/v1/analyses?workspace_id=${activeWorkspace!.id}&repository_id=${repositoryId}`
      ).catch(() => ({ analyses: [] })),
    retry: false,
  });

  if (!activeWorkspace || isRepoLoading) {
    return (
      <Shell>
        <div className="flex-1 flex items-center justify-center h-full">
          <div className="animate-pulse space-y-4 flex flex-col items-center">
            <div className="w-12 h-12 bg-[#12151A] rounded-lg border border-[#20242B]" />
            <div className="w-32 h-4 bg-[#12151A] rounded" />
          </div>
        </div>
      </Shell>
    );
  }

  if (!repo) {
    return (
      <Shell>
        <div className="flex-1 flex flex-col items-center justify-center h-full space-y-4">
          <Box className="w-12 h-12 text-[#5F6773]" />
          <h2 className="text-xl text-[#F5F7FA]">Repository Not Found</h2>
          <p className="text-[#8B93A1]">The requested repository does not exist or you lack access.</p>
        </div>
      </Shell>
    );
  }

  // Find latest analysis if any (assuming sorted or we just sort them by created_at)
  const sortedAnalyses = analysesData?.analyses
    ? [...analysesData.analyses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    : [];
  
  const latestAnalysis = sortedAnalyses.length > 0 ? sortedAnalyses[0] : null;

  return (
    <Shell>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-[#20242B] px-6 py-4 shrink-0 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <GitBranch className="w-5 h-5 text-[#8B93A1]" />
              <h1 className="text-lg font-medium text-[#F5F7FA]">{repo.name}</h1>
              <span className="text-[10px] font-mono text-[#5F6773] bg-[#12151A] border border-[#20242B] px-2 py-0.5 rounded">
                {repo.source_type || "git"}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm text-[#5F6773]">
              {repo.repository_identifier.startsWith('http') ? (
                <a 
                  href={repo.repository_identifier} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="hover:text-[#F5F7FA] hover:underline flex items-center gap-1"
                >
                  {repo.repository_identifier}
                  <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <span>{repo.repository_identifier}</span>
              )}
            </div>
          </div>
          <button
            onClick={() => setShowAnalyzeModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[#F5F7FA] text-[#08090B] hover:bg-white rounded-md text-sm font-medium transition-colors"
          >
            <Play className="w-4 h-4" />
            Analyze Repository
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          <h2 className="text-sm font-medium text-[#F5F7FA] uppercase tracking-widest text-opacity-50">Latest Analysis</h2>
          
          {isAnalysesLoading ? (
            <div className="animate-pulse w-full h-32 bg-[#0D0F12] border border-[#20242B] rounded-xl" />
          ) : !latestAnalysis ? (
            <div className="border border-[#20242B] bg-[#0D0F12] rounded-xl p-8 text-center flex flex-col items-center">
              <Activity className="w-8 h-8 text-[#5F6773] mb-4" />
              <h3 className="text-[#F5F7FA] font-medium mb-1">No Analyses Yet</h3>
              <p className="text-[#8B93A1] text-sm max-w-md">
                This repository has not been analyzed in the current workspace. Start an analysis to extract intents, generate contracts, and verify evidence.
              </p>
            </div>
          ) : (
            <div className="border border-[#20242B] bg-[#0D0F12] rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-[#20242B] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`w-2.5 h-2.5 rounded-full ${latestAnalysis.status === 'COMPLETED' ? 'bg-[#10B981]' : latestAnalysis.status === 'FAILED' ? 'bg-[#EF4444]' : 'bg-[#F59E0B] animate-pulse'}`} />
                  <span className="text-sm font-medium text-[#F5F7FA]">
                    {latestAnalysis.status}
                  </span>
                </div>
                <div className="text-xs font-mono text-[#5F6773]">
                  {new Date(latestAnalysis.created_at).toLocaleString()}
                </div>
              </div>
              <div className="px-5 py-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Analysis ID</div>
                  <div className="text-sm text-[#F5F7FA] truncate" title={latestAnalysis.id}>{latestAnalysis.id}</div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Commit</div>
                  <div className="text-sm text-[#F5F7FA] flex items-center gap-1.5 truncate">
                    <GitCommitHorizontal className="w-3.5 h-3.5 text-[#5F6773] shrink-0" />
                    {latestAnalysis.commit_id ? latestAnalysis.commit_id.substring(0, 7) : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Duration</div>
                  <div className="text-sm text-[#F5F7FA]">
                    {latestAnalysis.completed_at 
                      ? `${Math.round((new Date(latestAnalysis.completed_at).getTime() - new Date(latestAnalysis.started_at).getTime()) / 1000)}s` 
                      : "In progress"}
                  </div>
                </div>
              </div>
              
              {latestAnalysis.status === 'FAILED' && (
                <div className="px-5 py-3 border-t border-[#EF4444]/20 bg-[#EF4444]/5">
                  <p className="text-xs text-[#EF4444]">
                    This analysis failed during execution. Historical provenance from previous analyses may not apply to this state.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* History */}
          {sortedAnalyses.length > 1 && (
             <div className="pt-6 space-y-4">
               <h2 className="text-sm font-medium text-[#F5F7FA] uppercase tracking-widest text-opacity-50">History</h2>
               <div className="border border-[#20242B] bg-[#0D0F12] rounded-xl overflow-hidden divide-y divide-[#20242B]">
                 {sortedAnalyses.slice(1).map(analysis => (
                   <div key={analysis.id} className="px-5 py-3 flex items-center justify-between hover:bg-[#12151A] transition-colors">
                     <div className="flex items-center gap-4">
                       <span className={`w-2 h-2 rounded-full ${analysis.status === 'COMPLETED' ? 'bg-[#10B981]' : analysis.status === 'FAILED' ? 'bg-[#EF4444]' : 'bg-[#5F6773]'}`} />
                       <span className="text-sm font-mono text-[#8B93A1] w-20">{analysis.commit_id?.substring(0, 7) || 'N/A'}</span>
                       <span className="text-sm text-[#F5F7FA]">{analysis.status}</span>
                     </div>
                     <div className="text-xs font-mono text-[#5F6773]">
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
