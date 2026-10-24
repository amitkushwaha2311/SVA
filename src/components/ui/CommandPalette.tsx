"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Search, FileText, Scale, Eye, ShieldCheck, Activity, CheckCircle2, GitCommitHorizontal, HelpCircle, ChevronRight, GitBranch, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace } from "@/components/providers";

interface Command {
  id: string;
  label: string;
  group: string;
  href?: string;
  icon: React.ReactNode;
  keywords?: string[];
}

const COMMANDS: Command[] = [
  { id: "overview",      label: "Assurance Control",  group: "Navigation", href: "/",            icon: <Activity className="w-4 h-4" />,       keywords: ["dashboard", "home", "overview"] },
  { id: "intent",        label: "Intent Explorer",     group: "Navigation", href: "/intent",       icon: <FileText className="w-4 h-4" />,       keywords: ["intent", "requirements", "human"] },
  { id: "ambiguity",     label: "Ambiguity",           group: "Navigation", href: "/ambiguity",    icon: <HelpCircle className="w-4 h-4" />,     keywords: ["ambiguity", "conflict", "clarify"] },
  { id: "contracts",     label: "Contract Explorer",   group: "Navigation", href: "/contracts",    icon: <Scale className="w-4 h-4" />,          keywords: ["contracts", "obligations", "invariants"] },
  { id: "evidence",      label: "Evidence Explorer",   group: "Navigation", href: "/evidence",     icon: <Eye className="w-4 h-4" />,            keywords: ["evidence", "forensic", "behavioral"] },
  { id: "verification",  label: "Verification",        group: "Navigation", href: "/verification", icon: <CheckCircle2 className="w-4 h-4" />,   keywords: ["verification", "proven", "unknown", "investigation"] },
  { id: "drift",         label: "Semantic Drift",      group: "Navigation", href: "/drift",        icon: <GitCommitHorizontal className="w-4 h-4" />, keywords: ["drift", "stale", "commits", "ci"] },
  { id: "security",      label: "Security Center",     group: "System",     href: "/security",     icon: <ShieldCheck className="w-4 h-4" />,    keywords: ["security", "sandbox", "path guard", "network"] },
  { id: "activity",      label: "Activity",            group: "System",     href: "/activity",     icon: <Activity className="w-4 h-4" />,       keywords: ["activity", "audit", "timeline", "events"] },
];

/**
 * Open the command palette programmatically from any component.
 * Dispatches a custom event that CommandPalette listens to.
 */
export function openCommandPalette() {
  window.dispatchEvent(new CustomEvent("sva:open-search"));
}

