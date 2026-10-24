"use client";

import { Shell } from "@/components/layout/Shell";
import { ShieldCheck, ShieldAlert, Lock, Terminal, Globe, Key, FileCode } from "lucide-react";

export default function SecurityCenter() {
  return (
    <Shell>
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <div className="text-[10px] font-mono text-[#10B981] uppercase tracking-widest mb-1.5 font-medium">Boundary Assurance</div>
          <h1 className="text-3xl md:text-4xl font-serif tracking-tight text-[#F5EFE5] flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-[#10B981]" />
            Security Center
          </h1>
          <p className="text-[#B5AA9C] mt-2 font-mono text-xs md:text-sm tracking-wide">
            Enterprise boundary controls and verifiable environment isolation guarantees.
          </p>
        </header>

        <div className="bg-[#211B16] border border-[#514236] rounded-2xl p-8 md:p-10 shadow-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
            <SecurityControl 
              title="Repository"
              status="UNTRUSTED"
              description="Repository contents are treated as untrusted data at all stages."
              icon={<FileCode />}
              color="amber"
            />
            
            <SecurityControl 
              title="Filesystem"
              status="RESTRICTED"
              description="Read-only access strictly confined to isolated workspace paths."
              icon={<Lock />}
              color="green"
            />
            
            <SecurityControl 
              title="Network"
              status="DENIED"
              description="Outbound network access is disabled during semantic verification."
              icon={<Globe />}
              color="amber"
            />
            
            <SecurityControl 
              title="Secrets"
              status="DENIED"
              description="No environment secrets or credentials injected to execution context."
              icon={<Key />}
              color="amber"
            />
            
            <SecurityControl 
              title="Shell"
              status="DISABLED"
              description="Subprocess and shell execution explicitly disabled in sandbox."
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
              description="Traversal protection enabled for all file and directory operations."
              icon={<ShieldCheck />}
              color="green"
            />
            
            <SecurityControl 
              title="Audit Logging"
              status="ENABLED"
              description="All boundary transitions are cryptographically logged and verifiable."
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
    amber: { text: "text-[#F4D9A0]", border: "border-[#514236]", bg: "bg-[#2A221B]", icon: "text-[#F4D9A0]" },
    red: { text: "text-[#EF4444]", border: "border-[#EF4444]/30", bg: "bg-[#EF4444]/10", icon: "text-[#EF4444]" },
  };

  const c = colorMap[color] || colorMap.green;

  return (
    <div className="flex gap-4 items-start border-b border-[#514236] pb-6 last:border-0 last:pb-0">
      <div className={`w-11 h-11 rounded-xl border ${c.border} ${c.bg} flex items-center justify-center shrink-0 shadow-inner`}>
        <div className={`w-5 h-5 ${c.icon}`}>{icon}</div>
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-base text-[#F5EFE5] font-medium">{title}</h3>
          <span className={`text-[10px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded-full border ${c.border} ${c.text} font-medium`}>
            {status}
          </span>
        </div>
        <p className="text-xs md:text-sm text-[#B5AA9C] leading-relaxed font-sans">
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
