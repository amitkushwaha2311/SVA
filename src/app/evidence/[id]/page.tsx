"use client";

import { use, useEffect } from "react";
import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Eye, Shield, Copy, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// Reusing types and components from main evidence page (simplified for detail view)
const STATUS_STYLES: Record<string, { text: string; border: string; bg: string }> = {
  PROVEN:      { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10" },
  SUPPORTED:   { text: "text-[#06B6D4]", border: "border-[#06B6D4]/30", bg: "bg-[#06B6D4]/10" },
  VIOLATED:    { text: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10" },
  UNKNOWN:     { text: "text-[#8B5CF6]", border: "border-[#8B5CF6]/30", bg: "bg-[#8B5CF6]/10" },
  INCONCLUSIVE:{ text: "text-[#9333EA]", border: "border-[#9333EA]/30", bg: "bg-[#9333EA]/10" },
  STALE:       { text: "text-[#D97706]", border: "border-[#D97706]/30", bg: "bg-[#D97706]/10" },
  VERIFIED:    { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  return (
    <div className={cn("inline-flex items-center gap-1.5 text-[10px] font-mono tracking-widest px-2 py-0.5 rounded border whitespace-nowrap", s.text, s.border, s.bg)}>
      <span>{status}</span>
    </div>
  );
}

export default function EvidenceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["evidence", id],
    queryFn: async () => {
      return apiFetch<any>(`/v1/evidence/${id}?workspace_id=default`);
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
          <h1 className="text-xl font-sans text-[#F5F7FA]">Evidence Not Found</h1>
          <p className="text-sm text-[#8B93A1] mt-2 mb-6 max-w-md">
            The requested behavioral evidence could not be found, or you do not have permission to view it.
          </p>
          <Link href="/evidence" className="text-sm font-medium text-[#08090B] bg-[#F5F7FA] px-4 py-2 rounded hover:bg-white transition-colors">
            Return to Evidence Explorer
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-8">
        <Link href="/evidence" className="text-xs font-mono text-[#5F6773] hover:text-[#F5F7FA] mb-6 inline-block transition-colors">
          ← Back to Explorer
        </Link>
        <div className="border border-[#20242B] bg-[#08090B] rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-[#20242B] flex items-center justify-between bg-[#0D0F12]">
            <div className="flex items-center gap-3">
              <Eye className="w-5 h-5 text-[#8B93A1]" />
              <h1 className="text-lg font-mono text-[#F5F7FA]">{data.evidence_id}</h1>
            </div>
            <StatusPill status={data.status} />
          </div>
          <div className="p-6 space-y-6">
             {/* Detail layout reusing similar logic to inspector... */}
             <div className="grid grid-cols-2 gap-4">
               <div>
                 <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Result</div>
                 <div className="font-mono text-sm text-[#F5F7FA]">{data.result}</div>
               </div>
               <div>
                 <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-1">Method</div>
                 <div className="font-mono text-sm text-[#8B93A1]">{data.verification_method}</div>
               </div>
             </div>
             
             <div className="border-t border-[#20242B] pt-6">
                <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">Observation</div>
                <p className="text-sm text-[#F5F7FA] leading-relaxed">{data.observation}</p>
             </div>
             
             {data.integrity && (
                <div className="border-t border-[#20242B] pt-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="w-4 h-4 text-[#10B981]" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773]">Integrity</span>
                  </div>
                  <div className="font-mono text-xs text-[#8B93A1]">Hash ({data.integrity.hash_algorithm}): {data.integrity.evidence_hash}</div>
                </div>
             )}
          </div>
        </div>
      </div>
    </Shell>
  );
}