export function CommandPalette() {
  const { activeWorkspace } = useWorkspace();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const { data: searchData, isLoading, isError } = useQuery({
    queryKey: ["search", activeWorkspace?.id, query],
    enabled: !!activeWorkspace?.id && query.trim().length > 0,
    queryFn: () =>
      apiFetch<{ results: any[] }>(
        `/v1/search?workspace_id=${activeWorkspace!.id}&q=${encodeURIComponent(query.trim())}`
      ),
    staleTime: 5000,
  });

  // Listen for keyboard shortcut AND our custom open event
  useEffect(() => {
    const handleOpen = () => {
      setOpen(true);
      setQuery("");
      setSelected(0);
    };

    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(o => !o);
        setQuery("");
        setSelected(0);
      }
      if (e.key === "Escape") setOpen(false);
    };

    window.addEventListener("keydown", handler);
    window.addEventListener("sva:open-search", handleOpen as EventListener);
    return () => {
      window.removeEventListener("keydown", handler);
      window.removeEventListener("sva:open-search", handleOpen as EventListener);
    };
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  const filteredCommands = query
    ? COMMANDS.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.keywords?.some(k => k.includes(query.toLowerCase()))
      )
    : COMMANDS;

  const remoteCommands = useMemo(() => {
    if (!searchData?.results) return [];
    return searchData.results.map(r => {
      let icon = <FileText className="w-4 h-4" />;
      if (r.type === 'repository') icon = <GitBranch className="w-4 h-4" />;
      else if (r.type === 'analysis') icon = <Activity className="w-4 h-4" />;
      else if (r.type === 'intent') icon = <FileText className="w-4 h-4" />;
      else if (r.type === 'contract') icon = <Scale className="w-4 h-4" />;
      else if (r.type === 'evidence') icon = <Eye className="w-4 h-4" />;
      
      return {
        id: `remote-${r.id}`,
        label: r.label,
        group: r.type.charAt(0).toUpperCase() + r.type.slice(1) + 's',
        href: r.href,
        icon
      };
    });
  }, [searchData]);

  const allFiltered = [...filteredCommands, ...remoteCommands];
  
  // Update selected index to stay within bounds if results shrink
  useEffect(() => {
    if (selected >= allFiltered.length && allFiltered.length > 0) {
      setSelected(allFiltered.length - 1);
    } else if (allFiltered.length === 0) {
      setSelected(0);
    }
  }, [allFiltered.length, selected]);

  const groups = Array.from(new Set(allFiltered.map(c => c.group)));

  const execute = useCallback((cmd: Command) => {
    if (cmd.href) router.push(cmd.href);
    setOpen(false);
    setQuery("");
  }, [router]);

  const handleKey = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, allFiltered.length - 1)); }
    if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === "Enter") { e.preventDefault(); if (allFiltered[selected]) execute(allFiltered[selected]); }
  }, [allFiltered, selected, execute]);

  let flatIdx = 0;

  return (
    <>
      <AnimatePresence>
        {open && (
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-[18vh] p-4"
            onClick={() => setOpen(false)}
          >
            <motion.div
              key="palette"
              initial={{ opacity: 0, scale: 0.98, y: -6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.98, y: -6 }}
              transition={{ duration: 0.15 }}
              className="w-full max-w-[580px] bg-[#211B16] border border-[#514236] rounded-xl shadow-2xl overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[#514236] bg-[#2A221B]/40">
                <Search className="w-4 h-4 text-[#F4D9A0] shrink-0" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={e => { setQuery(e.target.value); setSelected(0); }}
                  onKeyDown={handleKey}
                  placeholder="Search pages, requirements, evidence, verification..."
                  className="flex-1 bg-transparent text-[#F5EFE5] text-sm outline-none placeholder:text-[#B5AA9C]/60"
                />
                <kbd className="text-[10px] font-mono text-[#B5AA9C] border border-[#514236] bg-[#2A221B] rounded px-1.5 py-0.5 shadow-sm">ESC</kbd>
              </div>

              <div className="max-h-[380px] overflow-y-auto py-2">
                {isLoading ? (
                  <div className="px-4 py-8 text-center flex flex-col items-center justify-center">
                    <Loader2 className="w-5 h-5 text-[#F4D9A0] animate-spin mb-2" />
                    <span className="text-xs text-[#B5AA9C] font-mono">Searching workspace...</span>
                  </div>
                ) : isError ? (
                  <div className="px-4 py-8 text-center flex flex-col items-center justify-center text-[#EF4444]">
                    <AlertCircle className="w-5 h-5 mb-2" />
                    <span className="text-xs font-mono">Failed to search</span>
                  </div>
                ) : allFiltered.length === 0 ? (
                  <div className="px-4 py-8 text-center text-xs text-[#B5AA9C] font-mono">No results found</div>
                ) : groups.map(group => (
                  <div key={group} className="mb-2 last:mb-0">
                    <div className="px-4 py-1.5 text-[10px] font-mono uppercase tracking-widest text-[#B5AA9C]/70">{group}</div>
                    {allFiltered.filter(c => c.group === group).map(cmd => {
                      const idx = flatIdx++;
                      const isSelected = selected === idx;
                      return (
                        <button
                          key={cmd.id}
                          onClick={() => execute(cmd)}
                          onMouseEnter={() => setSelected(idx)}
                          className={cn(
                            "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors text-sm",
                            isSelected 
                              ? "bg-[#2A221B] text-[#F4D9A0]" 
                              : "text-[#B5AA9C] hover:text-[#F5EFE5] hover:bg-[#2A221B]/40"
                          )}
                        >
                          <span className={cn("shrink-0", isSelected ? "text-[#F4D9A0]" : "text-[#B5AA9C]")}>
                            {cmd.icon}
                          </span>
                          <span className="flex-1 truncate">{cmd.label}</span>
                          <ChevronRight className={cn("w-3.5 h-3.5 transition-opacity shrink-0", isSelected ? "opacity-100 text-[#F4D9A0]" : "opacity-0")} />
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>

              <div className="px-4 py-2.5 border-t border-[#514236] flex gap-4 text-[10px] font-mono text-[#B5AA9C] bg-[#17130F]/40">
                <span><kbd className="border border-[#514236] bg-[#2A221B] rounded px-1 text-[9px]">↑↓</kbd> Navigate</span>
                <span><kbd className="border border-[#514236] bg-[#2A221B] rounded px-1 text-[9px]">↵</kbd> Select</span>
                <span><kbd className="border border-[#514236] bg-[#2A221B] rounded px-1 text-[9px]">ESC</kbd> Close</span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
