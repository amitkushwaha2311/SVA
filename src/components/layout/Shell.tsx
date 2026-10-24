"use client";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { useAuth } from "@/components/providers";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Box } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#17130F] flex items-center justify-center p-6 text-[#F5EFE5]">
        <div className="animate-pulse space-y-4 flex flex-col items-center">
          <div className="w-12 h-12 bg-[#2A221B] rounded-xl border border-[#514236] flex items-center justify-center">
            <Box className="w-6 h-6 text-[#F4D9A0] opacity-80" />
          </div>
          <div className="w-32 h-3 bg-[#2A221B] rounded-md" />
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#17130F] text-[#F5EFE5]">
      <CommandPalette />
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-[#17130F]">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 relative">
          {children}
        </main>
      </div>
    </div>
  );
}
