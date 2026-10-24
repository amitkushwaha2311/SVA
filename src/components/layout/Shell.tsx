"use client";

import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { CommandPalette } from "@/components/ui/CommandPalette";

export function Shell({ children }: { children: React.ReactNode }) {
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
