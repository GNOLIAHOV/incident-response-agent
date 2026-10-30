"use client";

import React, { useState } from "react";
import { Check, Copy, ShieldCheck, Code, AlertCircle } from "lucide-react";

interface CodePatchViewerProps {
  patchCode?: string | null;
  serviceName?: string;
  isPaused?: boolean;
}

export function CodePatchViewer({
  patchCode,
  serviceName,
  isPaused,
}: CodePatchViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!patchCode) return;
    navigator.clipboard.writeText(patchCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = (patchCode || "").split("\n");

  return (
    <div className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Code className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-white text-base">
              Autonomous Code Patch
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Target file: <span className="font-mono text-slate-300">{serviceName || "service"}/app.py</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {patchCode ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>AST Validated</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 text-slate-400 text-xs font-mono">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Awaiting Patch Synthesis</span>
            </div>
          )}

          {patchCode && (
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg bg-obsidian-900 border border-slate-700 text-slate-400 hover:text-white transition-colors"
              title="Copy Patch to Clipboard"
            >
              {copied ? (
                <Check className="h-4 w-4 text-emerald-400" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {patchCode ? (
        <div className="relative rounded-xl bg-obsidian-950 border border-slate-800 overflow-hidden font-mono text-xs">
          <div className="flex items-center justify-between px-4 py-2 bg-obsidian-900 border-b border-slate-800 text-[11px] text-slate-400">
            <span>Unified Diff Preview</span>
            <span className="text-emerald-400 font-semibold">Ready for GitHub PR Dispatch</span>
          </div>

          <div className="p-4 overflow-x-auto max-h-96">
            <table className="w-full">
              <tbody>
                {lines.map((line, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50">
                    <td className="w-10 pr-4 text-right text-slate-600 select-none">
                      {idx + 1}
                    </td>
                    <td className="text-slate-200 whitespace-pre">
                      {line}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="rounded-xl bg-obsidian-950 border border-slate-800 p-8 text-center">
          <Code className="h-8 w-8 text-slate-600 mx-auto mb-2 animate-pulse" />
          <p className="text-xs text-slate-400">
            PatchingSpecialist is analyzing the AST and synthesizing remediation code...
          </p>
        </div>
      )}
    </div>
  );
}
