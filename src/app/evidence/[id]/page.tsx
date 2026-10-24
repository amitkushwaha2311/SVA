"use client";

import { use, useEffect } from "react";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace } from "@/components/providers";
import { Eye, Shield, Copy, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, { text: string; border: string; bg: string }> = {
  PROVEN:      { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10" },
  SUPPORTED:   { text: "text-[#06B6D4]", border: "border-[#06B6D4]/30", bg: "bg-[#06B6D4]/10" },
  VIOLATED:    { text: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10" },
  UNKNOWN:     { text: "text-[#9CA3AF]", border: "border-[#9CA3AF]/30", bg: "bg-[#9CA3AF]/10" },
  INCONCLUSIVE:{ text: "text-[#F59E0B]", border: "border-[#F59E0B]/30", bg: "bg-[#F59E0B]/10" },
  STALE:       { text: "text-[#C084FC]", border: "border-[#C084FC]/30", bg: "bg-[#C084FC]/10" },
  VERIFIED:    { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  return (
    <div className={cn("inline-flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2.5 py-0.5 rounded-full border whitespace-nowrap font-medium", s.text, s.border, s.bg)}>
      <span>{status}</span>
    </div>
  );
}

export default function EvidenceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { activeWorkspace } = useWorkspace();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["evidence", id, activeWorkspace?.id],
    enabled: !!activeWorkspace?.id,
    queryFn: async () => {
      return apiFetch<any>(`/v1/evidence/${id}?workspace_id=${activeWorkspace!.id}`);
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
          <h1 className="text-2xl font-serif text-[#F5EFE5]">Evidence Not Found</h1>
          <p className="text-sm text-[#B5AA9C] mt-2 mb-6 max-w-md">
            The requested behavioral evidence could not be found, or you do not have permission to view it.
          </p>
          <Link href="/evidence" className="text-sm font-semibold text-[#17130F] bg-[#F4D9A0] px-5 py-2.5 rounded-xl hover:bg-[#fae6bb] transition-all shadow-md shadow-[#F4D9A0]/10">
            Return to Evidence Explorer
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-6 md:py-8 space-y-6">
        <Link href="/evidence" className="text-xs font-mono text-[#B5AA9C] hover:text-[#F4D9A0] inline-flex items-center gap-1.5 transition-colors">
          ← Back to Explorer
        </Link>
        <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-2xl">
          <div className="px-6 py-5 border-b border-[#514236] flex items-center justify-between bg-[#2A221B]/40">
            <div className="flex items-center gap-3">
              <Eye className="w-5 h-5 text-[#F4D9A0]" />
              <h1 className="text-lg font-mono text-[#F5EFE5] font-semibold">{data.evidence_id}</h1>
            </div>
            <StatusPill status={data.status} />
          </div>
          <div className="p-6 md:p-8 space-y-6">
             <div className="grid grid-cols-2 gap-4">
               <div className="bg-[#2A221B] border border-[#514236] p-4 rounded-xl">
                 <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Result</div>
                 <div className="font-mono text-sm text-[#F5EFE5] font-semibold">{data.result}</div>
               </div>
               <div className="bg-[#2A221B] border border-[#514236] p-4 rounded-xl">
                 <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-1 font-medium">Method</div>
                 <div className="font-mono text-sm text-[#F4D9A0]">{data.verification_method}</div>
               </div>
             </div>
             
             <div className="border-t border-[#514236] pt-6">
                <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">Observation</div>
                <p className="text-sm md:text-base text-[#F5EFE5] leading-relaxed font-serif italic bg-[#2A221B]/50 p-4 rounded-xl border border-[#514236]">
                  "{data.observation}"
                </p>
             </div>
             
             {data.integrity && (
                <div className="border-t border-[#514236] pt-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="w-4 h-4 text-[#10B981]" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#847768] font-medium">Integrity Verification</span>
                  </div>
                  <div className="font-mono text-xs text-[#F4D9A0] bg-[#2A221B] p-3.5 rounded-xl border border-[#514236]">
                    Hash ({data.integrity.hash_algorithm}): {data.integrity.evidence_hash}
                  </div>
                </div>
             )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
