"use client";

import { Shell } from "@/components/layout/Shell";
import { ShieldCheck, ShieldAlert, Lock, Terminal, Globe, Key, FileCode } from "lucide-react";

export default function SecurityCenter() {
  return (
    <Shell>
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-sans tracking-tight text-[#F5F7FA] flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-[#10B981]" />
            Security Center
          </h1>
          <p className="text-[#8B93A1] mt-2 font-mono text-sm tracking-wide">
            Enterprise boundary controls and environment guarantees.
          </p>
        </header>

        <div className="bg-[#08090B] border border-[#20242B] rounded-lg p-8">
          <div className="grid grid-cols-2 gap-x-12 gap-y-8">
            <SecurityControl 
              title="Repository"
              status="UNTRUSTED"
              description="Repository contents are treated as untrusted data."
              icon={<FileCode />}
              color="amber"
            />
            
            <SecurityControl 
              title="Filesystem"
              status="RESTRICTED"
              description="Read-only access to isolated workspace paths."
              icon={<Lock />}
              color="green"
            />
            
            <SecurityControl 
              title="Network"
              status="DENIED"
              description="Outbound network access is disabled."
              icon={<Globe />}
              color="amber"
            />
            
            <SecurityControl 
              title="Secrets"
              status="DENIED"
              description="No environment secrets injected to execution context."
              icon={<Key />}
              color="amber"
            />
            
            <SecurityControl 
              title="Shell"
              status="DISABLED"
              description="Subprocess and shell execution explicitly disabled."
              icon={<Terminal />}
              color="amber"
            />
            
            <SecurityControl 
              title="Hardened Execution"
              status="UNAVAILABLE"
              description="Phase 9 currently does not provide production execution."
              icon={<ShieldAlert />}
              color="red"
            />
            
            <SecurityControl 
              title="Path Guard"
              status="ACTIVE"
              description="Traversal protection enabled for all file operations."
              icon={<ShieldCheck />}
              color="green"
            />
            
            <SecurityControl 
              title="Audit Logging"
              status="ENABLED"
              description="All boundary transitions are cryptographically logged."
              icon={<FileText />}
              color="green"
            />
          </div>
        </div>
      </div>
    </Shell>
  );
}

function SecurityControl({ title, status, description, icon, color }: any) {
  const colorMap: any = {
    green: { text: "text-[#10B981]", border: "border-[#10B981]/30", bg: "bg-[#10B981]/10", icon: "text-[#10B981]" },
    amber: { text: "text-[#F59E0B]", border: "border-[#F59E0B]/30", bg: "bg-[#F59E0B]/10", icon: "text-[#F59E0B]" },
    red: { text: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10", icon: "text-[#EF4444]" },
  };

  const c = colorMap[color] || colorMap.green;

  return (
    <div className="flex gap-4 items-start border-b border-[#20242B] pb-6 last:border-0 last:pb-0">
      <div className={`w-10 h-10 rounded border ${c.border} ${c.bg} flex items-center justify-center shrink-0`}>
        <div className={`w-5 h-5 ${c.icon}`}>{icon}</div>
      </div>
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h3 className="font-medium text-[#F5F7FA]">{title}</h3>
          <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded border ${c.border} ${c.text}`}>
            {status}
          </span>
        </div>
        <p className="text-sm text-[#8B93A1] leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  );
}

function FileText(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  );
}
