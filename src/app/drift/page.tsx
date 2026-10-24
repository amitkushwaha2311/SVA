"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { GitCommitHorizontal, AlertTriangle, CheckCircle2, XCircle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface DriftReport {
  drift_id: string;
  repository_id: string;
  base_commit: string;
  target_commit: string;
  changes: any[];
  impacts: any[];
  invalidations: any[];
  summary: any | null;
}

function ciAction(report: DriftReport): "PASS" | "REVIEW" | "BLOCK" {
  if (!report.summary) return "REVIEW";
  const s = report.summary;
  if (s.ci_action) return s.ci_action;
  if (report.invalidations.length > 0) return "REVIEW";
  return "PASS";
}

const CI_STYLES = {
  PASS:   { color: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10", Icon: CheckCircle2 },
  REVIEW: { color: "text-[#F59E0B]", border: "border-[#F59E0B]/30", bg: "bg-[#F59E0B]/10", Icon: AlertTriangle },
  BLOCK:  { color: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10", Icon: XCircle },
};

export default function DriftPage() {
  const { activeWorkspace } = useWorkspace();
  const { activeRepository, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["drift", activeWorkspace?.id, activeRepository?.id],
    enabled: !!activeWorkspace?.id && !!activeRepository?.id,
    queryFn: () =>
      apiFetch<{ items: DriftReport[] }>(`/v1/drift?workspace_id=${activeWorkspace!.id}&repository_id=${activeRepository!.id}`).catch(() => ({ items: [] })),
    retry: false,
  });

  const reports = data?.items ?? [];

  return (
    <Shell>
      <div className="max-w-5xl mx-auto space-y-8">
        <header>
          <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1.5 font-medium">Evolution Tracking</div>
          <h1 className="text-3xl md:text-4xl font-serif tracking-tight text-[#F5EFE5]">Semantic Drift</h1>
          <p className="text-[#B5AA9C] mt-2 font-mono text-xs tracking-wide uppercase">
            Impact analysis across commits. Identifies stale evidence and required reviews.
          </p>
        </header>

        {isRepoLoading || isLoading ? (
          <div className="space-y-4">
            {[1, 2].map(i => <div key={i} className="h-32 bg-[#211B16] rounded-2xl animate-pulse border border-[#514236]" />)}
          </div>
        ) : !activeRepository ? (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-16 flex flex-col items-center text-center shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
              <GitCommitHorizontal className="w-7 h-7 text-[#847768]" />
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">No Repository Selected</div>
            <p className="text-[#B5AA9C] text-sm leading-relaxed max-w-xs">
              Select a repository from the top bar to view drift reports.
            </p>
          </div>
        ) : reports.length === 0 ? (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-16 flex flex-col items-center text-center shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
              <GitCommitHorizontal className="w-7 h-7 text-[#847768]" />
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">No Drift Records</div>
            <p className="text-[#B5AA9C] text-sm leading-relaxed max-w-xs">
              No semantic drift has been computed for this repository. Run drift analysis between two commits to see impact.
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {reports.map(report => {
              const action = ciAction(report);
              const style = CI_STYLES[action];
              const Icon = style.Icon;
              return (
                <div key={report.drift_id} className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-xl">
                  {/* Header */}
                  <div className="px-6 py-4.5 border-b border-[#514236] flex items-center justify-between bg-[#2A221B]/40 flex-wrap gap-4">
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-3 font-mono text-xs md:text-sm">
                        <div className="px-2.5 py-1 bg-[#2A221B] border border-[#514236] rounded-lg text-[#B5AA9C]">
                          {report.base_commit.slice(0, 8)}
                        </div>
                        <ChevronRight className="w-4 h-4 text-[#847768]" />
                        <div className="px-2.5 py-1 bg-[#2A221B] border border-[#514236] rounded-lg text-[#F5EFE5] font-medium">
                          {report.target_commit.slice(0, 8)}
                        </div>
                      </div>
                      <div className="text-xs font-mono text-[#847768] hidden sm:block">{report.drift_id}</div>
                    </div>
                    <div className={cn("flex items-center gap-2 text-[10px] font-mono tracking-widest px-3 py-1 rounded-full border font-medium", style.color, style.border, style.bg)}>
                      <Icon className="w-3.5 h-3.5" />
                      <span>CI: {action}</span>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 divide-x divide-[#514236]">
                    <MetricCell label="File Changes" value={report.changes.length} />
                    <MetricCell label="Semantic Impacts" value={report.impacts.length} />
                    <MetricCell label="Invalidations" value={report.invalidations.length} warn={report.invalidations.length > 0} />
                  </div>

                  {/* Invalidations detail */}
                  {report.invalidations.length > 0 && (
                    <div className="px-6 py-5 border-t border-[#514236] bg-[#17130F]/40">
                      <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-3 font-medium">Invalidated Artifacts</div>
                      <div className="space-y-2.5">
                        {report.invalidations.slice(0, 5).map((inv: any, i: number) => (
                          <div key={i} className="flex justify-between items-start gap-4 bg-[#211B16] border border-[#514236] p-3 rounded-xl">
                            <div className="flex gap-3 items-start min-w-0">
                              <span className="text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border border-[#514236] text-[#F4D9A0] bg-[#2A221B] mt-0.5 whitespace-nowrap">
                                {inv.artifact_type}
                              </span>
                              <div className="min-w-0">
                                <span className="font-mono text-xs text-[#F5EFE5] truncate block">{inv.artifact_id}</span>
                                {inv.reason && (
                                  <p className="text-xs text-[#B5AA9C] mt-1 leading-relaxed font-sans">{inv.reason}</p>
                                )}
                              </div>
                            </div>
                            <span className={cn(
                              "text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border shrink-0 font-medium",
                              inv.status === "STALE" ? "text-[#C084FC] border-[#C084FC]/30 bg-[#C084FC]/10" : "text-[#B5AA9C] border-[#514236] bg-[#2A221B]"
                            )}>
                              {inv.status}
                            </span>
                          </div>
                        ))}
                        {report.invalidations.length > 5 && (
                          <div className="text-xs text-[#847768] font-mono pt-1">
                            +{report.invalidations.length - 5} more invalidations
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {report.summary?.explanation && (
                    <div className="px-6 py-4 border-t border-[#514236] bg-[#2A221B]/30">
                      <p className="text-xs md:text-sm text-[#B5AA9C] leading-relaxed font-serif italic">{report.summary.explanation}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Shell>
  );
}

function MetricCell({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className="px-6 py-5">
      <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1.5 font-medium">{label}</div>
      <div className={cn("text-2xl md:text-3xl font-serif font-medium", warn && value > 0 ? "text-[#C084FC]" : "text-[#F5EFE5]")}>{value}</div>
    </div>
  );
}
