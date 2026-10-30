"use client";

import React, { useState, useEffect } from "react";
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

  // Keyboard shortcuts: A for Approve, R for Revise
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if typing inside a textarea or input
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }
      if (e.key === "a" || e.key === "A") {
        e.preventDefault();
        handleApprove();
      } else if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        setShowFeedbackInput(true);
      }
    };

    if (isPaused || approvalStatus === "pending") {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isPaused, approvalStatus]);

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
      <div className="rounded-xl bg-emerald-950/20 border border-emerald-500/20 p-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-white text-xs">
              Code Patch Approved & GitHub PR Dispatched
            </h4>
            <p className="text-[11px] text-slate-300 mt-0.5">
              Pull Request was generated and verified. The Scribe Specialist has compiled the Google SRE Post-Mortem.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (approvalStatus === "rejected") {
    return (
      <div className="rounded-xl bg-rose-950/20 border border-rose-500/20 p-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center shrink-0">
            <XCircle className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-white text-xs">
              Patch Rejected by Engineer
            </h4>
            <p className="text-[11px] text-slate-300 mt-0.5">
              The proposed code modification was cancelled. No pull request was created.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3.5 pb-3 border-b border-hairline">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-indigo-400" />
            <h4 className="font-semibold text-white text-sm">
              Human-in-the-Loop Verification Gate
            </h4>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Agent paused at breakpoint. Inspect proposed AST patch and authorize deployment.
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-surface-850 border border-hairline text-sky-400 text-[11px] font-mono">
          <Send className="h-3 w-3" />
          <span>Telegram Synced</span>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      {!showFeedbackInput ? (
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleApprove}
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors duration-150 disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5" />
            )}
            <span>Approve & Open GitHub PR</span>
            <span className="kbd-cap bg-emerald-800 text-emerald-200 border-emerald-700">A</span>
          </button>

          <button
            onClick={() => setShowFeedbackInput(true)}
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-surface-850 hover:bg-surface-800 text-amber-400 border border-amber-500/30 font-semibold text-xs transition-colors duration-150 disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Request Revision</span>
            <span className="kbd-cap">R</span>
          </button>

          <button
            onClick={handleReject}
            disabled={isSubmitting}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-850 hover:bg-surface-800 text-rose-400 border border-rose-500/30 font-semibold text-xs transition-colors duration-150 disabled:opacity-50"
          >
            <XCircle className="h-3.5 w-3.5" />
            <span>Reject</span>
          </button>
        </div>
      ) : (
        /* Human Feedback Input Form */
        <form onSubmit={handleRevisionSubmit} className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Provide Feedback to Patching Specialist</span>
          </div>

          <textarea
            rows={2}
            required
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="e.g. Please increase socket timeout to 10s and add exponential backoff retry..."
            className="w-full px-3 py-1.5 rounded-lg bg-surface-950 border border-hairline text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/60 font-mono"
          />

          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowFeedbackInput(false)}
              className="px-3 py-1 rounded text-xs text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
              <span>Submit Feedback</span>
            </button>
          </div>
        </form>
      )}

      {/* Info footer */}
      <p className="text-[10px] text-slate-500 mt-3 font-mono">
        Dual Authorization: Press [A] to Approve, [R] to Request Revision, or tap button on Telegram.
      </p>
    </div>
  );
}
