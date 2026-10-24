"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { Eye, X, Shield, AlertTriangle, Copy, Check, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface EvidenceItem {
  evidence_id: string;
  contract_id: string | null;
  requirement_id: string | null;
  repository_id: string;
  commit_id: string;
  evidence_type: string;
  verification_method: string;
  result: string;
  status: string;
  description: string;
  observation: string;
  collected_at: string;
  integrity: { evidence_hash: string; hash_algorithm: string; parent_evidence_ids: string[]; } | null;
  environment: { tool_name: string | null; tool_version: string | null; os_name: string | null; } | null;
}

const STATUS_STYLES: Record<string, { text: string; border: string; bg: string; dot: string }> = {
  PROVEN:      { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10", dot: "bg-[#10B981]" },
  SUPPORTED:   { text: "text-[#06B6D4]", border: "border-[#06B6D4]/30", bg: "bg-[#06B6D4]/10", dot: "bg-[#06B6D4]" },
  VIOLATED:    { text: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10", dot: "bg-[#EF4444]" },
  UNKNOWN:     { text: "text-[#9CA3AF]", border: "border-[#9CA3AF]/30", bg: "bg-[#9CA3AF]/10", dot: "bg-[#9CA3AF]" },
  INCONCLUSIVE:{ text: "text-[#F59E0B]", border: "border-[#F59E0B]/30", bg: "bg-[#F59E0B]/10", dot: "bg-[#F59E0B]" },
  STALE:       { text: "text-[#C084FC]", border: "border-[#C084FC]/30", bg: "bg-[#C084FC]/10", dot: "bg-[#C084FC]" },
  VERIFIED:    { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10", dot: "bg-[#10B981]" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  return (
    <div className={cn("inline-flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border whitespace-nowrap font-medium", s.text, s.border, s.bg)}>
      <div className={cn("w-1.5 h-1.5 rounded-full", s.dot)} aria-hidden />
      <span>{status}</span>
    </div>
  );
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="text-[#847768] hover:text-[#F4D9A0] transition-colors ml-1 p-0.5 rounded"
      title="Copy ID"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-[#10B981]" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

export default function EvidencePage() {
  const [selected, setSelected] = useState<EvidenceItem | null>(null);

  const { activeWorkspace } = useWorkspace();
  const { activeRepository, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["evidence", activeWorkspace?.id, activeRepository?.id],
    enabled: !!activeWorkspace?.id && !!activeRepository?.id,
    queryFn: () =>
      apiFetch<{ items: EvidenceItem[]; total: number }>(`/v1/evidence?workspace_id=${activeWorkspace!.id}&repository_id=${activeRepository!.id}`).catch(() => ({ items: [], total: 0 })),
    retry: false,
  });

  const items = data?.items ?? [];

  return (
    <Shell>
      <div className="flex h-full -m-6 md:-m-8 gap-0">
        {/* Table Panel */}
        <div className={cn("flex flex-col bg-[#17130F]", selected ? "flex-1 min-w-0" : "w-full")}>
          <div className="px-6 md:px-8 py-6 border-b border-[#514236] bg-[#211B16]/40">
            <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1 font-medium">Forensic Observability</div>
            <h1 className="text-2xl md:text-3xl font-serif tracking-tight text-[#F5EFE5]">Evidence Explorer</h1>
            <p className="text-[#B5AA9C] mt-1 font-mono text-xs tracking-wide">
              Cryptographically verified behavioral traces — {data?.total ?? 0} records
            </p>
          </div>

          {isRepoLoading || isLoading ? (
            <div className="p-6 space-y-2">
              {[1, 2, 3, 4].map(i => <div key={i} className="h-12 bg-[#211B16] rounded-xl animate-pulse border border-[#514236]" />)}
            </div>
          ) : !activeRepository ? (
            <div className="flex-1 flex flex-col items-center justify-center p-16 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mb-6">
                <Eye className="w-7 h-7 text-[#847768]" />
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-3 font-medium">No Repository</div>
              <p className="text-[#B5AA9C] max-w-sm text-sm leading-relaxed mb-2">
                No repository is selected.
              </p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-16 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[#211B16] border border-[#514236] flex items-center justify-center mb-6 shadow-md">
                <Eye className="w-7 h-7 text-[#847768]" />
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-3 font-medium">No Behavioral Evidence</div>
              <p className="text-[#B5AA9C] max-w-sm text-sm leading-relaxed mb-2">
                No behavioral evidence has been recorded for this obligation.
              </p>
              <p className="text-[#847768] text-xs font-mono mb-5">This does not establish violation.</p>
              <div className="font-mono text-xs tracking-widest border border-[#9CA3AF]/30 bg-[#9CA3AF]/10 text-[#9CA3AF] px-3.5 py-1.5 rounded-full font-medium">
                Current state: UNKNOWN
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              {/* Header */}
              <div className="grid grid-cols-[minmax(160px,1fr)_140px_140px_120px_80px_120px_100px_28px] gap-4 px-6 py-3 border-b border-[#514236] bg-[#211B16]/70">
                {["Evidence ID", "Requirement", "Contract", "Method", "Commit", "Result", "Status", ""].map(h => (
                  <div key={h} className="text-[10px] font-mono uppercase tracking-widest text-[#847768] font-medium">{h}</div>
                ))}
              </div>
              {/* Rows */}
              {items.map(ev => (
                <button
                  key={ev.evidence_id}
                  onClick={() => setSelected(ev === selected ? null : ev)}
                  className={cn(
                    "w-full grid grid-cols-[minmax(160px,1fr)_140px_140px_120px_80px_120px_100px_28px] gap-4 px-6 py-3.5 border-b border-[#514236] text-left transition-all hover:bg-[#211B16] items-center group",
                    selected?.evidence_id === ev.evidence_id && "bg-[#211B16] border-l-2 border-l-[#F4D9A0]"
                  )}
                >
                  <div className="font-mono text-xs text-[#F5EFE5] truncate font-medium group-hover:text-[#F4D9A0] transition-colors">{ev.evidence_id}</div>
                  <div className="font-mono text-xs text-[#B5AA9C] truncate">{ev.requirement_id ?? "—"}</div>
                  <div className="font-mono text-xs text-[#B5AA9C] truncate">{ev.contract_id ?? "—"}</div>
                  <div className="font-mono text-xs text-[#B5AA9C] truncate">{ev.verification_method}</div>
                  <div className="font-mono text-xs text-[#847768] truncate">{ev.commit_id.slice(0, 7)}</div>
                  <div className="font-mono text-xs text-[#F5EFE5] font-medium">{ev.result}</div>
                  <StatusPill status={ev.status} />
                  <ChevronRight className="w-4 h-4 text-[#847768] opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Evidence Inspector */}
        {selected && (
          <div className="w-[420px] min-w-[420px] border-l border-[#514236] bg-[#17130F] overflow-y-auto flex flex-col shadow-2xl">
            <div className="flex justify-between items-center px-6 py-5 border-b border-[#514236] bg-[#211B16]/50">
              <span className="font-mono text-xs uppercase tracking-widest text-[#F4D9A0] font-medium">Evidence Inspector</span>
              <button onClick={() => setSelected(null)} className="text-[#847768] hover:text-[#F5EFE5] transition-colors p-1 rounded-lg hover:bg-[#211B16]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 space-y-6 flex-1">
              <div>
                <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Evidence ID</div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-[#F5EFE5] break-all font-medium">{selected.evidence_id}</span>
                  <CopyButton value={selected.evidence_id} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Field label="Status"><StatusPill status={selected.status} /></Field>
                <Field label="Result"><span className="font-mono text-sm text-[#F5EFE5] font-medium">{selected.result}</span></Field>
                <Field label="Method"><span className="font-mono text-xs text-[#B5AA9C]">{selected.verification_method}</span></Field>
                <Field label="Type"><span className="font-mono text-xs text-[#B5AA9C]">{selected.evidence_type}</span></Field>
                <Field label="Commit"><span className="font-mono text-xs text-[#B5AA9C] truncate">{selected.commit_id}</span></Field>
                <Field label="Collected"><span className="font-mono text-xs text-[#B5AA9C]">{new Date(selected.collected_at).toLocaleDateString()}</span></Field>
              </div>

              {(selected.requirement_id || selected.contract_id) && (
                <div className="border-t border-[#514236] pt-4 space-y-3">
                  {selected.requirement_id && <Field label="Requirement"><span className="font-mono text-xs text-[#F4D9A0]">{selected.requirement_id}</span></Field>}
                  {selected.contract_id && <Field label="Contract"><span className="font-mono text-xs text-[#F4D9A0]">{selected.contract_id}</span></Field>}
                </div>
              )}

              <div className="border-t border-[#514236] pt-4">
                <Field label="Observation">
                  <p className="text-sm text-[#B5AA9C] leading-relaxed mt-1 bg-[#211B16] border border-[#514236] p-3.5 rounded-xl font-serif italic">{selected.observation}</p>
                </Field>
              </div>

              {selected.integrity && (
                <div className="border-t border-[#514236] pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="w-4 h-4 text-[#10B981]" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#847768] font-medium">Integrity Verification</span>
                  </div>
                  <div className="space-y-2.5 bg-[#211B16] border border-[#514236] p-4 rounded-xl">
                    <Field label="Algorithm"><span className="font-mono text-xs text-[#B5AA9C]">{selected.integrity.hash_algorithm}</span></Field>
                    <Field label="Hash">
                      <div className="flex items-center gap-1 mt-1">
                        <span className="font-mono text-xs text-[#F4D9A0] break-all">{selected.integrity.evidence_hash}</span>
                        <CopyButton value={selected.integrity.evidence_hash} />
                      </div>
                    </Field>
                    {selected.integrity.parent_evidence_ids.length > 0 && (
                      <Field label="Parent Evidence">
                        <div className="space-y-1 mt-1">
                          {selected.integrity.parent_evidence_ids.map(pid => (
                            <div key={pid} className="font-mono text-xs text-[#847768]">{pid}</div>
                          ))}
                        </div>
                      </Field>
                    )}
                  </div>
                </div>
              )}

              {selected.environment && (
                <div className="border-t border-[#514236] pt-4">
                  <div className="text-[10px] font-mono uppercase tracking-widest text-[#847768] mb-3 font-medium">Environment</div>
                  <div className="grid grid-cols-2 gap-3 bg-[#211B16] border border-[#514236] p-3.5 rounded-xl">
                    {selected.environment.tool_name && <Field label="Tool"><span className="font-mono text-xs text-[#B5AA9C]">{selected.environment.tool_name} {selected.environment.tool_version}</span></Field>}
                    {selected.environment.os_name && <Field label="OS"><span className="font-mono text-xs text-[#B5AA9C]">{selected.environment.os_name}</span></Field>}
                  </div>
                </div>
              )}

              {selected.status === "STALE" && (
                <div className="border border-[#C084FC]/30 bg-[#C084FC]/5 rounded-xl p-4 flex gap-3">
                  <AlertTriangle className="w-4 h-4 text-[#C084FC] mt-0.5 shrink-0" />
                  <div className="text-sm text-[#B5AA9C] leading-relaxed">
                    <span className="text-[#C084FC] font-mono text-xs uppercase tracking-widest block mb-1 font-medium">Stale Evidence</span>
                    This evidence was produced against a different repository state. It remains traceable but cannot establish truth for the current commit.
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">{label}</div>
      {children}
    </div>
  );
}
