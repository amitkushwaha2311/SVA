"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { FileText, MapPin, Search, CheckCircle, AlertCircle, ShieldCheck } from "lucide-react";

export default function IntentExplorer() {
  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis, isRepoLoading } = useRepository();

  const { data: intents = [], isLoading, refetch } = useQuery({
    queryKey: ["intents", activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: async () => {
      const res = await apiFetch<any>(`/v1/intent?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`);
      return res.items || [];
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (candidateId: string) => 
      apiFetch(`/v1/intent/${candidateId}/confirm?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`, {
        method: "POST"
      }),
    onSuccess: () => refetch()
  });

  return (
    <Shell>
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA]">Intent Explorer</h1>
          <p className="text-[#8B93A1] mt-2 font-mono text-sm tracking-wide">Trace original human statements to their semantic interpretation.</p>
        </header>

        <div className="space-y-6">
          {isRepoLoading || isLoading ? (
            <div className="text-[#5F6773] font-mono text-sm animate-pulse">Loading intent candidates...</div>
          ) : !activeAnalysis || intents.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center bg-[#08090B] border border-[#20242B] rounded-lg">
              <FileText className="w-10 h-10 text-[#20242B] mb-6" />
              <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">No Intent Found</div>
              <p className="text-[#8B93A1] max-w-xs text-sm leading-relaxed mb-4">
                {!activeAnalysis ? "No analysis has been completed for this repository yet." : "No semantic intent was found in this analysis."}
              </p>
            </div>
          ) : (
            <div className="border border-[#20242B] bg-[#08090B] rounded-lg divide-y divide-[#20242B]">
              {intents.map((intent: any) => (
                <div key={intent.id} className="p-6 space-y-6">
                  <div className="flex gap-4 items-start">
                    <div className="w-8 h-8 rounded bg-[#12151A] border border-[#20242B] flex items-center justify-center shrink-0 mt-1">
                      <FileText className="w-4 h-4 text-[#F5F7FA]" />
                    </div>
                    <div className="space-y-4 flex-1">
                      
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-2">Original Intent</div>
                          <div className="text-xl text-[#F5F7FA] font-medium leading-relaxed">
                            "{intent.original_statement}"
                          </div>
                        </div>
                        {intent.human_confirmed ? (
                          <div className="bg-[#10B981]/10 text-[#10B981] px-3 py-1.5 rounded flex items-center gap-2 border border-[#10B981]/20 font-mono text-xs tracking-wide">
                            <ShieldCheck className="w-4 h-4" /> HUMAN_CONFIRMED
                          </div>
                        ) : (
                          <button 
                            onClick={() => confirmMutation.mutate(intent.id)}
                            disabled={confirmMutation.isPending}
                            className="bg-[#3B82F6] hover:bg-[#2563EB] text-white px-4 py-2 rounded flex items-center gap-2 font-mono text-sm tracking-wide transition-colors"
                          >
                            {confirmMutation.isPending ? "Confirming..." : "Confirm Intent"}
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-4 gap-6 pt-4 border-b border-[#20242B] pb-6">
                        <div>
                          <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-1"><MapPin className="w-3 h-3" /> Source</div>
                          <div className="text-[#8B93A1] font-mono text-sm">{intent.source_file || "Unknown"}{intent.source_line ? `:${intent.source_line}` : ""}</div>
                        </div>
                        <div>
                          <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-1"><Search className="w-3 h-3" /> Provenance</div>
                          <div className="text-[#8B93A1] font-mono text-sm bg-[#12151A] px-2 py-0.5 rounded border border-[#20242B] inline-block">{intent.provenance || "UNKNOWN"}</div>
                        </div>
                        <div>
                          <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1">Status</div>
                          <div className="text-[#10B981] font-mono text-sm flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" /> {intent.status}
                          </div>
                        </div>
                        <div>
                          <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Confirmation</div>
                          <div className="text-[#8B93A1] font-mono text-sm">
                            {intent.human_confirmed ? "Confirmed by user" : "Pending human review"}
                          </div>
                        </div>
                      </div>

                      {/* Structured Semantics */}
                      <div>
                         <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-4">Structured Interpretation</div>
                         {(intent.actor || intent.action || intent.resource) ? (
                            <div className="bg-[#12151A] border border-[#20242B] rounded p-4 space-y-4">
                              <div className="grid grid-cols-3 gap-4">
                                <div>
                                  <div className="text-[#5F6773] font-mono text-xs mb-1">Actor</div>
                                  <div className="text-[#F5F7FA] font-mono text-sm">{intent.actor || "None"}</div>
                                </div>
                                <div>
                                  <div className="text-[#5F6773] font-mono text-xs mb-1">Action</div>
                                  <div className="text-[#F5F7FA] font-mono text-sm">{intent.action || "None"}</div>
                                </div>
                                <div>
                                  <div className="text-[#5F6773] font-mono text-xs mb-1">Resource</div>
                                  <div className="text-[#F5F7FA] font-mono text-sm">{intent.resource || "None"}</div>
                                </div>
                              </div>
                              {intent.assumptions && intent.assumptions.length > 0 && (
                                <div className="pt-2 border-t border-[#20242B]/50">
                                  <div className="text-[#5F6773] font-mono text-xs mb-2">Assumptions</div>
                                  <ul className="list-disc pl-4 space-y-1">
                                    {intent.assumptions.map((assum: string, i: number) => (
                                      <li key={i} className="text-[#8B93A1] font-mono text-sm">{assum}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                         ) : (
                            <div className="text-[#8B93A1] font-mono text-sm italic">
                              No structured interpretation was safely extracted.
                            </div>
                         )}
                         {!intent.human_confirmed && (
                            <div className="mt-4 text-[#8B93A1] text-sm">
                              By clicking Confirm, you verify that this semantic interpretation accurately represents the intended requirement.
                            </div>
                         )}
                      </div>

                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
