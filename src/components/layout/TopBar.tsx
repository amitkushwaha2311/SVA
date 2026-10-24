"use client";

import { useWorkspace, useAuth, useRepository } from "@/components/providers";
import { openCommandPalette } from "@/components/ui/CommandPalette";
import { GitBranch, ChevronDown, User as UserIcon, Check, LogOut, Search } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { user } = useAuth();
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } = useWorkspace();
  const { repositories: repos, activeRepository, setActiveRepository } = useRepository();
  const [wsOpen, setWsOpen] = useState(false);
  const [repoOpen, setRepoOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const wsRef = useRef<HTMLDivElement>(null);
  const repoRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const router = useRouter();

  // Close all dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wsRef.current && !wsRef.current.contains(e.target as Node)) setWsOpen(false);
      if (repoRef.current && !repoRef.current.contains(e.target as Node)) setRepoOpen(false);
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Escape closes the active dropdown
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setWsOpen(false);
        setRepoOpen(false);
        setUserOpen(false);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const handleSwitchWorkspace = (ws: { id: string; name: string; role: string }) => {
    setActiveWorkspace(ws);
    setWsOpen(false);
    queryClient.invalidateQueries();
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
    } finally {
      router.push("/login");
    }
  };

  return (
    <div className="h-14 border-b border-[#514236] bg-[#211B16] flex items-center justify-between px-6 font-sans shrink-0">
      <div className="flex items-center gap-3 md:gap-4 min-w-0">

        {/* ── Workspace Selector ─────────────────────────────────────── */}
        <div ref={wsRef} className="relative">
          <button
            type="button"
            onClick={() => setWsOpen(o => !o)}
            aria-expanded={wsOpen}
            aria-haspopup="menu"
            aria-label="Select workspace"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all border text-sm font-medium",
              wsOpen
                ? "bg-[#2A221B] border-[#F4D9A0]/60 text-[#F5EFE5] shadow-sm"
                : "bg-[#2A221B]/60 hover:bg-[#2A221B] border-[#514236] hover:border-[#F4D9A0]/40 text-[#F5EFE5]"
            )}
            disabled={isLoading}
          >
            <span className="max-w-[160px] truncate text-[#F5EFE5]">
              {isLoading ? "Loading..." : activeWorkspace?.name || "Select Workspace"}
            </span>
            <ChevronDown className={cn("w-3.5 h-3.5 text-[#B5AA9C] transition-transform shrink-0", wsOpen && "rotate-180")} />
          </button>

          {wsOpen && (
            <div role="menu" className="absolute top-full left-0 mt-1.5 w-64 bg-[#211B16] border border-[#514236] rounded-xl shadow-2xl z-50 overflow-hidden backdrop-blur-md">
              <div className="px-3.5 py-2.5 border-b border-[#514236] bg-[#2A221B]/50">
                <span className="text-[10px] font-mono text-[#847768] uppercase tracking-widest">Your Workspaces</span>
              </div>
              {workspaces.length === 0 ? (
                <div className="px-3 py-4 text-sm text-[#847768] font-mono text-center">No workspaces found</div>
              ) : (
                <div className="py-1">
                  {workspaces.map(ws => (
                    <button
                      key={ws.id}
                      type="button"
                      role="menuitem"
                      onClick={() => handleSwitchWorkspace(ws)}
                      className={cn(
                        "w-full flex items-center justify-between px-3.5 py-2.5 text-left text-sm transition-colors hover:bg-[#2A221B]",
                        activeWorkspace?.id === ws.id ? "text-[#F4D9A0] bg-[#2A221B]/40 font-medium" : "text-[#B5AA9C] hover:text-[#F5EFE5]"
                      )}
                    >
                      <div className="flex flex-col gap-0.5 min-w-0">
                        <span className="truncate">{ws.name}</span>
                        <span className="text-[10px] font-mono text-[#847768] uppercase">{ws.role}</span>
                      </div>
                      {activeWorkspace?.id === ws.id && (
                        <Check className="w-4 h-4 text-[#10B981] shrink-0 ml-2" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-[#514236] hidden sm:block" />

        {/* ── Repository Selector ────────────────────────────────────── */}
        <div ref={repoRef} className="relative hidden sm:block">
          <button
            type="button"
            onClick={() => setRepoOpen(o => !o)}
            aria-expanded={repoOpen}
            aria-haspopup="menu"
            aria-label="Select repository"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all border text-sm font-medium",
              repoOpen
                ? "bg-[#2A221B] border-[#F4D9A0]/60 text-[#F5EFE5]"
                : "bg-[#2A221B]/60 hover:bg-[#2A221B] border-[#514236] text-[#B5AA9C] hover:text-[#F5EFE5] hover:border-[#F4D9A0]/40"
            )}
            disabled={!activeWorkspace}
          >
            <GitBranch className="w-3.5 h-3.5 text-[#F4D9A0] shrink-0" />
            <span className="max-w-[140px] truncate">
              {activeRepository ? activeRepository.name : "Repository"}
            </span>
            <ChevronDown className={cn("w-3.5 h-3.5 text-[#847768] transition-transform shrink-0", repoOpen && "rotate-180")} />
          </button>

          {repoOpen && (
            <div role="menu" className="absolute top-full left-0 mt-1.5 w-72 bg-[#211B16] border border-[#514236] rounded-xl shadow-2xl z-50 overflow-hidden backdrop-blur-md">
              <div className="px-3.5 py-2.5 border-b border-[#514236] bg-[#2A221B]/50">
                <span className="text-[10px] font-mono text-[#847768] uppercase tracking-widest">Repositories</span>
              </div>
              {repos.length === 0 ? (
                <div className="px-3 py-4 text-sm text-[#847768] font-mono text-center">No repositories in this workspace</div>
              ) : (
                <div className="py-1 max-h-72 overflow-y-auto">
                  {repos.map(repo => (
                    <button
                      key={repo.id}
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setActiveRepository(repo);
                        setRepoOpen(false);
                      }}
                      className={cn(
                        "w-full text-left flex items-center gap-3 px-3.5 py-2.5 text-sm transition-colors hover:bg-[#2A221B]",
                        activeRepository?.id === repo.id ? "text-[#F4D9A0] bg-[#2A221B]/40 font-medium" : "text-[#B5AA9C] hover:text-[#F5EFE5]"
                      )}
                    >
                      <GitBranch className="w-4 h-4 text-[#847768] shrink-0" />
                      <div className="flex flex-col gap-0.5 min-w-0">
                        <span className="truncate font-medium">{repo.name}</span>
                        <span className="text-[10px] font-mono text-[#847768] truncate">{repo.repository_identifier}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-[#514236] hidden md:block" />

        {/* ── Search Button ──────────────────────────────────────────── */}
        <button
          type="button"
          onClick={openCommandPalette}
          aria-label="Open search (Ctrl+K)"
          className="hidden md:flex items-center gap-2 text-xs font-mono px-3 py-1.5 bg-[#2A221B] rounded-lg text-[#B5AA9C] border border-[#514236] hover:border-[#F4D9A0]/50 hover:text-[#F5EFE5] transition-all focus:outline-none focus:border-[#F4D9A0]"
        >
          <Search className="w-3.5 h-3.5 text-[#F4D9A0]" />
          <span>Search</span>
          <kbd className="ml-1 text-[10px] border border-[#514236] bg-[#211B16] rounded px-1.5 py-0.5 text-[#B5AA9C]">⌘K</kbd>
        </button>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {/* ── User Menu ──────────────────────────────────────────────── */}
        <div ref={userRef} className="relative">
          <button
            type="button"
            onClick={() => setUserOpen(o => !o)}
            aria-expanded={userOpen}
            aria-haspopup="menu"
            aria-label="User menu"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all border text-sm font-medium",
              userOpen
                ? "bg-[#2A221B] border-[#F4D9A0]/60 text-[#F5EFE5]"
                : "bg-[#2A221B]/60 hover:bg-[#2A221B] border-[#514236] hover:border-[#F4D9A0]/40 text-[#F5EFE5]"
            )}
          >
            <div className="w-5 h-5 rounded-full bg-[#5B4632] flex items-center justify-center text-[#F4D9A0]">
              <UserIcon className="w-3 h-3" />
            </div>
            <span className="text-sm text-[#F5EFE5] max-w-[140px] truncate hidden sm:block">
              {user?.email || "User"}
            </span>
          </button>

          {userOpen && (
            <div role="menu" className="absolute top-full right-0 mt-1.5 w-56 bg-[#211B16] border border-[#514236] rounded-xl shadow-2xl z-50 overflow-hidden backdrop-blur-md">
              <div className="px-4 py-3 border-b border-[#514236] bg-[#2A221B]/40">
                <div className="text-sm text-[#F5EFE5] font-medium truncate">{user?.email}</div>
                <div className="text-[10px] font-mono text-[#F4D9A0] mt-0.5 uppercase tracking-widest">{user?.role}</div>
              </div>
              <div className="py-1">
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-[#EF4444] hover:bg-[#2A221B] transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
