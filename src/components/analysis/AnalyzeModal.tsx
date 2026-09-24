"use client";

import { useState } from "react";
import { X, GitBranch, HardDrive, AlertTriangle, ArrowRight, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { AnalysisProgress } from "./AnalysisProgress";
import { cn } from "@/lib/utils";

interface Props {
  workspaceId: string;
  repositoryId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

type Step = "configure" | "running" | "complete";

interface RegisteredRepo {
  id: string;
  name: string;
}

export function AnalyzeModal({ workspaceId, repositoryId, onClose, onSuccess }: Props) {
  const [step, setStep] = useState<Step>("configure");

  // Form fields
  const [name, setName] = useState("");
  const [provider, setProvider] = useState<"git" | "local">("git");
  const [identifier, setIdentifier] = useState("");
  const [revision, setRevision] = useState("main");

  // State
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      // 1. Register repository if not provided
      let currentRepoId = repositoryId;
      if (!currentRepoId) {
        const repo = await apiFetch<RegisteredRepo>("/v1/orchestration/repositories", {
          method: "POST",
          body: JSON.stringify({
            workspace_id: workspaceId,
            name: name.trim() || identifier.trim().split("/").pop() || "Repository",
            provider,
            identifier: identifier.trim(),
          }),
        });
        currentRepoId = repo.id;
      }

      // 2. Create analysis job (202 Accepted)
      const analysis = await apiFetch<{ id: string }>(`/v1/orchestration/repositories/${currentRepoId}/analyses`, {
        method: "POST",
        body: JSON.stringify({ revision: revision.trim() || "main" }),
      });

      setAnalysisId(analysis.id);
      setStep("running");
    } catch (e: any) {
      setError(e?.message || "Failed to start analysis. Check your repository URL and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAnalysisComplete = (result: { status: string }) => {
    if (result.status === "COMPLETED") {
      setStep("complete");
      setTimeout(onSuccess, 1500);
    }
    // FAILED/CANCELLED are shown in AnalysisProgress
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0D0F12] border border-[#20242B] rounded-xl shadow-2xl w-full max-w-lg">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-[#20242B]">
          <div>
            <h2 className="text-sm font-medium text-[#F5F7FA]">Analyze Repository</h2>
            <p className="text-xs text-[#5F6773] font-mono mt-0.5">
              {step === "configure" && "Register and analyze a repository"}
              {step === "running"   && "Analysis pipeline running…"}
              {step === "complete"  && "Analysis complete"}
            </p>
          </div>
          {step !== "running" && (
            <button onClick={onClose} className="text-[#5F6773] hover:text-[#F5F7FA] transition-colors p-1">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="px-6 py-6 space-y-5">

          {/* ── Step 1: Configure ─────────────────────────────────────────── */}
          {step === "configure" && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Security notice */}
              <div className="border border-[#20242B] bg-[#12151A] rounded-lg px-4 py-3">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-4 h-4 text-[#F59E0B] shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono text-[#F59E0B] uppercase tracking-widest mb-1">Security Notice</div>
                    <p className="text-xs text-[#8B93A1] leading-relaxed">
                      Repository contents are treated as <span className="text-[#F5F7FA] font-mono">UNTRUSTED DATA</span>.
                      No repository code is executed during static analysis.
                    </p>
                  </div>
                </div>
              </div>

              {!repositoryId && (
                <>
                  {/* Provider */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">
                      Provider
                    </label>
                    <div className="flex gap-2">
                      {(["git", "local"] as const).map((p) => (
                        <button
                          key={p}
                          type="button"
                          onClick={() => setProvider(p)}
                          className={cn(
                            "flex items-center gap-2 px-3 py-2 rounded-md border text-sm transition-colors",
                            provider === p
                              ? "border-[#5F6773] text-[#F5F7FA] bg-[#12151A]"
                              : "border-[#20242B] text-[#5F6773] hover:text-[#8B93A1]"
                          )}
                        >
                          {p === "git" ? <GitBranch className="w-4 h-4" /> : <HardDrive className="w-4 h-4" />}
                          {p === "git" ? "Git (HTTPS)" : "Local Path"}
                        </button>
                      ))}
                    </div>
                    {provider === "git" && (
                      <p className="mt-1.5 text-[10px] font-mono text-[#5F6773]">
                        Only public HTTPS URLs. Embedded credentials are rejected.
                      </p>
                    )}
                  </div>

                  {/* Repository name */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">
                      Display Name (optional)
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="my-service"
                      className="w-full bg-[#12151A] border border-[#20242B] rounded-md px-3 py-2 text-sm text-[#F5F7FA] placeholder:text-[#5F6773] font-mono focus:outline-none focus:border-[#5F6773] transition-colors"
                    />
                  </div>

                  {/* Identifier */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">
                      {provider === "git" ? "Repository URL" : "Local Path"}
                    </label>
                    <input
                      type="text"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      placeholder={provider === "git" ? "https://github.com/org/repo" : "C:/path/to/repo"}
                      required
                      className="w-full bg-[#12151A] border border-[#20242B] rounded-md px-3 py-2 text-sm text-[#F5F7FA] placeholder:text-[#5F6773] font-mono focus:outline-none focus:border-[#5F6773] transition-colors"
                    />
                  </div>
                </>
              )}

              {/* Revision */}
              <div>
                <label className="block text-[10px] font-mono text-[#5F6773] uppercase tracking-widest mb-2">
                  Revision (branch, tag, or commit SHA)
                </label>
                <input
                  type="text"
                  value={revision}
                  onChange={(e) => setRevision(e.target.value)}
                  placeholder="main"
                  className="w-full bg-[#12151A] border border-[#20242B] rounded-md px-3 py-2 text-sm text-[#F5F7FA] placeholder:text-[#5F6773] font-mono focus:outline-none focus:border-[#5F6773] transition-colors"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="px-3 py-2.5 rounded-md border border-[#EF4444]/30 bg-[#EF4444]/5 text-xs font-mono text-[#EF4444]">
                  {error}
                </div>
              )}

              {/* Submit */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="text-sm text-[#5F6773] hover:text-[#F5F7FA] transition-colors px-3 py-2"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || (!repositoryId && !identifier.trim())}
                  className="flex items-center gap-2 px-4 py-2 bg-[#F5F7FA] text-[#08090B] text-sm font-medium rounded-md hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  {submitting ? "Starting…" : "Start Analysis"}
                </button>
              </div>
            </form>
          )}

          {/* ── Step 2: Running ───────────────────────────────────────────── */}
          {step === "running" && analysisId && (
            <AnalysisProgress
              analysisId={analysisId}
              onComplete={handleAnalysisComplete}
            />
          )}

          {/* ── Step 3: Complete ──────────────────────────────────────────── */}
          {step === "complete" && (
            <div className="text-center py-6">
              <div className="w-12 h-12 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-[#10B981] text-xl">✓</span>
              </div>
              <p className="text-sm text-[#F5F7FA] font-medium">Analysis Complete</p>
              <p className="text-xs text-[#5F6773] font-mono mt-1">Loading assurance state…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
