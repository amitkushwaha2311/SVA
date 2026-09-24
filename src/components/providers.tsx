"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
          {children}
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
    // Uses /api/v1/workspaces/ — returns only workspaces the authenticated user is a member of
    apiFetch<{ items: Workspace[] }>("/v1/workspaces/")
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
