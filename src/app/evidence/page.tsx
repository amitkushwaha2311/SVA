"use client";

import { Shell } from "@/components/layout/Shell";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
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
  UNKNOWN:     { text: "text-[#8B5CF6]", border: "border-[#8B5CF6]/30", bg: "bg-[#8B5CF6]/10", dot: "bg-[#8B5CF6]" },
  INCONCLUSIVE:{ text: "text-[#9333EA]", border: "border-[#9333EA]/30", bg: "bg-[#9333EA]/10", dot: "bg-[#9333EA]" },
  STALE:       { text: "text-[#D97706]", border: "border-[#D97706]/30", bg: "bg-[#D97706]/10", dot: "bg-[#D97706]" },
  VERIFIED:    { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10", dot: "bg-[#10B981]" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  return (
    <div className={cn("flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border whitespace-nowrap", s.text, s.border, s.bg)}>
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
      className="text-[#5F6773] hover:text-[#F5F7FA] transition-colors ml-1"
      title="Copy ID"
    >
      {copied ? <Check className="w-3 h-3 text-[#10B981]" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

export default function EvidencePage() {
  const [selected, setSelected] = useState<EvidenceItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["evidence"],
    queryFn: () =>
      apiFetch<{ items: EvidenceItem[]; total: number }>("/v1/evidence/?workspace_id=default").catch(() => ({ items: [], total: 0 })),
    retry: false,
  });

  const items = data?.items ?? [];

  return (
    <Shell>
      <div className="flex h-full -m-6 gap-0">
        {/* Table Panel */}
        <div className={cn("flex flex-col", selected ? "flex-1 min-w-0" : "w-full")}>
          <div className="px-6 py-5 border-b border-[#20242B] bg-[#08090B]">
            <h1 className="text-2xl font-sans tracking-tight text-[#F5F7FA]">Evidence Explorer</h1>
            <p className="text-[#5F6773] mt-1 font-mono text-xs tracking-wide">
              Forensic observability — {data?.total ?? 0} records
            </p>
          </div>

          {isLoading ? (
            <div className="p-6 space-y-2">
              {[1, 2, 3, 4].map(i => <div key={i} className="h-10 bg-[#0D0F12] rounded animate-pulse border border-[#20242B]" />)}
            </div>
          ) : items.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-16 text-center">
              <Eye className="w-10 h-10 text-[#20242B] mb-6" />
              <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-3">No Behavioral Evidence</div>
              <p className="text-[#8B93A1] max-w-sm text-sm leading-relaxed mb-2">
                No behavioral evidence has been recorded for this obligation.
              </p>
              <p className="text-[#5F6773] text-xs font-mono mb-4">This does not establish violation.</p>
              <div className="font-mono text-xs tracking-widest border border-[#8B5CF6]/30 bg-[#8B5CF6]/10 text-[#8B5CF6] px-3 py-1.5 rounded">
                Current state: UNKNOWN
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              {/* Header */}
              <div className="grid grid-cols-[minmax(160px,1fr)_140px_140px_120px_80px_120px_100px_28px] gap-4 px-6 py-2 border-b border-[#20242B] bg-[#0D0F12]">
                {["Evidence ID", "Requirement", "Contract", "Method", "Commit", "Result", "Status", ""].map(h => (
                  <div key={h} className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773]">{h}</div>
                ))}
              </div>
              {/* Rows */}
              {items.map(ev => (
                <button
                  key={ev.evidence_id}
                  onClick={() => setSelected(ev === selected ? null : ev)}
                  className={cn(
                    "w-full grid grid-cols-[minmax(160px,1fr)_140px_140px_120px_80px_120px_100px_28px] gap-4 px-6 py-3 border-b border-[#20242B] text-left transition-colors hover:bg-[#0D0F12] items-center",
                    selected?.evidence_id === ev.evidence_id && "bg-[#12151A]"
                  )}
                >
                  <div className="font-mono text-xs text-[#F5F7FA] truncate">{ev.evidence_id}</div>
                  <div className="font-mono text-xs text-[#8B93A1] truncate">{ev.requirement_id ?? "—"}</div>
                  <div className="font-mono text-xs text-[#8B93A1] truncate">{ev.contract_id ?? "—"}</div>
                  <div className="font-mono text-xs text-[#8B93A1] truncate">{ev.verification_method}</div>
                  <div className="font-mono text-xs text-[#5F6773] truncate">{ev.commit_id.slice(0, 7)}</div>
                  <div className="font-mono text-xs text-[#F5F7FA]">{ev.result}</div>
                  <StatusPill status={ev.status} />
                  <ChevronRight className="w-4 h-4 text-[#5F6773]" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Evidence Inspector */}
        {selected && (
          <div className="w-[400px] min-w-[400px] border-l border-[#20242B] bg-[#08090B] overflow-y-auto flex flex-col">
            <div className="flex justify-between items-center px-6 py-4 border-b border-[#20242B]">
              <span className="font-mono text-xs uppercase tracking-widest text-[#5F6773]">Evidence Inspector</span>
              <button onClick={() => setSelected(null)} className="text-[#5F6773] hover:text-[#F5F7FA] transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 space-y-6 flex-1">
              <div>
                <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Evidence ID</div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-[#F5F7FA] break-all">{selected.evidence_id}</span>
                  <CopyButton value={selected.evidence_id} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Field label="Status"><StatusPill status={selected.status} /></Field>
                <Field label="Result"><span className="font-mono text-sm text-[#F5F7FA]">{selected.result}</span></Field>
                <Field label="Method"><span className="font-mono text-xs text-[#8B93A1]">{selected.verification_method}</span></Field>
                <Field label="Type"><span className="font-mono text-xs text-[#8B93A1]">{selected.evidence_type}</span></Field>
                <Field label="Commit"><span className="font-mono text-xs text-[#8B93A1]">{selected.commit_id}</span></Field>
                <Field label="Collected"><span className="font-mono text-xs text-[#8B93A1]">{new Date(selected.collected_at).toLocaleString()}</span></Field>
              </div>

              {(selected.requirement_id || selected.contract_id) && (
                <div className="border-t border-[#20242B] pt-4 space-y-3">
                  {selected.requirement_id && <Field label="Requirement"><span className="font-mono text-sm text-[#F5F7FA]">{selected.requirement_id}</span></Field>}
                  {selected.contract_id && <Field label="Contract"><span className="font-mono text-sm text-[#F5F7FA]">{selected.contract_id}</span></Field>}
                </div>
              )}

              <div className="border-t border-[#20242B] pt-4">
                <Field label="Observation">
                  <p className="text-sm text-[#8B93A1] leading-relaxed mt-1">{selected.observation}</p>
                </Field>
              </div>

              {selected.integrity && (
                <div className="border-t border-[#20242B] pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="w-4 h-4 text-[#10B981]" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773]">Integrity</span>
                  </div>
                  <div className="space-y-2">
                    <Field label="Algorithm"><span className="font-mono text-xs text-[#8B93A1]">{selected.integrity.hash_algorithm}</span></Field>
                    <Field label="Hash">
                      <div className="flex items-center gap-1 mt-1">
                        <span className="font-mono text-xs text-[#5F6773] break-all">{selected.integrity.evidence_hash}</span>
                        <CopyButton value={selected.integrity.evidence_hash} />
                      </div>
                    </Field>
                    {selected.integrity.parent_evidence_ids.length > 0 && (
                      <Field label="Parent Evidence">
                        <div className="space-y-1 mt-1">
                          {selected.integrity.parent_evidence_ids.map(pid => (
                            <div key={pid} className="font-mono text-xs text-[#5F6773]">{pid}</div>
                          ))}
                        </div>
                      </Field>
                    )}
                  </div>
                </div>
              )}

              {selected.environment && (
                <div className="border-t border-[#20242B] pt-4">
                  <div className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773] mb-3">Environment</div>
                  <div className="grid grid-cols-2 gap-3">
                    {selected.environment.tool_name && <Field label="Tool"><span className="font-mono text-xs text-[#8B93A1]">{selected.environment.tool_name} {selected.environment.tool_version}</span></Field>}
                    {selected.environment.os_name && <Field label="OS"><span className="font-mono text-xs text-[#8B93A1]">{selected.environment.os_name}</span></Field>}
                  </div>
                </div>
              )}

              {selected.status === "STALE" && (
                <div className="border border-[#D97706]/30 bg-[#D97706]/5 rounded p-4 flex gap-3">
                  <AlertTriangle className="w-4 h-4 text-[#D97706] mt-0.5 shrink-0" />
                  <div className="text-sm text-[#8B93A1] leading-relaxed">
                    <span className="text-[#D97706] font-mono text-xs uppercase tracking-widest block mb-1">Stale Evidence</span>
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
      <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-0.5">{label}</div>
      {children}
    </div>
  );
}
