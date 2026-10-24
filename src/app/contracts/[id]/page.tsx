"use client";

import { use, useEffect } from "react";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";
import { Scale, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function ContractDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis } = useRepository();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["contract", id, activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: async () => {
      return apiFetch<any>(`/v1/contracts/${id}?workspace_id=${activeWorkspace!.id}&analysis_id=${activeAnalysis!.id}`);
    },
    retry: false,
  });

  if (isLoading) {
    return (
      <Shell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="w-8 h-8 text-[#F4D9A0] animate-spin" />
        </div>
      </Shell>
    );
  }

  if (error || !data) {
    return (
      <Shell>
        <div className="flex flex-col h-full items-center justify-center text-center p-8">
          <div className="w-16 h-16 rounded-2xl bg-[#EF4444]/10 border border-[#EF4444]/30 flex items-center justify-center mb-6">
            <XCircle className="w-8 h-8 text-[#EF4444]" />
          </div>
          <h1 className="text-2xl font-serif text-[#F5EFE5]">Contract Not Found</h1>
          <p className="text-sm text-[#B5AA9C] mt-2 mb-6 max-w-md">
            The requested contract could not be found, or you do not have permission to view it.
          </p>
          <Link href="/contracts" className="text-sm font-semibold text-[#17130F] bg-[#F4D9A0] px-5 py-2.5 rounded-xl hover:bg-[#fae6bb] transition-all shadow-md shadow-[#F4D9A0]/10">
            Return to Contract Explorer
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-6 md:py-8 space-y-6">
        <Link href="/contracts" className="text-xs font-mono text-[#B5AA9C] hover:text-[#F4D9A0] inline-flex items-center gap-1.5 transition-colors">
          ← Back to Explorer
        </Link>
        <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-2xl">
          <div className="px-6 py-5 border-b border-[#514236] flex items-center justify-between bg-[#2A221B]/40">
            <div className="flex items-center gap-3">
              <Scale className="w-5 h-5 text-[#F4D9A0]" />
              <h1 className="text-lg font-mono text-[#F5EFE5] font-semibold">{data.contract_id}</h1>
            </div>
            <div className="text-[10px] font-mono tracking-widest px-2.5 py-1 rounded-full border border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981] font-medium">
              READY
            </div>
          </div>
          <div className="p-6 md:p-8 space-y-6">
             <div>
                <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">Primary Behavior</div>
                <p className="text-base text-[#F5EFE5] leading-relaxed font-serif italic">"{data.behavior_rules}"</p>
             </div>
             
             {data.invariants && data.invariants.length > 0 && (
                <div className="border-t border-[#514236] pt-6">
                  <div className="text-[10px] font-mono uppercase tracking-widest text-[#847768] mb-3 font-medium">Invariants</div>
                  <ul className="space-y-2">
                    {data.invariants.map((inv: string, i: number) => (
                      <li key={i} className="text-xs md:text-sm text-[#F5EFE5] font-mono bg-[#2A221B] border border-[#514236] px-4 py-2.5 rounded-xl">
                        {inv}
                      </li>
                    ))}
                  </ul>
                </div>
             )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
