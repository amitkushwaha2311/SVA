"use client";

import { useState } from "react";
import { X, GitBranch, HardDrive, AlertTriangle, ArrowRight, Loader2, Check } from "lucide-react";
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
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="bg-[#211B16] border border-[#514236] rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-[#514236] bg-[#2A221B]/40">
          <div>
            <h2 className="text-base font-serif font-medium text-[#F5EFE5]">Analyze Repository</h2>
            <p className="text-xs text-[#B5AA9C] font-mono mt-0.5">
              {step === "configure" && "Register and analyze repository semantics"}
              {step === "running"   && "Analysis pipeline running…"}
              {step === "complete"  && "Analysis complete"}
            </p>
          </div>
          {step !== "running" && (
            <button onClick={onClose} className="text-[#847768] hover:text-[#F5EFE5] transition-colors p-1.5 rounded-lg hover:bg-[#2A221B]">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="px-6 py-6 space-y-5">

          {/* ── Step 1: Configure ─────────────────────────────────────────── */}
          {step === "configure" && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Security notice */}
              <div className="border border-[#514236] bg-[#2A221B] rounded-xl px-4 py-3.5 shadow-sm">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-4 h-4 text-[#C8792C] shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono text-[#C8792C] uppercase tracking-widest mb-1 font-medium">Security Notice</div>
                    <p className="text-xs text-[#B5AA9C] leading-relaxed">
                      Repository contents are treated as <span className="text-[#F5EFE5] font-mono font-medium">UNTRUSTED DATA</span>.
                      No repository code is executed during static analysis.
                    </p>
                  </div>
                </div>
              </div>

              {!repositoryId && (
                <>
                  {/* Provider */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">
                      Provider
                    </label>
                    <div className="flex gap-2">
                      {(["git", "local"] as const).map((p) => (
                        <button
                          key={p}
                          type="button"
                          onClick={() => setProvider(p)}
                          className={cn(
                            "flex items-center gap-2 px-3.5 py-2 rounded-xl border text-sm transition-all font-medium",
                            provider === p
                              ? "border-[#F4D9A0] text-[#F5EFE5] bg-[#2A221B] shadow-sm"
                              : "border-[#514236] text-[#847768] hover:text-[#B5AA9C] bg-[#17130F]/40"
                          )}
                        >
                          {p === "git" ? <GitBranch className="w-4 h-4 text-[#F4D9A0]" /> : <HardDrive className="w-4 h-4 text-[#F4D9A0]" />}
                          {p === "git" ? "Git (HTTPS)" : "Local Path"}
                        </button>
                      ))}
                    </div>
                    {provider === "git" && (
                      <p className="mt-1.5 text-[10px] font-mono text-[#847768]">
                        Only public HTTPS URLs. Embedded credentials are rejected.
                      </p>
                    )}
                  </div>

                  {/* Repository name */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">
                      Display Name (optional)
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="my-service"
                      className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-sm text-[#F5EFE5] placeholder:text-[#847768] font-mono focus:outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all"
                    />
                  </div>

                  {/* Identifier */}
                  <div>
                    <label className="block text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">
                      {provider === "git" ? "Repository URL" : "Local Path"}
                    </label>
                    <input
                      type="text"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      placeholder={provider === "git" ? "https://github.com/org/repo" : "C:/path/to/repo"}
                      required
                      className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-sm text-[#F5EFE5] placeholder:text-[#847768] font-mono focus:outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all"
                    />
                  </div>
                </>
              )}

              {/* Revision */}
              <div>
                <label className="block text-[10px] font-mono text-[#847768] uppercase tracking-widest mb-2 font-medium">
                  Revision (branch, tag, or commit SHA)
                </label>
                <input
                  type="text"
                  value={revision}
                  onChange={(e) => setRevision(e.target.value)}
                  placeholder="main"
                  className="w-full bg-[#2A221B] border border-[#514236] rounded-xl px-3.5 py-2.5 text-sm text-[#F5EFE5] placeholder:text-[#847768] font-mono focus:outline-none focus:border-[#F4D9A0] focus:ring-1 focus:ring-[#F4D9A0]/30 transition-all"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="px-3.5 py-2.5 rounded-xl border border-[#EF4444]/30 bg-[#EF4444]/10 text-xs font-mono text-[#EF4444]">
                  {error}
                </div>
              )}

              {/* Submit */}
              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="text-sm font-medium text-[#B5AA9C] hover:text-[#F5EFE5] transition-colors px-4 py-2.5 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || (!repositoryId && !identifier.trim())}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#F4D9A0] text-[#17130F] text-sm font-semibold rounded-xl hover:bg-[#fae6bb] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-[#F4D9A0]/10 active:scale-95"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin text-[#17130F]" /> : <ArrowRight className="w-4 h-4" />}
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
            <div className="text-center py-8 space-y-3">
              <div className="w-14 h-14 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 flex items-center justify-center mx-auto mb-2 shadow-lg shadow-[#10B981]/10">
                <Check className="w-7 h-7 text-[#10B981]" />
              </div>
              <p className="text-base text-[#F5EFE5] font-serif font-medium">Analysis Complete</p>
              <p className="text-xs text-[#B5AA9C] font-mono">Loading assurance state…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
