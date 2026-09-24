"use client";

import { useWorkspace, useAuth } from "@/components/providers";
import { openCommandPalette } from "@/components/ui/CommandPalette";
import { GitBranch, ChevronDown, User as UserIcon, Check, LogOut, Search } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface Repository {
  id: string;
  name: string;
  provider_type: string | null;
  repository_identifier: string;
}

export function TopBar() {
  const { user } = useAuth();
  const { workspaces, activeWorkspace, setActiveWorkspace, isLoading } = useWorkspace();
  const [wsOpen, setWsOpen] = useState(false);
  const [repoOpen, setRepoOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const wsRef = useRef<HTMLDivElement>(null);
  const repoRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const router = useRouter();

  // Fetch repositories for the active workspace — same endpoint as the dashboard
  const { data: reposData } = useQuery({
    queryKey: ["topbar-repositories", activeWorkspace?.id],
    enabled: !!activeWorkspace?.id,
    queryFn: () =>
      apiFetch<{ items: Repository[] }>(
        `/v1/orchestration/repositories?workspace_id=${activeWorkspace!.id}`
      ).catch(() => ({ items: [] })),
    staleTime: 30_000,
  });
  const repos = reposData?.items ?? [];

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
    <div className="h-14 border-b border-[#20242B] bg-[#0D0F12] flex items-center justify-between px-6 font-sans shrink-0">
      <div className="flex items-center gap-4 min-w-0">

        {/* ── Workspace Selector ─────────────────────────────────────── */}
        <div ref={wsRef} className="relative">
          <button
            type="button"
            onClick={() => setWsOpen(o => !o)}
            aria-expanded={wsOpen}
            aria-haspopup="menu"
            aria-label="Select workspace"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors border",
              wsOpen
                ? "bg-[#12151A] border-[#5F6773]"
                : "hover:bg-[#12151A] border-transparent hover:border-[#20242B]"
            )}
            disabled={isLoading}
          >
            <span className="text-sm font-medium text-[#F5F7FA] max-w-[160px] truncate">
              {isLoading ? "Loading..." : activeWorkspace?.name || "Select Workspace"}
            </span>
            <ChevronDown className={cn("w-4 h-4 text-[#5F6773] transition-transform shrink-0", wsOpen && "rotate-180")} />
          </button>

          {wsOpen && (
            <div role="menu" className="absolute top-full left-0 mt-1 w-64 bg-[#0D0F12] border border-[#20242B] rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="px-3 py-2 border-b border-[#20242B]">
                <span className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest">Your Workspaces</span>
              </div>
              {workspaces.length === 0 ? (
                <div className="px-3 py-4 text-sm text-[#5F6773] font-mono text-center">No workspaces found</div>
              ) : (
                <div className="py-1">
                  {workspaces.map(ws => (
                    <button
                      key={ws.id}
                      type="button"
                      role="menuitem"
                      onClick={() => handleSwitchWorkspace(ws)}
                      className={cn(
                        "w-full flex items-center justify-between px-3 py-2.5 text-left text-sm transition-colors hover:bg-[#12151A]",
                        activeWorkspace?.id === ws.id ? "text-[#F5F7FA]" : "text-[#8B93A1]"
                      )}
                    >
                      <div className="flex flex-col gap-0.5 min-w-0">
                        <span className="truncate font-medium">{ws.name}</span>
                        <span className="text-[10px] font-mono text-[#5F6773]">{ws.role}</span>
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

        <div className="h-4 w-px bg-[#20242B] hidden sm:block" />

        {/* ── Repository Selector ────────────────────────────────────── */}
        <div ref={repoRef} className="relative hidden sm:block">
          <button
            type="button"
            onClick={() => setRepoOpen(o => !o)}
            aria-expanded={repoOpen}
            aria-haspopup="menu"
            aria-label="Select repository"
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors border text-sm",
              repoOpen
                ? "bg-[#12151A] border-[#5F6773] text-[#F5F7FA]"
                : "border-transparent text-[#8B93A1] hover:bg-[#12151A] hover:border-[#20242B] hover:text-[#F5F7FA]"
            )}
            disabled={!activeWorkspace}
          >
            <GitBranch className="w-3.5 h-3.5 shrink-0" />
            <span className="font-medium max-w-[140px] truncate">Repository</span>
            <ChevronDown className={cn("w-4 h-4 text-[#5F6773] transition-transform shrink-0", repoOpen && "rotate-180")} />
          </button>

          {repoOpen && (
            <div role="menu" className="absolute top-full left-0 mt-1 w-72 bg-[#0D0F12] border border-[#20242B] rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="px-3 py-2 border-b border-[#20242B]">
                <span className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest">Repositories</span>
              </div>
              {repos.length === 0 ? (
                <div className="px-3 py-4 text-sm text-[#5F6773] font-mono text-center">No repositories in this workspace</div>
              ) : (
                <div className="py-1 max-h-72 overflow-y-auto">
                  {repos.map(repo => (
                    <Link
                      key={repo.id}
                      href={`/repositories/${repo.id}`}
                      role="menuitem"
                      onClick={() => setRepoOpen(false)}
                      className="flex items-center gap-3 px-3 py-2.5 text-sm text-[#8B93A1] hover:bg-[#12151A] hover:text-[#F5F7FA] transition-colors"
                    >
                      <GitBranch className="w-4 h-4 text-[#5F6773] shrink-0" />
                      <div className="flex flex-col gap-0.5 min-w-0">
                        <span className="font-medium truncate text-[#F5F7FA]">{repo.name}</span>
                        <span className="text-[10px] font-mono text-[#5F6773] truncate">{repo.repository_identifier}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-[#20242B] hidden md:block" />

        {/* ── Search Button ──────────────────────────────────────────── */}
        <button
          type="button"
          onClick={openCommandPalette}
          aria-label="Open search (Ctrl+K)"
          className="hidden md:flex items-center gap-2 text-xs font-mono px-3 py-1.5 bg-[#12151A] rounded text-[#8B93A1] border border-[#20242B] hover:border-[#5F6773] hover:text-[#F5F7FA] transition-colors focus:outline-none focus:border-[#5F6773]"
        >
          <Search className="w-3.5 h-3.5 text-[#5F6773]" />
          <span>Search</span>
          <kbd className="ml-1 text-[10px] border border-[#20242B] rounded px-1 py-0.5 text-[#5F6773]">⌘K</kbd>
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
              "flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors border",
              userOpen
                ? "bg-[#12151A] border-[#5F6773]"
                : "hover:bg-[#12151A] border-transparent hover:border-[#20242B]"
            )}
          >
            <UserIcon className="w-4 h-4 text-[#8B93A1]" />
            <span className="text-sm text-[#F5F7FA] max-w-[140px] truncate hidden sm:block">
              {user?.email || "User"}
            </span>
          </button>

          {userOpen && (
            <div role="menu" className="absolute top-full right-0 mt-1 w-56 bg-[#0D0F12] border border-[#20242B] rounded-lg shadow-xl z-50 overflow-hidden">
              <div className="px-3 py-3 border-b border-[#20242B]">
                <div className="text-sm text-[#F5F7FA] font-medium truncate">{user?.email}</div>
                <div className="text-[10px] font-mono text-[#5F6773] mt-0.5 uppercase tracking-widest">{user?.role}</div>
              </div>
              <div className="py-1">
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-[#EF4444] hover:bg-[#12151A] transition-colors"
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
