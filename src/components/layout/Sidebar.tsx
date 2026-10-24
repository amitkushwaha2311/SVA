"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  Activity, 
  FileText, 
  ShieldCheck, 
  GitCommitHorizontal, 
  Scale, 
  HelpCircle,
  Eye,
  CheckCircle2,
  Box
} from "lucide-react";
import { useState } from "react";

export function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const routes = [
    { name: "Overview", path: "/", icon: <Activity className="w-4 h-4" /> },
    { name: "Intent", path: "/intent", icon: <FileText className="w-4 h-4" /> },
    { name: "Ambiguity", path: "/ambiguity", icon: <HelpCircle className="w-4 h-4" /> },
    { name: "Contracts", path: "/contracts", icon: <Scale className="w-4 h-4" /> },
    { name: "Evidence", path: "/evidence", icon: <Eye className="w-4 h-4" /> },
    { name: "Verification", path: "/verification", icon: <CheckCircle2 className="w-4 h-4" /> },
    { name: "Drift", path: "/drift", icon: <GitCommitHorizontal className="w-4 h-4" /> },
  ];

  const systemRoutes = [
    { name: "Security", path: "/security", icon: <ShieldCheck className="w-4 h-4" /> },
    { name: "Activity", path: "/activity", icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <>
      {/* Mobile Toggle */}
      <button 
        className="md:hidden fixed bottom-4 right-4 z-50 bg-[#F4D9A0] text-[#17130F] p-3 rounded-full shadow-lg border border-[#514236] transition-transform active:scale-95"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle navigation menu"
      >
        <Box className="w-5 h-5 text-[#17130F]" />
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/70 backdrop-blur-xs z-40 transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed md:static inset-y-0 left-0 z-40 w-64 border-r border-[#514236] bg-[#17130F] flex flex-col h-screen font-sans text-sm transition-transform duration-200 ease-in-out shrink-0",
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        {/* Brand Header */}
        <div className="p-5 border-b border-[#514236] flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[#2A221B] border border-[#514236] flex items-center justify-center group-hover:border-[#F4D9A0]/50 transition-colors shadow-inner">
              <Box className="w-4 h-4 text-[#F4D9A0]" />
            </div>
            <div className="flex flex-col">
              <span className="font-serif text-lg tracking-wider font-semibold text-[#F5EFE5] leading-none">SVA</span>
              <span className="text-[10px] font-mono text-[#B5AA9C] tracking-widest uppercase mt-0.5">Assurance</span>
            </div>
          </Link>
          <span className="text-[10px] font-mono text-[#F4D9A0] bg-[#2A221B] border border-[#514236] px-2 py-0.5 rounded-full">
            v2.0
          </span>
        </div>
      
        {/* Navigation Content */}
        <div className="flex-1 overflow-y-auto py-5 px-3 space-y-6">
          <div>
            <div className="px-3 mb-2 text-[10px] font-mono font-medium text-[#847768] tracking-widest uppercase">
              Assurance Control
            </div>
            <nav className="space-y-1">
              {routes.map((route) => {
                const isActive = pathname === route.path;
                return (
                  <Link
                    key={route.path}
                    href={route.path}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150",
                      isActive 
                        ? "bg-[#2A221B] text-[#F5EFE5] border border-[#514236] shadow-sm font-medium" 
                        : "text-[#B5AA9C] hover:text-[#F5EFE5] hover:bg-[#211B16] border border-transparent"
                    )}
                  >
                    <span className={cn(
                      "transition-colors",
                      isActive ? "text-[#F4D9A0]" : "text-[#847768] group-hover:text-[#B5AA9C]"
                    )}>
                      {route.icon}
                    </span>
                    <span>{route.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2 text-[10px] font-mono font-medium text-[#847768] tracking-widest uppercase">
              System Boundary
            </div>
            <nav className="space-y-1">
              {systemRoutes.map((route) => {
                const isActive = pathname === route.path;
                return (
                  <Link
                    key={route.path}
                    href={route.path}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150",
                      isActive 
                        ? "bg-[#2A221B] text-[#F5EFE5] border border-[#514236] shadow-sm font-medium" 
                        : "text-[#B5AA9C] hover:text-[#F5EFE5] hover:bg-[#211B16] border border-transparent"
                    )}
                  >
                    <span className={cn(
                      "transition-colors",
                      isActive ? "text-[#F4D9A0]" : "text-[#847768]"
                    )}>
                      {route.icon}
                    </span>
                    <span>{route.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-[#514236] bg-[#211B16]/50 text-xs text-[#847768] font-mono">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-[#10B981]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
              ONLINE
            </span>
            <span className="text-[11px] text-[#B5AA9C]">Zero-Trust Mode</span>
          </div>
        </div>
      </aside>
    </>
  );
}
