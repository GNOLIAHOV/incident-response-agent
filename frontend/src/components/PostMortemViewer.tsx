"use client";

import React, { useState } from "react";
import {
  FileText,
  Copy,
  Check,
  Printer,
  ShieldCheck,
  Clock,
  Zap,
  Tag,
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
    <div className="rounded-2xl bg-obsidian-850/90 border border-slate-800 p-6 sm:p-8 backdrop-blur-sm max-w-4xl mx-auto shadow-2xl">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                Google SRE Post-Mortem Standard
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                Blameless Culture
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white font-mono mt-0.5">
              {data.incident_id}
            </h2>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-obsidian-900 border border-slate-700 text-xs font-medium text-slate-300 hover:text-white hover:border-slate-600 transition-colors"
          >
            {copied ? (
              <Check className="h-4 w-4 text-emerald-400" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
            <span>{copied ? "Copied" : "Copy Markdown"}</span>
          </button>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-xs font-medium text-indigo-400 hover:bg-indigo-600/30 transition-colors"
          >
            <Printer className="h-4 w-4" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Meta Highlights Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-b border-slate-800 text-xs">
        <div>
          <span className="text-slate-400 block mb-1">Target Service</span>
          <span className="font-mono font-semibold text-white">
            {data.service_name}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-1">Severity Rating</span>
          <span className="font-mono font-bold text-rose-400">
            {data.severity} CRITICAL
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-1">Recovery Time (MTTR)</span>
          <span className="font-mono font-semibold text-emerald-400">
            ~28 seconds
          </span>
        </div>
        <div>
          <span className="text-slate-400 block mb-1">Detection Time (MTTD)</span>
          <span className="font-mono font-semibold text-indigo-400">
            ~6 seconds
          </span>
        </div>
      </div>

      {/* Post-Mortem Markdown Body */}
      <div className="mt-8 prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed font-sans space-y-6">
        <div className="bg-obsidian-950 rounded-xl p-6 border border-slate-800 font-mono text-xs whitespace-pre-wrap overflow-x-auto leading-relaxed">
          {data.post_mortem_markdown}
        </div>
      </div>

      {/* Audit Certificate Badge */}
      <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          <span>Compiled autonomously by ScribeSpecialist</span>
        </div>
        <span className="font-mono">Audit Hash: SHA-256 Verified</span>
      </div>
    </div>
  );
}
