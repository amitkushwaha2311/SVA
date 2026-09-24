"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
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
    color: "text-[#F59E0B]", bg: "bg-[#F59E0B]/10", border: "border-[#F59E0B]/30"
  },
  INCONCLUSIVE: {
    icon: <AlertTriangle className="w-4 h-4" />,
    color: "text-[#9333EA]", bg: "bg-[#9333EA]/10", border: "border-[#9333EA]/30"
  },
};

export default function AmbiguityPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["ambiguity"],
    queryFn: () =>
      apiFetch<{ items: AmbiguityCase[] }>("/v1/ambiguity/?workspace_id=default&analysis_id=default").catch(() => ({ items: [] })),
    retry: false,
  });

  const cases = data?.items ?? [];

  return (
    <Shell>
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA]">Ambiguity</h1>
          <p className="text-[#8B93A1] mt-2 font-mono text-xs tracking-wide uppercase">
            Detected conflicts in semantic interpretation. Requires human resolution.
          </p>
        </header>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2].map(i => <div key={i} className="h-40 bg-[#0D0F12] rounded animate-pulse border border-[#20242B]" />)}
          </div>
        ) : cases.length === 0 ? (
          <div className="border border-[#20242B] bg-[#08090B] rounded-lg p-16 flex flex-col items-center text-center">
            <HelpCircle className="w-10 h-10 text-[#20242B] mb-6" />
            <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">No Ambiguity Detected</div>
            <p className="text-[#8B93A1] text-sm leading-relaxed max-w-xs">
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
    <div className="border border-[#20242B] bg-[#08090B] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#20242B] flex items-start justify-between gap-4 bg-[#0D0F12]">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm text-[#5F6773]">{c.ambiguity_id}</span>
            <div className="flex gap-2">
              {c.ambiguity_types.map(t => (
                <span key={t} className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-[#F59E0B]/30 bg-[#F59E0B]/10 text-[#F59E0B]">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <div className="flex gap-2 items-start">
            <AlertTriangle className="w-4 h-4 text-[#F59E0B] mt-0.5 shrink-0" />
            <p className="text-[#F5F7FA] text-sm leading-relaxed font-medium">"{c.statement}"</p>
          </div>
        </div>
        <div className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-[#F59E0B]/30 bg-[#F59E0B]/10 text-[#F59E0B] shrink-0">
          AMBIGUITY DETECTED
        </div>
      </div>

      {/* Interpretations */}
      {c.interpretations.length > 0 && (
        <div className="px-6 py-4 border-b border-[#20242B]">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-4">
            Possible Interpretations
          </div>
          <div className="space-y-3">
            {c.interpretations.map((interp, idx) => {
              const style = INTERP_STATUS_STYLES[interp.status] ?? INTERP_STATUS_STYLES.PROPOSED;
              return (
                <div
                  key={interp.interpretation_id}
                  className={cn("flex gap-4 p-4 rounded border", style.bg, style.border)}
                >
                  <div className={cn("flex items-center gap-2 shrink-0 mt-0.5", style.color)}>
                    {style.icon}
                    <span className="text-[10px] font-mono tracking-widest">{idx + 1}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-[#F5F7FA] leading-relaxed mb-2">{interp.statement}</p>
                    <div className="flex items-center gap-4">
                      <span className={cn("text-[10px] font-mono tracking-widest", style.color)}>{interp.status}</span>
                      {interp.interpretation_method && (
                        <span className="text-[10px] font-mono text-[#5F6773]">via {interp.interpretation_method}</span>
                      )}
                    </div>
                    {interp.assumptions.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {interp.assumptions.map((a, ai) => (
                          <div key={ai} className="text-xs font-mono text-[#5F6773]">↳ {a}</div>
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
        <div className="px-6 py-4">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-3">
            Clarification Required
          </div>
          {c.questions.map(q => (
            <div key={q.question_id} className="space-y-3">
              <div className="flex gap-3 items-start">
                <HelpCircle className="w-4 h-4 text-[#8B5CF6] mt-0.5 shrink-0" />
                <p className="text-sm text-[#F5F7FA] leading-relaxed italic">"{q.question}"</p>
              </div>
              {q.distinguishing_scenario_id && (
                <div className="pl-7 text-xs font-mono text-[#5F6773]">
                  Distinguishing scenario: {q.distinguishing_scenario_id}
                </div>
              )}
              {q.options.length > 0 && (
                <div className="pl-7 space-y-2">
                  {q.options.map((opt, oi) => (
                    <div key={oi} className="text-sm text-[#8B93A1] flex gap-2 items-start">
                      <span className="text-[#5F6773] font-mono shrink-0">{oi + 1}.</span>
                      <span>{opt}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className={cn(
                "text-[10px] font-mono tracking-widest px-3 py-1.5 rounded border inline-block ml-7",
                q.status === "HUMAN_SELECTED" ? "text-[#10B981] border-[#10B981]/30 bg-[#10B981]/10" :
                "text-[#F59E0B] border-[#F59E0B]/30 bg-[#F59E0B]/10"
              )}>
                {q.status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
