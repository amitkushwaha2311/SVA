"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { Scale, ChevronRight, Check, X, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface Contract {
  contract_id: string;
  contract_version: string;
  requirement_id: string | null;
  statement: string;
  compilation_status: string;
  behaviors: Array<{ behavior_id: string; is_allowed: string; description: string; actor: string | null; action: string | null; }>;
  invariants: Array<{ invariant_id: string; statement: string; }>;
  assumptions: Array<{ assumption_id: string; statement: string; }>;
  targets: Array<{ target_id: string; category: string; description: string; }>;
}

const STATUS_STYLES: Record<string, string> = {
  READY: "text-[#10B981] border-[#10B981]/30 bg-[#10B981]/10",
  DRAFT: "text-[#F59E0B] border-[#F59E0B]/30 bg-[#F59E0B]/10",
  BLOCKED: "text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10",
  SUPERSEDED: "text-[#847768] border-[#514236] bg-[#211B16]",
};

export default function ContractsPage() {
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);

  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["contracts", activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: () => apiFetch<{ items: Contract[] }>(`/v1/contracts?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`).catch(() => ({ items: [] })),
    retry: false,
  });

  const contracts = data?.items ?? [];

  return (
    <Shell>
      <div className="flex gap-0 h-full -m-6 md:-m-8">
        {/* Contract List */}
        <div className={cn(
          "flex flex-col border-r border-[#514236] bg-[#17130F]",
          selectedContract ? "w-[400px] min-w-[400px]" : "flex-1"
        )}>
          <div className="p-6 md:p-8 border-b border-[#514236] bg-[#211B16]/30">
            <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1.5 font-medium">Formal Semantics</div>
            <h1 className="text-2xl md:text-3xl font-serif tracking-tight text-[#F5EFE5]">Contract Explorer</h1>
            <p className="text-[#B5AA9C] mt-1 font-mono text-xs tracking-wide">Semantic contracts compiled from requirements.</p>
          </div>

          {isRepoLoading || isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-[#211B16] rounded-xl animate-pulse border border-[#514236]" />
              ))}
            </div>
          ) : !activeAnalysis ? (
            <EmptyState
              title="No Analysis"
              message="No analysis has been completed for this repository yet."
              detail=""
            />
          ) : contracts.length === 0 ? (
            <EmptyState
              title="No contracts"
              message="No semantic contracts have been compiled for this analysis."
              detail="Run intent discovery and contract compilation to populate this view."
            />
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-[#514236]">
              {contracts.map(c => (
                <button
                  key={c.contract_id}
                  onClick={() => setSelectedContract(c)}
                  className={cn(
                    "w-full text-left px-6 py-4.5 transition-all hover:bg-[#211B16] group relative",
                    selectedContract?.contract_id === c.contract_id && "bg-[#211B16] border-l-2 border-l-[#F4D9A0]"
                  )}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-1.5 pr-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-sm text-[#F5EFE5] font-medium">{c.contract_id}</span>
                        <span className="font-mono text-[10px] text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-1.5 py-0.2 rounded">v{c.contract_version}</span>
                      </div>
                      {c.requirement_id && (
                        <div className="text-xs font-mono text-[#847768]">REQ → {c.requirement_id}</div>
                      )}
                      <p className="text-xs md:text-sm text-[#B5AA9C] line-clamp-2 leading-relaxed">{c.statement}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-3 mt-1">
                      <span className={cn("text-[10px] font-mono tracking-widest px-2 py-0.5 rounded-full border", STATUS_STYLES[c.compilation_status] || STATUS_STYLES.DRAFT)}>
                        {c.compilation_status}
                      </span>
                      <ChevronRight className="w-4 h-4 text-[#847768] opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Contract Inspector */}
        {selectedContract && (
          <div className="flex-1 overflow-y-auto bg-[#17130F] p-8 md:p-10">
            <ContractInspector contract={selectedContract} onClose={() => setSelectedContract(null)} />
          </div>
        )}
      </div>
    </Shell>
  );
}

function ContractInspector({ contract, onClose }: { contract: Contract; onClose: () => void }) {
  const positives = contract.behaviors.filter(b => b.is_allowed === "allowed");
  const negatives = contract.behaviors.filter(b => b.is_allowed === "forbidden");

  return (
    <div className="max-w-3xl space-y-8">
      <div className="flex justify-between items-start border-b border-[#514236] pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <span className="font-mono text-xl text-[#F5EFE5] font-semibold">{contract.contract_id}</span>
            <span className="font-mono text-xs text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2.5 py-0.5 rounded-full">
              VERSION {contract.contract_version}
            </span>
            <span className={cn("text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border", STATUS_STYLES[contract.compilation_status] || STATUS_STYLES.DRAFT)}>
              {contract.compilation_status}
            </span>
          </div>
          {contract.requirement_id && (
            <div className="text-xs font-mono text-[#847768]">Requirement ID: <span className="text-[#B5AA9C]">{contract.requirement_id}</span></div>
          )}
        </div>
        <button onClick={onClose} className="text-[#847768] hover:text-[#F5EFE5] transition-colors p-1.5 rounded-lg hover:bg-[#211B16] border border-transparent hover:border-[#514236]">
          <X className="w-5 h-5" />
        </button>
      </div>

      <InspectorSection title="Statement">
        <div className="bg-[#211B16] border border-[#514236] rounded-xl p-5 shadow-sm">
          <p className="text-[#F5EFE5] leading-relaxed text-sm md:text-base font-serif italic">"{contract.statement}"</p>
        </div>
      </InspectorSection>

      {positives.length > 0 && (
        <InspectorSection title="Positive Obligations">
          <div className="space-y-3">
            {positives.map(b => (
              <div key={b.behavior_id} className="flex gap-3.5 p-4 bg-[#211B16] border border-[#10B981]/30 rounded-xl shadow-sm">
                <Check className="w-4 h-4 text-[#10B981] mt-0.5 shrink-0" />
                <div className="space-y-2">
                  <p className="text-sm text-[#F5EFE5] leading-relaxed">{b.description}</p>
                  {b.actor && (
                    <div className="flex gap-4 pt-1">
                      <span className="text-xs font-mono text-[#847768]">Actor: <span className="text-[#F4D9A0]">{b.actor}</span></span>
                      {b.action && <span className="text-xs font-mono text-[#847768]">Action: <span className="text-[#F4D9A0]">{b.action}</span></span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {negatives.length > 0 && (
        <InspectorSection title="Negative Obligations">
          <div className="space-y-3">
            {negatives.map(b => (
              <div key={b.behavior_id} className="flex gap-3.5 p-4 bg-[#211B16] border border-[#EF4444]/30 rounded-xl shadow-sm">
                <X className="w-4 h-4 text-[#EF4444] mt-0.5 shrink-0" />
                <p className="text-sm text-[#F5EFE5] leading-relaxed">{b.description}</p>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.invariants.length > 0 && (
        <InspectorSection title="Invariants">
          <div className="space-y-2.5">
            {contract.invariants.map(inv => (
              <div key={inv.invariant_id} className="font-mono text-xs md:text-sm text-[#F5EFE5] bg-[#211B16] border border-[#514236] px-4 py-3 rounded-xl">
                {inv.statement}
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.assumptions.length > 0 && (
        <InspectorSection title="Assumptions">
          <div className="space-y-2.5">
            {contract.assumptions.map(a => (
              <div key={a.assumption_id} className="flex gap-3 items-start text-sm text-[#B5AA9C] bg-[#211B16] border border-[#514236] p-4 rounded-xl">
                <AlertTriangle className="w-4 h-4 text-[#C8792C] mt-0.5 shrink-0" />
                <span>{a.statement}</span>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.targets.length > 0 && (
        <InspectorSection title="Verification Targets">
          <div className="space-y-2.5">
            {contract.targets.map(t => (
              <div key={t.target_id} className="flex gap-3 items-center bg-[#211B16] border border-[#514236] px-4 py-3 rounded-xl">
                <span className="text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border border-[#514236] text-[#F4D9A0] bg-[#2A221B]">
                  {t.category}
                </span>
                <span className="text-sm text-[#B5AA9C]">{t.description}</span>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}
    </div>
  );
}

function InspectorSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest font-medium">{title}</div>
      {children}
    </div>
  );
}

function EmptyState({ title, message, detail }: { title: string; message: string; detail: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
      <div className="w-14 h-14 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mb-6">
        <Scale className="w-7 h-7 text-[#847768]" />
      </div>
      <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">{title}</div>
      <p className="text-[#B5AA9C] max-w-xs text-sm leading-relaxed mb-4">{message}</p>
      {detail && <p className="text-[#847768] text-xs font-mono">{detail}</p>}
    </div>
  );
}
