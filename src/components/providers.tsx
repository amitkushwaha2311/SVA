"use client";

import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { useState, createContext, useContext, useEffect } from "react";
import { apiFetch } from "@/lib/api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: 30_000 },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceProvider>
          <RepositoryProvider>
            {children}
          </RepositoryProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

// ─── Auth Context ─────────────────────────────────────────────────────────────

interface User {
  id: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  /** Call after successful login to re-hydrate session from cookie */
  login: () => Promise<void>;
  /** Clears user state — actual session revocation via POST /api/auth/logout */
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const data = await apiFetch<User>("/auth/me");
      setUser(data);
    } catch {
      // 401 is expected when unauthenticated — not an error to surface
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login: checkAuth, logout: () => setUser(null) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// ─── Workspace Context ────────────────────────────────────────────────────────

export interface Workspace {
  id: string;
  name: string;
  role: string;
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (w: Workspace) => void;
  isLoading: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      setWorkspaces([]);
      setActiveWorkspace(null);
      return;
    }

    setIsLoading(true);
    apiFetch<{ items: Workspace[] }>("/v1/workspaces")
      .then((data) => {
        setWorkspaces(data.items);
        
        // Check if the current activeWorkspace is still valid
        const isActiveValid = activeWorkspace && data.items.some(w => w.id === activeWorkspace.id);

        if (data.items.length > 0) {
          // If none active, or current active is invalid, select the first one
          if (!activeWorkspace || !isActiveValid) {
            setActiveWorkspace(data.items[0]);
          }
        } else {
          setActiveWorkspace(null);
        }
      })
      .catch(() => setWorkspaces([]))
      .finally(() => setIsLoading(false));
  }, [user]);

  return (
    <WorkspaceContext.Provider value={{ workspaces, activeWorkspace, setActiveWorkspace, isLoading }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}

// ─── Repository Context ───────────────────────────────────────────────────────

export interface Repository {
  id: string;
  name: string;
  provider_type: string | null;
  repository_identifier: string;
  created_at: string;
}

export interface Analysis {
  id: string;
  status: string;
  created_at: string;
}

interface RepositoryContextType {
  repositories: Repository[];
  activeRepository: Repository | null;
  setActiveRepository: (r: Repository | null) => void;
  activeAnalysis: Analysis | null;
  isRepoLoading: boolean;
}

const RepositoryContext = createContext<RepositoryContextType | undefined>(undefined);

export function RepositoryProvider({ children }: { children: React.ReactNode }) {
  const { activeWorkspace } = useWorkspace();
  const [activeRepository, setActiveRepository] = useState<Repository | null>(null);
  const { user } = useAuth();
  
  const { data: reposData, isLoading: isRepoLoading } = useQuery({
    queryKey: ["context-repositories", activeWorkspace?.id],
    enabled: !!activeWorkspace?.id && !!user,
    queryFn: () =>
      apiFetch<{ items: Repository[] }>(
        `/v1/orchestration/repositories?workspace_id=${activeWorkspace!.id}`
      ).catch(() => ({ items: [] })),
  });

  const repositories = reposData?.items || [];

  useEffect(() => {
    if (!activeWorkspace) {
      setActiveRepository(null);
      return;
    }
    if (repositories.length > 0) {
      if (!activeRepository || !repositories.find(r => r.id === activeRepository.id)) {
        setActiveRepository(repositories[0]);
      }
    } else {
      setActiveRepository(null);
    }
  }, [repositories, activeWorkspace, activeRepository]);

  const { data: analysesData } = useQuery({
    queryKey: ["context-analyses", activeRepository?.id, activeWorkspace?.id],
    enabled: !!activeWorkspace?.id && !!activeRepository?.id && !!user,
    queryFn: () =>
      apiFetch<{ analyses: Analysis[] }>(
        `/v1/analyses?workspace_id=${activeWorkspace!.id}&repository_id=${activeRepository!.id}`
      ).catch(() => ({ analyses: [] })),
  });

  const completedAnalyses = (analysesData?.analyses || []).filter(a => a.status === "COMPLETED");
  const sortedAnalyses = [...completedAnalyses].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  const activeAnalysis = sortedAnalyses.length > 0 ? sortedAnalyses[0] : null;

  return (
    <RepositoryContext.Provider value={{ repositories, activeRepository, setActiveRepository, activeAnalysis, isRepoLoading }}>
      {children}
    </RepositoryContext.Provider>
  );
}

export function useRepository() {
  const context = useContext(RepositoryContext);
  if (context === undefined) {
    throw new Error("useRepository must be used within a RepositoryProvider");
  }
  return context;
}

