"use client";

import { Shell } from "@/components/layout/Shell";
import { Activity, Database, Search, GitCommitHorizontal, ShieldCheck, AlertTriangle, CheckCircle2, LogOut, Eye, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

type EventType =
  | "ANALYSIS_STARTED"
  | "REPOSITORY_SCANNED"
  | "INTENT_DISCOVERED"
  | "AMBIGUITY_DETECTED"
  | "REQUIREMENT_CONFIRMED"
  | "CONTRACT_COMPILED"
  | "EVIDENCE_RECORDED"
  | "VERIFICATION_PERFORMED"
  | "DRIFT_DETECTED"
  | "SESSION_CREATED"
  | "USER_LOGOUT";

const EVENT_META: Record<EventType, { icon: React.ReactNode; color: string; label: string }> = {
  ANALYSIS_STARTED:       { icon: <Activity className="w-3.5 h-3.5" />, color: "text-[#06B6D4]", label: "Analysis started" },
  REPOSITORY_SCANNED:     { icon: <Database className="w-3.5 h-3.5" />, color: "text-[#B5AA9C]", label: "Repository scanned" },
  INTENT_DISCOVERED:      { icon: <Search className="w-3.5 h-3.5" />, color: "text-[#F4D9A0]", label: "Intent candidate discovered" },
  AMBIGUITY_DETECTED:     { icon: <AlertTriangle className="w-3.5 h-3.5" />, color: "text-[#F59E0B]", label: "Ambiguity detected" },
  REQUIREMENT_CONFIRMED:  { icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-[#10B981]", label: "Requirement confirmed" },
  CONTRACT_COMPILED:      { icon: <FileText className="w-3.5 h-3.5" />, color: "text-[#10B981]", label: "Contract compiled" },
  EVIDENCE_RECORDED:      { icon: <Eye className="w-3.5 h-3.5" />, color: "text-[#F4D9A0]", label: "Evidence recorded" },
  VERIFICATION_PERFORMED: { icon: <ShieldCheck className="w-3.5 h-3.5" />, color: "text-[#B5AA9C]", label: "Verification performed" },
  DRIFT_DETECTED:         { icon: <GitCommitHorizontal className="w-3.5 h-3.5" />, color: "text-[#C084FC]", label: "Drift detected" },
  SESSION_CREATED:        { icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-[#847768]", label: "Session created" },
  USER_LOGOUT:            { icon: <LogOut className="w-3.5 h-3.5" />, color: "text-[#847768]", label: "User logged out" },
};

const PLACEHOLDER_EVENTS: Array<{
  id: string;
  type: EventType;
  actor: string;
  resource: string;
  result: string;
  timestamp: string;
}> = [];

export default function ActivityPage() {
  const events = PLACEHOLDER_EVENTS;

  return (
    <Shell>
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex flex-col sm:flex-row justify-between sm:items-end gap-4">
          <div>
            <div className="text-[10px] font-mono text-[#F4D9A0] uppercase tracking-widest mb-1.5 font-medium">System Telemetry</div>
            <h1 className="text-3xl md:text-4xl font-serif tracking-tight text-[#F5EFE5]">Activity</h1>
            <p className="text-[#B5AA9C] mt-2 font-mono text-xs tracking-wide uppercase">
              Audit timeline — all verified system and user events.
            </p>
          </div>
          <div className="text-xs font-mono text-[#847768] sm:text-right">
            <div>Audit logging: <span className="text-[#10B981] font-semibold">ENABLED</span></div>
          </div>
        </header>

        {/* Event Type Legend */}
        <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-6 shadow-xl">
          <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-4 font-medium">Event Classifications</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {(Object.entries(EVENT_META) as [EventType, typeof EVENT_META[EventType]][]).map(([type, meta]) => (
              <div key={type} className="flex items-center gap-2">
                <span className={meta.color}>{meta.icon}</span>
                <span className="text-xs text-[#B5AA9C]">{meta.label}</span>
              </div>
            ))}
          </div>
        </div>

        {events.length === 0 ? (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl p-14 flex flex-col items-center text-center shadow-xl">
            <div className="w-14 h-14 rounded-2xl bg-[#2A221B] border border-[#514236] flex items-center justify-center mb-6">
              <Activity className="w-7 h-7 text-[#847768]" />
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-3 font-medium">No Historical Activity</div>
            <p className="text-[#B5AA9C] text-sm leading-relaxed max-w-md mb-6">
              Activity events will appear here as analyses are executed, intent candidates discovered, contracts compiled, and behavioral evidence verified.
            </p>
            <div className="border border-[#514236] bg-[#2A221B] rounded-xl p-5 text-left max-w-md w-full font-mono text-xs text-[#847768] space-y-2.5">
              <div className="text-[#F4D9A0] mb-3 uppercase tracking-widest font-medium">Monitored pipeline transitions:</div>
              {Object.values(EVENT_META).map(m => (
                <div key={m.label} className="flex items-center gap-2">
                  <span className="text-[#514236]">→</span> <span className="text-[#B5AA9C]">{m.label}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="border border-[#514236] bg-[#211B16] rounded-2xl overflow-hidden shadow-xl">
            <div className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-4 px-6 py-3 border-b border-[#514236] bg-[#2A221B]/60">
              {["", "Timestamp", "Actor", "Action", "Resource / Result"].map((h, i) => (
                <div key={i} className="text-[10px] font-mono uppercase tracking-widest text-[#847768] font-medium">{h}</div>
              ))}
            </div>
            <div className="divide-y divide-[#514236]">
              {events.map(ev => {
                const meta = EVENT_META[ev.type];
                return (
                  <div key={ev.id} className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-4 px-6 py-3.5 items-center hover:bg-[#2A221B]/40 transition-colors">
                    <span className={meta.color}>{meta.icon}</span>
                    <span className="font-mono text-xs text-[#847768]">{new Date(ev.timestamp).toLocaleString()}</span>
                    <span className="font-mono text-xs text-[#B5AA9C] truncate">{ev.actor}</span>
                    <span className="font-mono text-xs text-[#F5EFE5] font-medium">{meta.label}</span>
                    <span className="font-mono text-xs text-[#B5AA9C] truncate">{ev.resource}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Shell>
  );
}
