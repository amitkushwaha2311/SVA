"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
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
  const { data, isLoading } = useQuery({
    queryKey: ["drift"],
    queryFn: () =>
      apiFetch<{ items: DriftReport[] }>("/v1/drift/?workspace_id=default&repository_id=default").catch(() => ({ items: [] })),
    retry: false,
  });

  const reports = data?.items ?? [];

  return (
    <Shell>
      <div className="max-w-5xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA]">Semantic Drift</h1>
          <p className="text-[#8B93A1] mt-2 font-mono text-xs tracking-wide uppercase">
            Impact analysis across commits. Identifies stale evidence and required reviews.
          </p>
        </header>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2].map(i => <div key={i} className="h-32 bg-[#0D0F12] rounded animate-pulse border border-[#20242B]" />)}
          </div>
        ) : reports.length === 0 ? (
          <div className="border border-[#20242B] bg-[#08090B] rounded-lg p-16 flex flex-col items-center text-center">
            <GitCommitHorizontal className="w-10 h-10 text-[#20242B] mb-6" />
            <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">No Drift Records</div>
            <p className="text-[#8B93A1] text-sm leading-relaxed max-w-xs">
              No semantic drift has been computed for this repository. Run drift analysis between two commits to see impact.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map(report => {
              const action = ciAction(report);
              const style = CI_STYLES[action];
              const Icon = style.Icon;
              return (
                <div key={report.drift_id} className="border border-[#20242B] bg-[#08090B] rounded-lg overflow-hidden">
                  {/* Header */}
                  <div className="px-6 py-4 border-b border-[#20242B] flex items-center justify-between bg-[#0D0F12]">
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-3 font-mono text-sm">
                        <div className="px-2 py-1 bg-[#12151A] border border-[#20242B] rounded text-[#8B93A1]">
                          {report.base_commit.slice(0, 8)}
                        </div>
                        <ChevronRight className="w-4 h-4 text-[#5F6773]" />
                        <div className="px-2 py-1 bg-[#12151A] border border-[#20242B] rounded text-[#F5F7FA]">
                          {report.target_commit.slice(0, 8)}
                        </div>
                      </div>
                      <div className="text-xs font-mono text-[#5F6773] hidden sm:block">{report.drift_id}</div>
                    </div>
                    <div className={cn("flex items-center gap-2 text-[10px] font-mono tracking-widest px-3 py-1 rounded border", style.color, style.border, style.bg)}>
                      <Icon className="w-3.5 h-3.5" />
                      <span>CI: {action}</span>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-3 divide-x divide-[#20242B]">
                    <MetricCell label="File Changes" value={report.changes.length} />
                    <MetricCell label="Semantic Impacts" value={report.impacts.length} />
                    <MetricCell label="Invalidations" value={report.invalidations.length} warn={report.invalidations.length > 0} />
                  </div>

                  {/* Invalidations detail */}
                  {report.invalidations.length > 0 && (
                    <div className="px-6 py-4 border-t border-[#20242B]">
                      <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-3">Invalidated Artifacts</div>
                      <div className="space-y-2">
                        {report.invalidations.slice(0, 5).map((inv: any, i: number) => (
                          <div key={i} className="flex justify-between items-start gap-4">
                            <div className="flex gap-3 items-start">
                              <span className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-[#20242B] text-[#5F6773] bg-[#12151A] mt-0.5 whitespace-nowrap">
                                {inv.artifact_type}
                              </span>
                              <div>
                                <span className="font-mono text-xs text-[#F5F7FA]">{inv.artifact_id}</span>
                                {inv.reason && (
                                  <p className="text-xs text-[#8B93A1] mt-1 leading-relaxed">{inv.reason}</p>
                                )}
                              </div>
                            </div>
                            <span className={cn(
                              "text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border shrink-0",
                              inv.status === "STALE" ? "text-[#D97706] border-[#D97706]/30 bg-[#D97706]/10" : "text-[#8B93A1] border-[#20242B] bg-[#12151A]"
                            )}>
                              {inv.status}
                            </span>
                          </div>
                        ))}
                        {report.invalidations.length > 5 && (
                          <div className="text-xs text-[#5F6773] font-mono pt-2">
                            +{report.invalidations.length - 5} more invalidations
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {report.summary?.explanation && (
                    <div className="px-6 py-3 border-t border-[#20242B] bg-[#0D0F12]">
                      <p className="text-xs text-[#5F6773] leading-relaxed">{report.summary.explanation}</p>
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
    <div className="px-6 py-4">
      <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">{label}</div>
      <div className={cn("text-2xl font-sans", warn && value > 0 ? "text-[#D97706]" : "text-[#F5F7FA]")}>{value}</div>
    </div>
  );
}
