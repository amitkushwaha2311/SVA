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
        className="md:hidden fixed bottom-4 right-4 z-50 bg-[#10B981] text-[#0D0F12] p-3 rounded-full shadow-lg"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Box className="w-5 h-5" />
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed md:static inset-y-0 left-0 z-40 w-64 border-r border-[#20242B] bg-[#08090B] flex flex-col h-screen font-mono text-sm transition-transform duration-200 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        <div className="p-4 border-b border-[#20242B] flex items-center gap-2 font-bold tracking-widest text-[#F5F7FA]">
          <Box className="w-5 h-5 text-[#F5F7FA]" />
          SVA
        </div>
      
      <div className="flex-1 overflow-y-auto py-4">
        <div className="px-4 mb-2 text-xs font-semibold text-[#5F6773] tracking-widest uppercase">
          Control
        </div>
        <nav className="space-y-1 px-2">
          {routes.map((route) => (
            <Link
              key={route.path}
              href={route.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                pathname === route.path 
                  ? "bg-[#12151A] text-[#F5F7FA]" 
                  : "text-[#8B93A1] hover:text-[#F5F7FA] hover:bg-[#0D0F12]"
              )}
            >
              {route.icon}
              <span>{route.name}</span>
            </Link>
          ))}
        </nav>

        <div className="px-4 mt-8 mb-2 text-xs font-semibold text-[#5F6773] tracking-widest uppercase">
          System
        </div>
        <nav className="space-y-1 px-2">
          {systemRoutes.map((route) => (
            <Link
              key={route.path}
              href={route.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                pathname === route.path 
                  ? "bg-[#12151A] text-[#F5F7FA]" 
                  : "text-[#8B93A1] hover:text-[#F5F7FA] hover:bg-[#0D0F12]"
              )}
            >
              {route.icon}
              <span>{route.name}</span>
            </Link>
          ))}
        </nav>
      </div>
      
      <div className="p-4 border-t border-[#20242B] text-xs text-[#5F6773]">
        <div className="flex justify-between">
          <span>v2.0.0</span>
          <span>● ONLINE</span>
        </div>
      </div>
    </div>
    </>
  );
}
