"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
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
  SUPERSEDED: "text-[#5F6773] border-[#5F6773]/30 bg-[#5F6773]/10",
};

export default function ContractsPage() {
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["contracts"],
    queryFn: () => apiFetch<{ items: Contract[] }>("/v1/contracts/?workspace_id=default&analysis_id=default").catch(() => ({ items: [] })),
    retry: false,
  });

  const contracts = data?.items ?? [];

  return (
    <Shell>
      <div className="flex gap-0 h-full -m-6">
        {/* Contract List */}
        <div className={cn(
          "flex flex-col border-r border-[#20242B] bg-[#08090B]",
          selectedContract ? "w-[380px] min-w-[380px]" : "flex-1"
        )}>
          <div className="p-6 border-b border-[#20242B]">
            <h1 className="text-2xl font-sans tracking-tight text-[#F5F7FA]">Contract Explorer</h1>
            <p className="text-[#5F6773] mt-1 font-mono text-xs tracking-wide">Semantic contracts compiled from requirements.</p>
          </div>

          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-20 bg-[#0D0F12] rounded animate-pulse border border-[#20242B]" />
              ))}
            </div>
          ) : contracts.length === 0 ? (
            <EmptyState
              title="No contracts"
              message="No semantic contracts have been compiled for this analysis."
              detail="Run intent discovery and contract compilation to populate this view."
            />
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-[#20242B]">
              {contracts.map(c => (
                <button
                  key={c.contract_id}
                  onClick={() => setSelectedContract(c)}
                  className={cn(
                    "w-full text-left px-6 py-4 transition-colors hover:bg-[#0D0F12] group",
                    selectedContract?.contract_id === c.contract_id && "bg-[#12151A]"
                  )}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm text-[#F5F7FA]">{c.contract_id}</span>
                        <span className="font-mono text-xs text-[#5F6773]">v{c.contract_version}</span>
                      </div>
                      {c.requirement_id && (
                        <div className="text-xs font-mono text-[#5F6773]">REQ → {c.requirement_id}</div>
                      )}
                      <p className="text-sm text-[#8B93A1] line-clamp-2 leading-relaxed">{c.statement}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-4">
                      <span className={cn("text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border", STATUS_STYLES[c.compilation_status] || STATUS_STYLES.DRAFT)}>
                        {c.compilation_status}
                      </span>
                      <ChevronRight className="w-4 h-4 text-[#5F6773] opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Contract Inspector */}
        {selectedContract && (
          <div className="flex-1 overflow-y-auto bg-[#08090B] p-8">
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
    <div className="max-w-2xl space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="font-mono text-lg text-[#F5F7FA]">{contract.contract_id}</span>
            <span className="font-mono text-xs text-[#5F6773] bg-[#12151A] border border-[#20242B] px-2 py-0.5 rounded">
              VERSION {contract.contract_version}
            </span>
            <span className={cn("text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border", STATUS_STYLES[contract.compilation_status] || STATUS_STYLES.DRAFT)}>
              {contract.compilation_status}
            </span>
          </div>
          {contract.requirement_id && (
            <div className="text-xs font-mono text-[#5F6773]">Requirement: {contract.requirement_id}</div>
          )}
        </div>
        <button onClick={onClose} className="text-[#5F6773] hover:text-[#F5F7FA] transition-colors p-1">
          <X className="w-5 h-5" />
        </button>
      </div>

      <InspectorSection title="Statement">
        <p className="text-[#F5F7FA] leading-relaxed text-sm">{contract.statement}</p>
      </InspectorSection>

      {positives.length > 0 && (
        <InspectorSection title="Positive Obligations">
          <div className="space-y-3">
            {positives.map(b => (
              <div key={b.behavior_id} className="flex gap-3 p-3 bg-[#0D0F12] border border-[#10B981]/20 rounded">
                <Check className="w-4 h-4 text-[#10B981] mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-[#F5F7FA] leading-relaxed">{b.description}</p>
                  {b.actor && (
                    <div className="flex gap-4 mt-2">
                      <span className="text-xs font-mono text-[#5F6773]">Actor: <span className="text-[#8B93A1]">{b.actor}</span></span>
                      {b.action && <span className="text-xs font-mono text-[#5F6773]">Action: <span className="text-[#8B93A1]">{b.action}</span></span>}
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
              <div key={b.behavior_id} className="flex gap-3 p-3 bg-[#0D0F12] border border-[#EF4444]/20 rounded">
                <X className="w-4 h-4 text-[#EF4444] mt-0.5 shrink-0" />
                <p className="text-sm text-[#F5F7FA] leading-relaxed">{b.description}</p>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.invariants.length > 0 && (
        <InspectorSection title="Invariants">
          <div className="space-y-2">
            {contract.invariants.map(inv => (
              <div key={inv.invariant_id} className="font-mono text-sm text-[#8B93A1] bg-[#0D0F12] border border-[#20242B] px-3 py-2 rounded">
                {inv.statement}
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.assumptions.length > 0 && (
        <InspectorSection title="Assumptions">
          <div className="space-y-2">
            {contract.assumptions.map(a => (
              <div key={a.assumption_id} className="flex gap-2 items-start text-sm text-[#8B93A1]">
                <AlertTriangle className="w-4 h-4 text-[#F59E0B] mt-0.5 shrink-0" />
                <span>{a.statement}</span>
              </div>
            ))}
          </div>
        </InspectorSection>
      )}

      {contract.targets.length > 0 && (
        <InspectorSection title="Verification Targets">
          <div className="space-y-2">
            {contract.targets.map(t => (
              <div key={t.target_id} className="flex gap-3 items-start">
                <span className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-[#20242B] text-[#5F6773] bg-[#12151A] mt-0.5">
                  {t.category}
                </span>
                <span className="text-sm text-[#8B93A1]">{t.description}</span>
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
    <div>
      <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-3">{title}</div>
      {children}
    </div>
  );
}

function EmptyState({ title, message, detail }: { title: string; message: string; detail: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
      <Scale className="w-10 h-10 text-[#20242B] mb-6" />
      <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">{title}</div>
      <p className="text-[#8B93A1] max-w-xs text-sm leading-relaxed mb-4">{message}</p>
      <p className="text-[#5F6773] text-xs font-mono">{detail}</p>
    </div>
  );
}
