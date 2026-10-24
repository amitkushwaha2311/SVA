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
          <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1.5 font-medium">Assurance Discovery</div>
          <h1 className="text-3xl md:text-4xl font-serif tracking-tight text-[#F5EFE5]">Intent Explorer</h1>
          <p className="text-[#B5AA9C] mt-2 font-mono text-xs md:text-sm tracking-wide">
            Trace original human statements to their semantic interpretation.
          </p>
        </header>

        <div className="space-y-6">
          {isRepoLoading || isLoading ? (
            <div className="text-[#847768] font-mono text-sm animate-pulse flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#F4D9A0] animate-ping" />
              Loading intent candidates...
            </div>
          ) : !activeAnalysis || intents.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-14 text-center bg-[#211B16] border border-[#514236] rounded-2xl shadow-xl">
              <div className="w-16 h-16 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
                <FileText className="w-8 h-8 text-[#847768]" />
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">No Intent Found</div>
              <p className="text-[#B5AA9C] max-w-sm text-sm leading-relaxed mb-4">
                {!activeAnalysis ? "No analysis has been completed for this repository yet." : "No semantic intent was found in this analysis."}
              </p>
            </div>
          ) : (
            <div className="border border-[#514236] bg-[#211B16] rounded-2xl divide-y divide-[#514236] overflow-hidden shadow-2xl">
              {intents.map((intent: any) => (
                <div key={intent.id} className="p-6 md:p-8 space-y-6">
                  <div className="flex gap-4 items-start">
                    <div className="w-10 h-10 rounded-xl bg-[#2A221B] border border-[#514236] flex items-center justify-center shrink-0 mt-1 shadow-inner">
                      <FileText className="w-5 h-5 text-[#F4D9A0]" />
                    </div>
                    <div className="space-y-5 flex-1 min-w-0">
                      
                      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                        <div className="space-y-1">
                          <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest">Original Intent</div>
                          <div className="text-xl md:text-2xl text-[#F5EFE5] font-serif leading-relaxed italic">
                            "{intent.original_statement}"
                          </div>
                        </div>
                        {intent.human_confirmed ? (
                          <div className="bg-[#10B981]/10 text-[#10B981] px-3.5 py-1.5 rounded-full flex items-center gap-2 border border-[#10B981]/30 font-mono text-xs tracking-wider shrink-0">
                            <ShieldCheck className="w-4 h-4" /> HUMAN_CONFIRMED
                          </div>
                        ) : (
                          <button 
                            onClick={() => confirmMutation.mutate(intent.id)}
                            disabled={confirmMutation.isPending}
                            className="bg-[#C8792C] hover:bg-[#b36c25] text-[#F5EFE5] px-4 py-2 rounded-xl flex items-center gap-2 font-mono text-xs tracking-wide transition-all shadow-md shadow-[#C8792C]/10 active:scale-95 shrink-0 disabled:opacity-50"
                          >
                            {confirmMutation.isPending ? "Confirming..." : "Confirm Intent"}
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-4 border-b border-[#514236] pb-6">
                        <div>
                          <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1 flex items-center gap-1.5">
                            <MapPin className="w-3 h-3 text-[#F4D9A0]" /> Source
                          </div>
                          <div className="text-[#B5AA9C] font-mono text-xs truncate" title={intent.source_file}>
                            {intent.source_file || "Unknown"}{intent.source_line ? `:${intent.source_line}` : ""}
                          </div>
                        </div>
                        <div>
                          <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1 flex items-center gap-1.5">
                            <Search className="w-3 h-3 text-[#F4D9A0]" /> Provenance
                          </div>
                          <div className="text-[#F4D9A0] font-mono text-xs bg-[#2A221B] px-2.5 py-0.5 rounded border border-[#514236] inline-block">
                            {intent.provenance || "UNKNOWN"}
                          </div>
                        </div>
                        <div>
                          <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1">Status</div>
                          <div className="text-[#10B981] font-mono text-xs flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" /> {intent.status}
                          </div>
                        </div>
                        <div>
                          <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1 flex items-center gap-1.5">
                            <AlertCircle className="w-3 h-3 text-[#C8792C]" /> Confirmation
                          </div>
                          <div className="text-[#B5AA9C] font-mono text-xs">
                            {intent.human_confirmed ? "Confirmed by user" : "Pending human review"}
                          </div>
                        </div>
                      </div>

                      {/* Structured Semantics */}
                      <div>
                         <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-3">Structured Interpretation</div>
                         {(intent.actor || intent.action || intent.resource) ? (
                            <div className="bg-[#2A221B] border border-[#514236] rounded-xl p-5 space-y-4">
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <div>
                                  <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1">Actor</div>
                                  <div className="text-[#F5EFE5] font-mono text-sm">{intent.actor || "None"}</div>
                                </div>
                                <div>
                                  <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1">Action</div>
                                  <div className="text-[#F5EFE5] font-mono text-sm">{intent.action || "None"}</div>
                                </div>
                                <div>
                                  <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-1">Resource</div>
                                  <div className="text-[#F5EFE5] font-mono text-sm">{intent.resource || "None"}</div>
                                </div>
                              </div>
                              {intent.assumptions && intent.assumptions.length > 0 && (
                                <div className="pt-3 border-t border-[#514236]/60">
                                  <div className="text-[#847768] font-mono text-[10px] uppercase tracking-widest mb-2">Assumptions</div>
                                  <ul className="list-disc pl-4 space-y-1">
                                    {intent.assumptions.map((assum: string, i: number) => (
                                      <li key={i} className="text-[#B5AA9C] font-mono text-xs">{assum}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                         ) : (
                            <div className="text-[#847768] font-mono text-xs italic">
                              No structured interpretation was safely extracted.
                            </div>
                         )}
                         {!intent.human_confirmed && (
                            <div className="mt-4 text-[#847768] text-xs">
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
