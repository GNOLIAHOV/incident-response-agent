"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertOctagon, Flame, X, Loader2, Sparkles } from "lucide-react";
import { triggerIncident } from "@/lib/api";

interface QuickTriggerModalProps {
  onSuccess?: (threadId: string) => void;
}

const PRESETS = [
  {
    name: "Payment Gateway Failure (P0)",
    service: "payment_service",
    description: "Gateway Timeout 504 spike. Transaction error rate jumped to 98.4% under flash sale load.",
  },
  {
    name: "Auth Token JWT Loop (P1)",
    service: "auth_service",
    description: "JWT token verification loop causing CPU spike to 95% on authentication cluster nodes.",
  },
  {
    name: "Inventory DB Pool Exhaustion (P2)",
    service: "inventory_service",
    description: "Active database pool exhausted at 20/20 connections. Stock update latency > 3500ms.",
  },
];

export function QuickTriggerModal({ onSuccess }: QuickTriggerModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [serviceName, setServiceName] = useState("payment_service");
  const [issueDescription, setIssueDescription] = useState(PRESETS[0].description);
  const [customThreadId, setCustomThreadId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

  const handleApplyPreset = (service: string, desc: string) => {
    setServiceName(service);
    setIssueDescription(desc);
  };

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!serviceName.trim() || !issueDescription.trim()) return;

    setIsLoading(true);
    setError(null);

    const generatedId =
      customThreadId.trim() ||
      `INC-${serviceName.substring(0, 4).toUpperCase()}-${Math.floor(
        100 + Math.random() * 900
      )}`;

    try {
      await triggerIncident({
        service_name: serviceName.trim(),
        issue_description: issueDescription.trim(),
        thread_id: generatedId,
      });

      setIsOpen(false);
      if (onSuccess) {
        onSuccess(generatedId);
      }
      router.push(`/incidents/${generatedId}`);
    } catch (err: any) {
      setError(err?.message || "Failed to trigger incident");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-amber-600 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-rose-600/20 hover:opacity-95 transition-all hover:scale-[1.02] active:scale-[0.98]"
      >
        <Flame className="h-4 w-4" />
        <span>Simulate Emergency Incident</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl bg-obsidian-900 border border-slate-700 p-6 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <AlertOctagon className="h-5 w-5 text-rose-500" />
                <h3 className="font-semibold text-white text-base">
                  Trigger Production Incident
                </h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Quick Presets */}
            <div className="mt-4">
              <label className="text-xs font-semibold uppercase text-slate-400 flex items-center gap-1.5 mb-2">
                <Sparkles className="h-3 w-3 text-indigo-400" />
                <span>Simulated Scenarios (1-Click)</span>
              </label>
              <div className="grid grid-cols-1 gap-2">
                {PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleApplyPreset(p.service, p.description)}
                    className={`text-left p-2.5 rounded-lg border text-xs transition-all ${
                      serviceName === p.service && issueDescription === p.description
                        ? "bg-indigo-600/20 border-indigo-500 text-white"
                        : "bg-slate-800/40 border-slate-700 text-slate-300 hover:bg-slate-800/80"
                    }`}
                  >
                    <span className="font-semibold block">{p.name}</span>
                    <span className="text-[11px] text-slate-400 line-clamp-1">
                      {p.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleTrigger} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Target Service Name
                </label>
                <input
                  type="text"
                  required
                  value={serviceName}
                  onChange={(e) => setServiceName(e.target.value)}
                  placeholder="e.g. payment_service"
                  className="w-full px-3 py-2 rounded-lg bg-obsidian-950 border border-slate-700 font-mono text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Issue Description / Alert Anomaly
                </label>
                <textarea
                  required
                  rows={3}
                  value={issueDescription}
                  onChange={(e) => setIssueDescription(e.target.value)}
                  placeholder="Describe the operational anomaly..."
                  className="w-full px-3 py-2 rounded-lg bg-obsidian-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Custom Thread ID (Optional)
                </label>
                <input
                  type="text"
                  value={customThreadId}
                  onChange={(e) => setCustomThreadId(e.target.value)}
                  placeholder="Auto-generated if blank (e.g. INC-PROD-002)"
                  className="w-full px-3 py-1.5 rounded-lg bg-obsidian-950 border border-slate-800 font-mono text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  {error}
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Dispatching Swarm...</span>
                    </>
                  ) : (
                    <>
                      <Flame className="h-4 w-4" />
                      <span>Dispatch Multi-Agent Swarm</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
