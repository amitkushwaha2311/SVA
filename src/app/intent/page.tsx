"use client";

import { Shell } from "@/components/layout/Shell";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { FileText, MapPin, Search } from "lucide-react";

export default function IntentExplorer() {
  const { data: intents = [], isLoading } = useQuery({
    queryKey: ["intents"],
    queryFn: () => apiFetch<any[]>("/analyses/latest/intent").catch(() => []),
  });

  return (
    <Shell>
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA]">Intent Explorer</h1>
          <p className="text-[#8B93A1] mt-2 font-mono text-sm tracking-wide">Trace original human statements to their semantic interpretation.</p>
        </header>

        <div className="space-y-6">
          {isLoading ? (
            <div className="text-[#5F6773] font-mono text-sm animate-pulse">Loading intent candidates...</div>
          ) : (
            <div className="border border-[#20242B] bg-[#08090B] rounded-lg divide-y divide-[#20242B]">
              <div className="p-6 space-y-6">
                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded bg-[#12151A] border border-[#20242B] flex items-center justify-center shrink-0 mt-1">
                    <FileText className="w-4 h-4 text-[#F5F7FA]" />
                  </div>
                  <div className="space-y-4 flex-1">
                    <div>
                      <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-2">Original Intent</div>
                      <div className="text-xl text-[#F5F7FA] font-medium leading-relaxed">
                        "Only project owners can delete projects."
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-6 pt-4">
                      <div>
                        <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-1"><MapPin className="w-3 h-3" /> Source</div>
                        <div className="text-[#8B93A1] font-mono text-sm">requirements.md:L42</div>
                      </div>
                      <div>
                        <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-1"><Search className="w-3 h-3" /> Provenance</div>
                        <div className="text-[#8B93A1] font-mono text-sm bg-[#12151A] px-2 py-0.5 rounded border border-[#20242B] inline-block">DOCUMENT</div>
                      </div>
                      <div>
                        <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-1">Confirmation</div>
                        <div className="text-[#10B981] font-mono text-sm flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" /> HUMAN_CONFIRMED
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pl-12">
                  <div className="border-l border-[#20242B] pl-6 py-2 space-y-6">
                    <div>
                      <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-3">Semantic Interpretation</div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-[#12151A] border border-[#20242B] rounded p-3">
                          <div className="text-[#5F6773] text-[10px] font-mono uppercase tracking-widest">Actor</div>
                          <div className="text-[#F5F7FA] font-mono text-sm mt-1">User</div>
                        </div>
                        <div className="bg-[#12151A] border border-[#20242B] rounded p-3">
                          <div className="text-[#5F6773] text-[10px] font-mono uppercase tracking-widest">Action</div>
                          <div className="text-[#F5F7FA] font-mono text-sm mt-1">DeleteProject</div>
                        </div>
                        <div className="bg-[#12151A] border border-[#20242B] rounded p-3">
                          <div className="text-[#5F6773] text-[10px] font-mono uppercase tracking-widest">Resource</div>
                          <div className="text-[#F5F7FA] font-mono text-sm mt-1">Project</div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-[#5F6773] font-mono text-xs uppercase tracking-widest mb-2">Assumptions</div>
                      <div className="font-mono text-sm text-[#8B93A1] bg-[#12151A] border border-[#20242B] rounded px-3 py-2 inline-block">
                        owner = project.owner_id
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
