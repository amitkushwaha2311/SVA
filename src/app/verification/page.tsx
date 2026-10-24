"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { ShieldCheck, FileSearch, AlertTriangle, ChevronRight, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ObligationVerification {
  obligation_id: string;
  contract_id: string;
  requirement_id: string | null;
  decision: string;
  explanation: string | null;
  supporting_evidence: string[];
  contradicting_evidence: string[];
}

interface RequirementVerification {
  id: string;
  requirement_id: string;
  contract_id: string;
  decision: string;
  explanation: string | null;
  limitations: string[];
  unresolved_obligations: string[];
}

interface VerificationList {
  requirement_verifications: RequirementVerification[];
  obligation_verifications: ObligationVerification[];
}

const DECISION_STYLES: Record<string, { color: string; border: string; bg: string }> = {
  PROVEN:      { color: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10" },
  SUPPORTED:   { color: "text-[#06B6D4]", border: "border-[#06B6D4]/30", bg: "bg-[#06B6D4]/10" },
  VIOLATED:    { color: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10" },
  UNKNOWN:     { color: "text-[#9CA3AF]", border: "border-[#9CA3AF]/30", bg: "bg-[#9CA3AF]/10" },
  INCONCLUSIVE:{ color: "text-[#F59E0B]", border: "border-[#F59E0B]/30", bg: "bg-[#F59E0B]/10" },
  STALE:       { color: "text-[#C084FC]", border: "border-[#C084FC]/30", bg: "bg-[#C084FC]/10" },
};

function StatusPill({ status }: { status: string }) {
  const s = DECISION_STYLES[status] ?? DECISION_STYLES.UNKNOWN;
  return (
    <div className={cn("inline-flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border whitespace-nowrap font-medium", s.color, s.border, s.bg)}>
      <span>{status}</span>
    </div>
  );
}

export default function VerificationPage() {
  const [selectedReq, setSelectedReq] = useState<RequirementVerification | null>(null);

  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["verification", activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: () =>
      apiFetch<VerificationList>(`/v1/verification?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`).catch(() => ({
        requirement_verifications: [],
        obligation_verifications: [],
      })),
    retry: false,
  });

  const reqs = data?.requirement_verifications ?? [];
  const obls = data?.obligation_verifications ?? [];

  return (
    <Shell>
      <div className="flex gap-0 h-full -m-6 md:-m-8 flex-col md:flex-row">
        {/* Requirements List */}
        <div className={cn(
          "flex flex-col border-r border-[#514236] bg-[#17130F]",
          selectedReq ? "md:w-[400px] md:min-w-[400px]" : "w-full"
        )}>
          <div className="p-6 md:p-8 border-b border-[#514236] bg-[#211B16]/30">
            <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1.5 font-medium">Assurance Evaluation</div>
            <h1 className="text-2xl md:text-3xl font-serif tracking-tight text-[#F5EFE5]">Verification Workspace</h1>
            <p className="text-[#B5AA9C] mt-1 font-mono text-xs tracking-wide">Evaluate obligation results and formal proofs.</p>
          </div>

          {isRepoLoading || isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-[#211B16] rounded-xl animate-pulse border border-[#514236]" />
              ))}
            </div>
          ) : !activeAnalysis ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mb-6">
                <ShieldCheck className="w-7 h-7 text-[#847768]" />
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">NO ANALYSIS</div>
              <p className="text-[#B5AA9C] max-w-xs text-sm leading-relaxed mb-4">
                No analysis has been completed for this repository yet.
              </p>
            </div>
          ) : reqs.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mb-6">
                <ShieldCheck className="w-7 h-7 text-[#847768]" />
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">NO VERIFICATION RESULT</div>
              <p className="text-[#B5AA9C] max-w-xs text-sm leading-relaxed mb-4">
                No verification result exists for this obligation.
              </p>
              <div className="font-mono text-xs tracking-widest border border-[#9CA3AF]/30 bg-[#9CA3AF]/10 text-[#9CA3AF] px-3.5 py-1.5 rounded-full font-medium">
                Current state: UNKNOWN
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-[#514236]">
              {reqs.map(req => (
                <button
                  key={req.id}
                  onClick={() => setSelectedReq(req)}
                  className={cn(
                    "w-full text-left px-6 py-4.5 transition-all hover:bg-[#211B16] group flex flex-col gap-2 relative",
                    selectedReq?.id === req.id && "bg-[#211B16] border-l-2 border-l-[#F4D9A0]"
                  )}
                >
                  <div className="flex justify-between items-start w-full">
                    <span className="font-mono text-sm text-[#F5EFE5] font-medium group-hover:text-[#F4D9A0] transition-colors">{req.requirement_id}</span>
                    <StatusPill status={req.decision} />
                  </div>
                  <p className="text-xs md:text-sm text-[#B5AA9C] line-clamp-2 leading-relaxed">{req.explanation}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Investigation Mode */}
        {selectedReq && (
          <div className="flex-1 border-t md:border-t-0 md:border-l border-[#514236] bg-[#17130F] p-6 md:p-8 flex flex-col min-h-[600px] overflow-y-auto">
            <div className="flex items-center gap-2.5 mb-6 text-[#F5EFE5] border-b border-[#514236] pb-4">
              <FileSearch className="w-5 h-5 text-[#F4D9A0]" />
              <h2 className="font-mono tracking-widest uppercase text-xs md:text-sm text-[#F4D9A0] font-medium">Investigation Mode</h2>
            </div>
            
            <div className="space-y-8 flex-1">
              <div>
                <h3 className="text-xl md:text-2xl text-[#F5EFE5] font-serif leading-relaxed mb-2 font-medium">
                  {selectedReq.explanation || "No explanation provided"}
                </h3>
                <div className="font-mono text-xs text-[#847768]">
                  Contract Binding: <span className="text-[#F4D9A0]">{selectedReq.contract_id}</span>
                </div>
              </div>

              <div className="relative pl-2">
                <div className="absolute left-[17px] top-4 bottom-4 w-px bg-[#514236]" />
                
                <div className="space-y-6 relative">
                  <TraceNode title="Requirement" id={selectedReq.requirement_id} status={selectedReq.decision} />
                  <TraceNode title="Contract" id={selectedReq.contract_id} status="READY" />
                  
                  {obls.filter(o => o.contract_id === selectedReq.contract_id).map(obl => (
                    <div key={obl.obligation_id} className="ml-8 relative">
                       <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#514236]" />
                       <TraceNode title="Obligation" id={obl.obligation_id} status={obl.decision} />
                       
                       {obl.supporting_evidence.map(ev => (
                         <div key={ev} className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#514236]" />
                           <TraceNode title="Evidence" id={ev} status="VERIFIED" />
                         </div>
                       ))}
                       {obl.contradicting_evidence.map(ev => (
                         <div key={ev} className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#514236]" />
                           <TraceNode title="Evidence" id={ev} status="VIOLATED" isError />
                         </div>
                       ))}
                       
                       {obl.supporting_evidence.length === 0 && obl.contradicting_evidence.length === 0 && (
                         <div key={`empty-${obl.obligation_id}`} className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#514236]" />
                           <TraceNode title="Evidence" id="No behavioral evidence available" status="UNAVAILABLE" isEnd />
                         </div>
                       )}
                    </div>
                  ))}
                  
                  <TraceNode title="Verification" id="Assurance proof complete" status={selectedReq.decision} isEnd />
                </div>
              </div>

              {selectedReq.decision === "UNKNOWN" && (
                <div className="mt-8 border border-[#514236] bg-[#211B16] rounded-2xl p-6 shadow-xl">
                  <div className="flex items-start gap-3.5">
                    <AlertTriangle className="w-5 h-5 text-[#F4D9A0] shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-mono text-xs tracking-widest text-[#F4D9A0] uppercase mb-2 font-medium">Why Unknown?</h4>
                      <div className="text-sm text-[#B5AA9C] space-y-4 leading-relaxed">
                        <p>Required behavioral evidence is unavailable in the current environment.</p>
                        {selectedReq.limitations && selectedReq.limitations.length > 0 && (
                           <div className="mt-4 space-y-2 bg-[#2A221B] border border-[#514236] p-4 rounded-xl">
                             <span className="block text-[10px] font-mono text-[#847768] mb-1 uppercase tracking-widest">Recorded Limitations:</span>
                             {selectedReq.limitations.map((lim, idx) => (
                               <div key={idx} className="text-[#F5EFE5] text-xs font-mono">• {lim}</div>
                             ))}
                           </div>
                        )}
                        <p className="font-mono text-xs text-[#9CA3AF] mt-4 uppercase tracking-widest pt-4 border-t border-[#514236]">
                          Therefore: UNKNOWN
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Shell>
  );
}

function TraceNode({ title, id, status, isError, isEnd }: any) {
  const isUnknown = status === "UNKNOWN" || status === "UNAVAILABLE";
  return (
    <div className="flex items-start gap-4">
      <div className={`w-8 h-8 rounded-full border border-[#514236] flex items-center justify-center shrink-0 z-10 ${isError ? 'bg-[#EF4444]/10 border-[#EF4444]/40' : isUnknown ? 'bg-[#9CA3AF]/10 border-[#9CA3AF]/40' : isEnd ? 'bg-[#10B981]/10 border-[#10B981]/40' : 'bg-[#2A221B]'}`}>
        <div className={`w-2 h-2 rounded-full ${isError ? 'bg-[#EF4444]' : isUnknown ? 'bg-[#9CA3AF]' : isEnd ? 'bg-[#10B981]' : 'bg-[#F4D9A0]'}`} />
      </div>
      <div className="pt-1 flex-1 flex justify-between items-start gap-2">
        <div>
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-0.5 font-medium">{title}</div>
          <div className="text-xs md:text-sm font-mono text-[#F5EFE5] break-all">{id}</div>
        </div>
        <StatusPill status={status} />
      </div>
    </div>
  );
}
