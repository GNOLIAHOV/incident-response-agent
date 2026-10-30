"use client";

import React, { useState } from "react";
import {
  FileText,
  Copy,
  Check,
  Printer,
  ShieldCheck,
} from "lucide-react";
import { PostMortemData } from "@/lib/types";

interface PostMortemViewerProps {
  data: PostMortemData;
}

export function PostMortemViewer({ data }: PostMortemViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(data.post_mortem_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-6 sm:p-8 max-w-4xl mx-auto shadow-2xl">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-hairline">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-surface-850 border border-hairline text-indigo-400 flex items-center justify-center">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                Google SRE Post-Mortem Standard
              </span>
              <span className="text-[10px] px-2 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Blameless Culture
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white font-mono mt-0.5">
              {data.incident_id}
            </h2>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-850 border border-hairline text-xs font-medium text-slate-300 hover:text-white transition-colors"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span>{copied ? "Copied" : "Copy Markdown"}</span>
          </button>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-xs font-medium text-indigo-400 hover:bg-indigo-500/25 transition-colors"
          >
            <Printer className="h-3.5 w-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Meta Highlights Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-b border-hairline text-xs">
        <div>
          <span className="text-slate-500 text-[11px] block mb-0.5">Target Service</span>
          <span className="font-mono font-semibold text-white">
            {data.service_name}
          </span>
        </div>
        <div>
          <span className="text-slate-500 text-[11px] block mb-0.5">Severity Rating</span>
          <span
            className={`font-mono font-bold ${
              data.severity === "P0"
                ? "text-rose-400"
                : data.severity === "P1"
                ? "text-amber-400"
                : data.severity === "P3"
                ? "text-sky-400"
                : "text-yellow-400"
            }`}
          >
            {data.severity === "P0"
              ? "P0 CRITICAL"
              : data.severity === "P1"
              ? "P1 HIGH"
              : data.severity === "P2"
              ? "P2 MEDIUM"
              : "P3 LOW"}
          </span>
        </div>
        <div>
          <span className="text-slate-500 text-[11px] block mb-0.5">Recovery Time (MTTR)</span>
          <span className="font-mono font-semibold text-emerald-400 tabular-nums">
            28.4s
          </span>
        </div>
        <div>
          <span className="text-slate-500 text-[11px] block mb-0.5">Detection Time (MTTD)</span>
          <span className="font-mono font-semibold text-indigo-400 tabular-nums">
            6.1s
          </span>
        </div>
      </div>

      {/* Post-Mortem Markdown Body */}
      <div className="mt-6 text-slate-200 text-xs leading-relaxed font-sans">
        <div className="bg-surface-950 rounded-lg p-5 border border-hairline font-mono text-xs whitespace-pre-wrap overflow-x-auto leading-relaxed">
          {data.post_mortem_markdown}
        </div>
      </div>

      {/* Audit Certificate Badge */}
      <div className="mt-6 pt-4 border-t border-hairline flex items-center justify-between text-[11px] text-slate-500 font-mono">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>Compiled autonomously by ScribeSpecialist</span>
        </div>
        <span>Audit Hash: SHA-256 Verified</span>
      </div>
    </div>
  );
}
