"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CheckCircle2, Clock, AlertCircle, Loader2, XCircle, Ban
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

interface AnalysisStatus {
  id: string;
  status: string;
  commit_id: string;
  snapshot_id: string | null;
  analyzer_version: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

const PIPELINE_STAGES = [
  { key: "INGESTING",    label: "Repository Ingestion" },
  { key: "SNAPSHOTTING", label: "Immutable Snapshot" },
  { key: "ANALYZING",   label: "Phase 1–9 Analysis" },
  { key: "VERIFYING",   label: "Verification & Skeptic" },
  { key: "COMPLETED",   label: "Assurance State Persisted" },
] as const;

const LIFECYCLE_ORDER = [
  "CREATED", "QUEUED", "INGESTING", "SNAPSHOTTING", "ANALYZING", "VERIFYING", "COMPLETED"
];

function stageStatus(stageKey: string, currentStatus: string): "completed" | "active" | "pending" | "failed" | "cancelled" {
  if (currentStatus === "FAILED") return stageKey === "INGESTING" ? "failed" : "pending";
  if (currentStatus === "CANCELLED") return "cancelled";

  const currentIdx = LIFECYCLE_ORDER.indexOf(currentStatus);
  const stageIdx = LIFECYCLE_ORDER.indexOf(stageKey);

  if (stageIdx < currentIdx) return "completed";
  if (stageIdx === currentIdx) return "active";
  return "pending";
}

function StatusIcon({ status }: { status: "completed" | "active" | "pending" | "failed" | "cancelled" }) {
  if (status === "completed") return <CheckCircle2 className="w-4 h-4 text-[#10B981]" />;
  if (status === "active")    return <Loader2 className="w-4 h-4 text-[#3B82F6] animate-spin" />;
  if (status === "failed")    return <AlertCircle className="w-4 h-4 text-[#EF4444]" />;
  if (status === "cancelled") return <Ban className="w-4 h-4 text-[#5F6773]" />;
  return <div className="w-4 h-4 rounded-full border border-[#20242B]" />;
}

interface Props {
  analysisId: string;
  onComplete?: (analysis: AnalysisStatus) => void;
}

export function AnalysisProgress({ analysisId, onComplete }: Props) {
  const [analysis, setAnalysis] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const data = await apiFetch<AnalysisStatus>(`/v1/orchestration/analyses/${analysisId}/status`);
      setAnalysis(data);

      const terminal = ["COMPLETED", "FAILED", "CANCELLED"];
      if (terminal.includes(data.status)) {
        onComplete?.(data);
        return false; // stop polling
      }
      return true; // continue
    } catch (e) {
      setError("Unable to fetch analysis status.");
      return false;
    }
  }, [analysisId, onComplete]);

  useEffect(() => {
    let active = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const loop = async () => {
      if (!active) return;
      const shouldContinue = await poll();
      if (shouldContinue && active) {
        timeoutId = setTimeout(loop, 2000);
      }
    };

    loop();
    return () => {
      active = false;
      clearTimeout(timeoutId);
    };
  }, [poll]);

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-[#EF4444] font-mono">
        <AlertCircle className="w-4 h-4 shrink-0" />
        {error}
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex items-center gap-2 text-sm text-[#5F6773] font-mono animate-pulse">
        <Loader2 className="w-4 h-4 animate-spin" />
        Connecting to analysis…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-mono text-[#5F6773] uppercase tracking-widest">Analysis</div>
          <div className="text-sm font-mono text-[#F5F7FA] mt-0.5 truncate">{analysis.id}</div>
        </div>
        <div className={cn(
          "text-[10px] font-mono px-2 py-0.5 rounded border",
          analysis.status === "COMPLETED" && "text-[#10B981] border-[#10B981]/30 bg-[#10B981]/10",
          analysis.status === "FAILED"    && "text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10",
          analysis.status === "CANCELLED" && "text-[#5F6773] border-[#20242B]",
          !["COMPLETED","FAILED","CANCELLED"].includes(analysis.status) && "text-[#3B82F6] border-[#3B82F6]/30 bg-[#3B82F6]/10 animate-pulse"
        )}>
          {analysis.status}
        </div>
      </div>

      {/* Pipeline stages */}
      <div className="space-y-2">
        {PIPELINE_STAGES.map((stage) => {
          const s = stageStatus(stage.key, analysis.status);
          return (
            <div
              key={stage.key}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors",
                s === "completed" && "border-[#10B981]/20 bg-[#10B981]/5",
                s === "active"    && "border-[#3B82F6]/30 bg-[#3B82F6]/5",
                s === "failed"    && "border-[#EF4444]/20 bg-[#EF4444]/5",
                s === "pending"   && "border-[#20242B] bg-transparent",
                s === "cancelled" && "border-[#20242B] bg-transparent opacity-40",
              )}
            >
              <StatusIcon status={s} />
              <span className={cn(
                "text-sm",
                s === "completed" && "text-[#10B981]",
                s === "active"    && "text-[#F5F7FA]",
                s === "failed"    && "text-[#EF4444]",
                s === "pending"   && "text-[#5F6773]",
                s === "cancelled" && "text-[#5F6773]",
              )}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {analysis.error_message && (
        <div className="px-3 py-2.5 rounded-lg border border-[#EF4444]/20 bg-[#EF4444]/5">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Error</div>
          <div className="text-xs font-mono text-[#EF4444]">{analysis.error_message}</div>
        </div>
      )}

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-2">
        <div className="px-3 py-2 bg-[#12151A] rounded border border-[#20242B]">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest">Revision</div>
          <div className="text-xs font-mono text-[#F5F7FA] mt-0.5 truncate">{analysis.commit_id || "—"}</div>
        </div>
        <div className="px-3 py-2 bg-[#12151A] rounded border border-[#20242B]">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest">Analyzer</div>
          <div className="text-xs font-mono text-[#F5F7FA] mt-0.5">{analysis.analyzer_version || "—"}</div>
        </div>
      </div>
    </div>
  );
}
