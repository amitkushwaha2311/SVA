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
  { key: "ANALYZING",   label: "Semantic Contract Extraction" },
  { key: "VERIFYING",   label: "Behavioral Verification & Proofs" },
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
  if (status === "active")    return <Loader2 className="w-4 h-4 text-[#F4D9A0] animate-spin" />;
  if (status === "failed")    return <AlertCircle className="w-4 h-4 text-[#EF4444]" />;
  if (status === "cancelled") return <Ban className="w-4 h-4 text-[#847768]" />;
  return <div className="w-4 h-4 rounded-full border border-[#514236]" />;
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
      <div className="flex items-center gap-2 text-sm text-[#EF4444] font-mono bg-[#EF4444]/10 border border-[#EF4444]/30 p-3 rounded-xl">
        <AlertCircle className="w-4 h-4 shrink-0" />
        {error}
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex items-center gap-2.5 text-sm text-[#B5AA9C] font-mono animate-pulse py-4">
        <Loader2 className="w-4 h-4 text-[#F4D9A0] animate-spin" />
        Connecting to analysis pipeline…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-1">
        <div>
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest font-medium">Job Identifier</div>
          <div className="text-xs font-mono text-[#F4D9A0] mt-0.5 truncate font-medium">{analysis.id}</div>
        </div>
        <div className={cn(
          "text-[10px] font-mono px-2.5 py-0.5 rounded-full border font-medium",
          analysis.status === "COMPLETED" && "text-[#10B981] border-[#10B981]/30 bg-[#10B981]/10",
          analysis.status === "FAILED"    && "text-[#EF4444] border-[#EF4444]/30 bg-[#EF4444]/10",
          analysis.status === "CANCELLED" && "text-[#847768] border-[#514236]",
          !["COMPLETED","FAILED","CANCELLED"].includes(analysis.status) && "text-[#F4D9A0] border-[#F4D9A0]/30 bg-[#F4D9A0]/10 animate-pulse"
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
                "flex items-center gap-3 px-3.5 py-2.5 rounded-xl border transition-all",
                s === "completed" && "border-[#10B981]/30 bg-[#10B981]/5",
                s === "active"    && "border-[#F4D9A0]/50 bg-[#F4D9A0]/10 shadow-sm",
                s === "failed"    && "border-[#EF4444]/30 bg-[#EF4444]/5",
                s === "pending"   && "border-[#514236] bg-[#211B16]/50",
                s === "cancelled" && "border-[#514236] bg-transparent opacity-40",
              )}
            >
              <StatusIcon status={s} />
              <span className={cn(
                "text-sm font-medium",
                s === "completed" && "text-[#10B981]",
                s === "active"    && "text-[#F5EFE5]",
                s === "failed"    && "text-[#EF4444]",
                s === "pending"   && "text-[#847768]",
                s === "cancelled" && "text-[#847768]",
              )}>
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {analysis.error_message && (
        <div className="px-4 py-3 rounded-xl border border-[#EF4444]/30 bg-[#EF4444]/10">
          <div className="text-[10px] font-mono text-[#EF4444] uppercase tracking-widest mb-1 font-medium">Pipeline Error</div>
          <div className="text-xs font-mono text-[#EF4444] leading-relaxed">{analysis.error_message}</div>
        </div>
      )}

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="px-3.5 py-2.5 bg-[#2A221B] rounded-xl border border-[#514236]">
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest font-medium">Revision</div>
          <div className="text-xs font-mono text-[#F5EFE5] mt-0.5 truncate font-medium">{analysis.commit_id || "—"}</div>
        </div>
        <div className="px-3.5 py-2.5 bg-[#2A221B] rounded-xl border border-[#514236]">
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest font-medium">Analyzer</div>
          <div className="text-xs font-mono text-[#F4D9A0] mt-0.5 font-medium">{analysis.analyzer_version || "—"}</div>
        </div>
      </div>
    </div>
  );
}
