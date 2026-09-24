"use client";

import { use, useEffect } from "react";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Scale, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function ContractDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["contract", id],
    queryFn: async () => {
      return apiFetch<any>(`/v1/contracts/${id}?workspace_id=default`);
    },
    retry: false,
  });

  if (isLoading) {
    return (
      <Shell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="w-8 h-8 text-[#5F6773] animate-spin" />
        </div>
      </Shell>
    );
  }

  if (error || !data) {
    return (
      <Shell>
        <div className="flex flex-col h-full items-center justify-center text-center p-6">
          <XCircle className="w-12 h-12 text-[#EF4444] mb-4" />
          <h1 className="text-xl font-sans text-[#F5F7FA]">Contract Not Found</h1>
          <p className="text-sm text-[#8B93A1] mt-2 mb-6 max-w-md">
            The requested contract could not be found, or you do not have permission to view it.
          </p>
          <Link href="/contracts" className="text-sm font-medium text-[#08090B] bg-[#F5F7FA] px-4 py-2 rounded hover:bg-white transition-colors">
            Return to Contract Explorer
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-8">
        <Link href="/contracts" className="text-xs font-mono text-[#5F6773] hover:text-[#F5F7FA] mb-6 inline-block transition-colors">
          ← Back to Explorer
        </Link>
        <div className="border border-[#20242B] bg-[#08090B] rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-[#20242B] flex items-center justify-between bg-[#0D0F12]">
            <div className="flex items-center gap-3">
              <Scale className="w-5 h-5 text-[#8B93A1]" />
              <h1 className="text-lg font-mono text-[#F5F7FA]">{data.contract_id}</h1>
            </div>
            <div className="text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]">
              READY
            </div>
          </div>
          <div className="p-6 space-y-6">
             <div>
                <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">Primary Behavior</div>
                <p className="text-sm text-[#F5F7FA] leading-relaxed">{data.behavior_rules}</p>
             </div>
             
             {data.invariants.length > 0 && (
                <div className="border-t border-[#20242B] pt-6">
                  <div className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773] mb-3">Invariants</div>
                  <ul className="space-y-2">
                    {data.invariants.map((inv: string, i: number) => (
                      <li key={i} className="text-sm text-[#8B93A1] font-mono bg-[#12151A] border border-[#20242B] px-3 py-2 rounded">
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
