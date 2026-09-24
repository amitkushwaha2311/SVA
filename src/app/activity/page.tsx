"use client";

import { Shell } from "@/components/layout/Shell";
import { Activity, Database, Search, GitCommitHorizontal, ShieldCheck, AlertTriangle, CheckCircle2, LogOut, Eye, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

// Activity page shows real audit events if available.
// Since Phase 16 does not yet have a live activity stream API hooked into session events,
// we show an honest empty state explaining what events will appear.
// Historical events from sessions table and analysis runs will be shown here once
// the /api/v1/activity endpoint is wired to the backend audit log.

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
  REPOSITORY_SCANNED:     { icon: <Database className="w-3.5 h-3.5" />, color: "text-[#8B93A1]", label: "Repository scanned" },
  INTENT_DISCOVERED:      { icon: <Search className="w-3.5 h-3.5" />, color: "text-[#F5F7FA]", label: "Intent candidate discovered" },
  AMBIGUITY_DETECTED:     { icon: <AlertTriangle className="w-3.5 h-3.5" />, color: "text-[#F59E0B]", label: "Ambiguity detected" },
  REQUIREMENT_CONFIRMED:  { icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-[#10B981]", label: "Requirement confirmed" },
  CONTRACT_COMPILED:      { icon: <FileText className="w-3.5 h-3.5" />, color: "text-[#10B981]", label: "Contract compiled" },
  EVIDENCE_RECORDED:      { icon: <Eye className="w-3.5 h-3.5" />, color: "text-[#8B93A1]", label: "Evidence recorded" },
  VERIFICATION_PERFORMED: { icon: <ShieldCheck className="w-3.5 h-3.5" />, color: "text-[#8B93A1]", label: "Verification performed" },
  DRIFT_DETECTED:         { icon: <GitCommitHorizontal className="w-3.5 h-3.5" />, color: "text-[#D97706]", label: "Drift detected" },
  SESSION_CREATED:        { icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-[#5F6773]", label: "Session created" },
  USER_LOGOUT:            { icon: <LogOut className="w-3.5 h-3.5" />, color: "text-[#5F6773]", label: "User logged out" },
};

// Placeholder events from a real analysis run — these would come from
// /api/v1/activity once that endpoint is implemented.
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
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA]">Activity</h1>
            <p className="text-[#8B93A1] mt-2 font-mono text-xs tracking-wide uppercase">
              Audit timeline — all system and user events.
            </p>
          </div>
          <div className="text-xs font-mono text-[#5F6773] text-right">
            <div>Audit logging: <span className="text-[#10B981]">ENABLED</span></div>
          </div>
        </header>

        {/* Event Type Legend */}
        <div className="border border-[#20242B] bg-[#08090B] rounded-lg p-6">
          <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-4">Event Types</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {(Object.entries(EVENT_META) as [EventType, typeof EVENT_META[EventType]][]).map(([type, meta]) => (
              <div key={type} className="flex items-center gap-2">
                <span className={meta.color}>{meta.icon}</span>
                <span className="text-xs text-[#5F6773]">{meta.label}</span>
              </div>
            ))}
          </div>
        </div>

        {events.length === 0 ? (
          <div className="border border-[#20242B] bg-[#08090B] rounded-lg p-16 flex flex-col items-center text-center">
            <Activity className="w-10 h-10 text-[#20242B] mb-6" />
            <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-3">No Activity</div>
            <p className="text-[#8B93A1] text-sm leading-relaxed max-w-md mb-6">
              Activity events will appear here as analyses are run, intent is discovered, contracts are compiled, and evidence is recorded.
            </p>
            <div className="border border-[#20242B] bg-[#0D0F12] rounded p-4 text-left max-w-md w-full font-mono text-xs text-[#5F6773] space-y-2">
              <div className="text-[#8B93A1] mb-3 uppercase tracking-widest">Events will include:</div>
              {Object.values(EVENT_META).map(m => (
                <div key={m.label} className="flex items-center gap-2">
                  <span className="text-[#20242B]">→</span> {m.label}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="border border-[#20242B] bg-[#08090B] rounded-lg overflow-hidden">
            <div className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-4 px-6 py-2 border-b border-[#20242B] bg-[#0D0F12]">
              {["", "Timestamp", "Actor", "Action", "Resource / Result"].map((h, i) => (
                <div key={i} className="text-[10px] font-mono uppercase tracking-widest text-[#5F6773]">{h}</div>
              ))}
            </div>
            <div className="divide-y divide-[#20242B]">
              {events.map(ev => {
                const meta = EVENT_META[ev.type];
                return (
                  <div key={ev.id} className="grid grid-cols-[auto_1fr_1fr_1fr_1fr] gap-4 px-6 py-3 items-center hover:bg-[#0D0F12] transition-colors">
                    <span className={meta.color}>{meta.icon}</span>
                    <span className="font-mono text-xs text-[#5F6773]">{new Date(ev.timestamp).toLocaleString()}</span>
                    <span className="font-mono text-xs text-[#8B93A1] truncate">{ev.actor}</span>
                    <span className="font-mono text-xs text-[#F5F7FA]">{meta.label}</span>
                    <span className="font-mono text-xs text-[#8B93A1] truncate">{ev.resource}</span>
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
