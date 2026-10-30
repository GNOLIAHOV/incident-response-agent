"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Send,
  Loader2,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import { submitApproval } from "@/lib/api";

interface HITLActionBarProps {
  threadId: string;
  isPaused: boolean;
  approvalStatus?: string;
  onDecisionSubmitted?: () => void;
}

export function HITLActionBar({
  threadId,
  isPaused,
  approvalStatus,
  onDecisionSubmitted,
}: HITLActionBarProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await submitApproval(threadId, { approved: true });
      if (onDecisionSubmitted) onDecisionSubmitted();
    } catch (err: any) {
      setError(err?.message || "Failed to submit approval");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      await submitApproval(threadId, { approved: false });
      if (onDecisionSubmitted) onDecisionSubmitted();
    } catch (err: any) {
      setError(err?.message || "Failed to reject fix");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackText.trim()) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await submitApproval(threadId, {
        approved: false,
        feedback: feedbackText.trim(),
      });
      setShowFeedbackInput(false);
      setFeedbackText("");
      if (onDecisionSubmitted) onDecisionSubmitted();
    } catch (err: any) {
      setError(err?.message || "Failed to submit revision feedback");
    } finally {
      setIsSubmitting(false);
    }
  };

  // If already resolved or escalated
  if (approvalStatus === "approved" || approvalStatus === "completed") {
    return (
      <div className="rounded-2xl bg-emerald-950/30 border border-emerald-500/30 p-6 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm">
              Code Patch Approved & GitHub PR Dispatched
            </h4>
            <p className="text-xs text-slate-300 mt-0.5">
              Pull Request was generated and verified. The Scribe Specialist has compiled the Google SRE Post-Mortem.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (approvalStatus === "rejected") {
    return (
      <div className="rounded-2xl bg-rose-950/30 border border-rose-500/30 p-6 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
            <XCircle className="h-6 w-6" />
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm">
              Patch Rejected by Engineer
            </h4>
            <p className="text-xs text-slate-300 mt-0.5">
              The proposed code modification was cancelled. No pull request was created.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-400" />
            <h4 className="font-semibold text-white text-base">
              Human-in-the-Loop Verification Gate
            </h4>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Agent paused at breakpoint. Inspect proposed AST patch and authorize deployment.
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono">
          <Send className="h-3 w-3" />
          <span>Telegram Synced</span>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      {!showFeedbackInput ? (
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleApprove}
            disabled={isSubmitting}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
            <span>Approve & Open GitHub PR</span>
          </button>

          <button
            onClick={() => setShowFeedbackInput(true)}
            disabled={isSubmitting}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600/20 text-amber-400 border border-amber-500/30 hover:bg-amber-600/30 font-semibold text-xs transition-all disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Request Revision</span>
          </button>

          <button
            onClick={handleReject}
            disabled={isSubmitting}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600/20 text-rose-400 border border-rose-500/30 hover:bg-rose-600/30 font-semibold text-xs transition-all disabled:opacity-50"
          >
            <XCircle className="h-4 w-4" />
            <span>Reject Patch</span>
          </button>
        </div>
      ) : (
        /* Human Feedback Input Form */
        <form onSubmit={handleRevisionSubmit} className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
            <MessageSquare className="h-4 w-4" />
            <span>Provide Feedback to Patching Specialist</span>
          </div>

          <textarea
            rows={2}
            required
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="e.g. Please increase socket timeout to 10s and add exponential backoff retry..."
            className="w-full px-3 py-2 rounded-xl bg-obsidian-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono"
          />

          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowFeedbackInput(false)}
              className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
              <span>Submit Feedback to Agent</span>
            </button>
          </div>
        </form>
      )}

      {/* Info footer */}
      <p className="text-[11px] text-slate-500 mt-4">
        💡 Dual Authorization Active: SRE engineers on duty can also tap the approval button in the team Telegram channel.
      </p>
    </div>
  );
}
