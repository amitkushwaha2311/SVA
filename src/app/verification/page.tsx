"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
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
  UNKNOWN:     { color: "text-[#8B5CF6]", border: "border-[#8B5CF6]/30", bg: "bg-[#8B5CF6]/10" },
  INCONCLUSIVE:{ color: "text-[#9333EA]", border: "border-[#9333EA]/30", bg: "bg-[#9333EA]/10" },
  STALE:       { color: "text-[#D97706]", border: "border-[#D97706]/30", bg: "bg-[#D97706]/10" },
};

function StatusPill({ status }: { status: string }) {
  const s = DECISION_STYLES[status] ?? DECISION_STYLES.UNKNOWN;
  return (
    <div className={cn("flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border whitespace-nowrap", s.color, s.border, s.bg)}>
      <span>{status}</span>
    </div>
  );
}

export default function VerificationPage() {
  const [selectedReq, setSelectedReq] = useState<RequirementVerification | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["verification"],
    queryFn: () =>
      apiFetch<VerificationList>("/v1/verification/?workspace_id=default&analysis_id=default").catch(() => ({
        requirement_verifications: [],
        obligation_verifications: [],
      })),
    retry: false,
  });

  const reqs = data?.requirement_verifications ?? [];
  const obls = data?.obligation_verifications ?? [];

  return (
    <Shell>
      <div className="flex gap-0 h-full -m-6 flex-col md:flex-row">
        {/* Requirements List */}
        <div className={cn(
          "flex flex-col border-r border-[#20242B] bg-[#08090B]",
          selectedReq ? "md:w-[380px] md:min-w-[380px]" : "w-full"
        )}>
          <div className="p-6 border-b border-[#20242B]">
            <h1 className="text-2xl font-sans tracking-tight text-[#F5F7FA]">Verification Workspace</h1>
            <p className="text-[#5F6773] mt-1 font-mono text-xs tracking-wide">Evaluate obligation results.</p>
          </div>

          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-[#0D0F12] rounded animate-pulse border border-[#20242B]" />
              ))}
            </div>
          ) : reqs.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <ShieldCheck className="w-10 h-10 text-[#20242B] mb-6" />
              <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">NO VERIFICATION RESULT</div>
              <p className="text-[#8B93A1] max-w-xs text-sm leading-relaxed mb-4">
                No verification result exists for this obligation.
              </p>
              <div className="font-mono text-xs tracking-widest border border-[#8B5CF6]/30 bg-[#8B5CF6]/10 text-[#8B5CF6] px-3 py-1.5 rounded">
                Current state: UNKNOWN
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-[#20242B]">
              {reqs.map(req => (
                <button
                  key={req.id}
                  onClick={() => setSelectedReq(req)}
                  className={cn(
                    "w-full text-left px-6 py-4 transition-colors hover:bg-[#0D0F12] group flex flex-col gap-2",
                    selectedReq?.id === req.id && "bg-[#12151A]"
                  )}
                >
                  <div className="flex justify-between items-start w-full">
                    <span className="font-mono text-sm text-[#F5F7FA]">{req.requirement_id}</span>
                    <StatusPill status={req.decision} />
                  </div>
                  <p className="text-sm text-[#8B93A1] line-clamp-2 leading-relaxed">{req.explanation}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Investigation Mode */}
        {selectedReq && (
          <div className="flex-1 border-t md:border-t-0 md:border-l border-[#20242B] bg-[#08090B] p-6 flex flex-col min-h-[600px] overflow-y-auto">
            <div className="flex items-center gap-2 mb-6 text-[#F5F7FA] border-b border-[#20242B] pb-4">
              <FileSearch className="w-5 h-5 text-[#8B5CF6]" />
              <h2 className="font-mono tracking-widest uppercase text-sm">Investigation Mode</h2>
            </div>
            
            <div className="space-y-8 flex-1">
              <div>
                <h3 className="text-xl text-[#F5F7FA] font-medium mb-2">{selectedReq.explanation || "No explanation provided"}</h3>
                <div className="font-mono text-sm text-[#5F6773]">Contract: {selectedReq.contract_id}</div>
              </div>

              <div className="relative">
                <div className="absolute left-[15px] top-4 bottom-4 w-px bg-[#20242B]" />
                
                <div className="space-y-6 relative">
                  <TraceNode title="Requirement" id={selectedReq.requirement_id} status={selectedReq.decision} />
                  <TraceNode title="Contract" id={selectedReq.contract_id} status="READY" />
                  
                  {obls.filter(o => o.contract_id === selectedReq.contract_id).map(obl => (
                    <div key={obl.obligation_id} className="ml-8 relative">
                       <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#20242B]" />
                       <TraceNode title="Obligation" id={obl.obligation_id} status={obl.decision} />
                       
                       {obl.supporting_evidence.map(ev => (
                         <div key={ev} className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#20242B]" />
                           <TraceNode title="Evidence" id={ev} status="VERIFIED" />
                         </div>
                       ))}
                       {obl.contradicting_evidence.map(ev => (
                         <div key={ev} className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#20242B]" />
                           <TraceNode title="Evidence" id={ev} status="VIOLATED" isError />
                         </div>
                       ))}
                       
                       {obl.supporting_evidence.length === 0 && obl.contradicting_evidence.length === 0 && (
                         <div className="ml-8 relative mt-4">
                           <div className="absolute -left-[24px] top-4 w-[20px] h-px bg-[#20242B]" />
                           <TraceNode title="Evidence" id="No behavioral evidence available" status="UNAVAILABLE" isEnd />
                         </div>
                       )}
                    </div>
                  ))}
                  
                  <TraceNode title="Verification" id="Assurance complete" status={selectedReq.decision} isEnd />
                </div>
              </div>

              {selectedReq.decision === "UNKNOWN" && (
                <div className="mt-8 border border-[#8B5CF6]/30 bg-[#8B5CF6]/5 rounded-lg p-5">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-[#8B5CF6] shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-mono text-sm tracking-widest text-[#F5F7FA] uppercase mb-2">Why Unknown?</h4>
                      <div className="text-sm text-[#8B93A1] space-y-4 leading-relaxed">
                        <p>Required behavioral evidence is unavailable in the current environment.</p>
                        {selectedReq.limitations && selectedReq.limitations.length > 0 && (
                           <div className="mt-4 space-y-2">
                             <span className="block text-xs font-mono text-[#5F6773] mb-1 uppercase">Limitations:</span>
                             {selectedReq.limitations.map((lim, idx) => (
                               <div key={idx} className="text-[#F5F7FA]">• {lim}</div>
                             ))}
                           </div>
                        )}
                        <p className="font-mono text-xs text-[#8B5CF6] mt-4 uppercase tracking-widest pt-4 border-t border-[#8B5CF6]/20">
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
      <div className={`w-8 h-8 rounded-full border border-[#20242B] flex items-center justify-center shrink-0 z-10 ${isError ? 'bg-[#EF4444]/10 border-[#EF4444]/30' : isUnknown ? 'bg-[#8B5CF6]/10 border-[#8B5CF6]/30' : isEnd ? 'bg-[#10B981]/10 border-[#10B981]/30' : 'bg-[#12151A]'}`}>
        <div className={`w-2 h-2 rounded-full ${isError ? 'bg-[#EF4444]' : isUnknown ? 'bg-[#8B5CF6]' : isEnd ? 'bg-[#10B981]' : 'bg-[#5F6773]'}`} />
      </div>
      <div className="pt-1.5 flex-1 flex justify-between items-start">
        <div>
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">{title}</div>
          <div className="text-sm font-mono text-[#F5F7FA]">{id}</div>
        </div>
        <StatusPill status={status} />
      </div>
    </div>
  );
}
