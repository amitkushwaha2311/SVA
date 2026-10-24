"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { HelpCircle, AlertTriangle, CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

interface Interpretation {
  interpretation_id: string;
  statement: string;
  interpretation_method: string;
  status: string;
  assumptions: string[];
}

interface Question {
  question_id: string;
  question: string;
  status: string;
  options: string[];
  distinguishing_scenario_id: string | null;
}

interface AmbiguityCase {
  ambiguity_id: string;
  statement: string;
  ambiguity_types: string[];
  interpretations: Interpretation[];
  questions: Question[];
}

const INTERP_STATUS_STYLES: Record<string, { icon: React.ReactNode; color: string; bg: string; border: string }> = {
  HUMAN_SELECTED: {
    icon: <CheckCircle2 className="w-4 h-4" />,
    color: "text-[#10B981]", bg: "bg-[#10B981]/10", border: "border-[#10B981]/30"
  },
  REJECTED: {
    icon: <XCircle className="w-4 h-4" />,
    color: "text-[#EF4444]", bg: "bg-[#EF4444]/10", border: "border-[#EF4444]/30"
  },
  PROPOSED: {
    icon: <Clock className="w-4 h-4" />,
    color: "text-[#F4D9A0]", bg: "bg-[#F4D9A0]/10", border: "border-[#F4D9A0]/30"
  },
  INCONCLUSIVE: {
    icon: <AlertTriangle className="w-4 h-4" />,
    color: "text-[#F59E0B]", bg: "bg-[#F59E0B]/10", border: "border-[#F59E0B]/30"
  },
};

export default function AmbiguityPage() {
  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["ambiguity", activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: () =>
      apiFetch<{ items: AmbiguityCase[] }>(`/v1/ambiguity/?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`).catch(() => ({ items: [] })),
    retry: false,
  });

  const cases = data?.items ?? [];

  return (
    <Shell>
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <div className="text-[10px] font-mono text-[#C8792C] uppercase tracking-widest mb-1.5 font-medium">Conflict Resolution</div>
          <h1 className="text-3xl md:text-4xl font-serif tracking-tight text-[#F5EFE5]">Ambiguity</h1>
          <p className="text-[#B5AA9C] mt-2 font-mono text-xs tracking-wide uppercase">
            Detected conflicts in semantic interpretation. Requires human resolution.
          </p>
        </header>

        {isRepoLoading || isLoading ? (
          <div className="space-y-4">
            {[1, 2].map(i => <div key={i} className="h-40 bg-[#211B16] rounded-2xl animate-pulse border border-[#514236]" />)}
          </div>
        ) : !activeAnalysis ? (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-16 flex flex-col items-center text-center shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
              <HelpCircle className="w-7 h-7 text-[#847768]" />
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">No Analysis Found</div>
            <p className="text-[#B5AA9C] text-sm leading-relaxed max-w-xs">
              No analysis has been completed for this repository yet.
            </p>
          </div>
        ) : cases.length === 0 ? (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-16 flex flex-col items-center text-center shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
              <CheckCircle2 className="w-7 h-7 text-[#10B981]" />
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-[#10B981] mb-2 font-medium">No Ambiguity Detected</div>
            <p className="text-[#B5AA9C] text-sm leading-relaxed max-w-sm">
              No ambiguous intent candidates have been identified. All requirements have clear, unambiguous semantic interpretations.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {cases.map(c => (
              <AmbiguityCard key={c.ambiguity_id} case_={c} />
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}

function AmbiguityCard({ case_: c }: { case_: AmbiguityCase }) {
  return (
    <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="px-6 py-5 border-b border-[#514236] flex items-start justify-between gap-4 bg-[#2A221B]/40">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-[#F4D9A0] bg-[#2A221B] px-2 py-0.5 rounded border border-[#514236]">{c.ambiguity_id}</span>
            <div className="flex gap-2">
              {c.ambiguity_types.map(t => (
                <span key={t} className="text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border border-[#C8792C]/40 bg-[#C8792C]/10 text-[#C8792C]">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div className="flex gap-2.5 items-start">
            <AlertTriangle className="w-4 h-4 text-[#C8792C] mt-1 shrink-0" />
            <p className="text-[#F5EFE5] text-base leading-relaxed font-serif italic">"{c.statement}"</p>
          </div>
        </div>
        <div className="text-[10px] font-mono tracking-widest px-2.5 py-1 rounded-full border border-[#C8792C]/40 bg-[#C8792C]/10 text-[#C8792C] shrink-0 font-medium">
          AMBIGUITY DETECTED
        </div>
      </div>

      {/* Interpretations */}
      {c.interpretations.length > 0 && (
        <div className="px-6 py-5 border-b border-[#514236]">
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-4 font-medium">
            Possible Interpretations
          </div>
          <div className="space-y-3">
            {c.interpretations.map((interp, idx) => {
              const style = INTERP_STATUS_STYLES[interp.status] ?? INTERP_STATUS_STYLES.PROPOSED;
              return (
                <div
                  key={interp.interpretation_id}
                  className={cn("flex gap-4 p-4 rounded-xl border transition-all", style.bg, style.border)}
                >
                  <div className={cn("flex items-center gap-2 shrink-0 mt-0.5", style.color)}>
                    {style.icon}
                    <span className="text-[10px] font-mono tracking-widest font-bold">{idx + 1}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-[#F5EFE5] leading-relaxed mb-2">{interp.statement}</p>
                    <div className="flex items-center gap-4">
                      <span className={cn("text-[10px] font-mono tracking-widest font-medium", style.color)}>{interp.status}</span>
                      {interp.interpretation_method && (
                        <span className="text-[10px] font-mono text-[#847768]">via {interp.interpretation_method}</span>
                      )}
                    </div>
                    {interp.assumptions.length > 0 && (
                      <div className="mt-2.5 space-y-1 pt-2 border-t border-[#514236]/40">
                        {interp.assumptions.map((a, ai) => (
                          <div key={ai} className="text-xs font-mono text-[#B5AA9C]">↳ {a}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Clarification Questions */}
      {c.questions.length > 0 && (
        <div className="px-6 py-5">
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-3 font-medium">
            Clarification Required
          </div>
          {c.questions.map(q => (
            <div key={q.question_id} className="space-y-3 bg-[#2A221B]/30 p-4 rounded-xl border border-[#514236]">
              <div className="flex gap-3 items-start">
                <HelpCircle className="w-4 h-4 text-[#F4D9A0] mt-0.5 shrink-0" />
                <p className="text-sm text-[#F5EFE5] leading-relaxed italic">"{q.question}"</p>
              </div>
              {q.distinguishing_scenario_id && (
                <div className="pl-7 text-xs font-mono text-[#847768]">
                  Distinguishing scenario: {q.distinguishing_scenario_id}
                </div>
              )}
              {q.options.length > 0 && (
                <div className="pl-7 space-y-2">
                  {q.options.map((opt, oi) => (
                    <div key={oi} className="text-sm text-[#B5AA9C] flex gap-2 items-start">
                      <span className="text-[#F4D9A0] font-mono text-xs shrink-0 font-medium">{oi + 1}.</span>
                      <span>{opt}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="pl-7 pt-1">
                <div className={cn(
                  "text-[10px] font-mono tracking-widest px-2.5 py-1 rounded-full border inline-block",
                  q.status === "HUMAN_SELECTED" ? "text-[#10B981] border-[#10B981]/30 bg-[#10B981]/10" :
                  "text-[#C8792C] border-[#C8792C]/30 bg-[#C8792C]/10"
                )}>
                  {q.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
