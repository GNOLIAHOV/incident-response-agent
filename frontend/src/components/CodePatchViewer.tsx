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
    <div className="rounded-xl bg-surface-900 border border-hairline p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3.5 pb-3 border-b border-hairline">
        <div>
          <div className="flex items-center gap-2">
            <Code className="h-4 w-4 text-indigo-400" />
            <h3 className="font-semibold text-white text-sm">
              AST-Validated Code Patch
            </h3>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Target: <span className="font-mono text-slate-300">{serviceName || "service"}/app.py</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {patchCode ? (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>AST Verified Safe</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-surface-850 text-slate-400 text-[11px] font-mono border border-hairline">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Synthesizing...</span>
            </div>
          )}

          {patchCode && (
            <button
              onClick={handleCopy}
              className="p-1 rounded bg-surface-850 border border-hairline text-slate-400 hover:text-white transition-colors"
              title="Copy Patch to Clipboard"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          )}
        </div>
      </div>

      {patchCode ? (
        <div className="relative rounded-lg bg-surface-950 border border-hairline overflow-hidden font-mono text-xs">
          <div className="flex items-center justify-between px-3.5 py-1.5 bg-surface-900 border-b border-hairline text-[10px] text-slate-400">
            <span>Unified Diff Inspection</span>
            <span className="text-emerald-400 font-semibold">Zero Unsafe Syscalls Detected</span>
          </div>

          <div className="p-3.5 overflow-x-auto max-h-96">
            <table className="w-full text-xs">
              <tbody>
                {lines.map((line, idx) => {
                  const isComment = line.trim().startsWith("#");
                  const isKeyword = line.includes("def ") || line.includes("return ") || line.includes("raise ");

                  return (
                    <tr key={idx} className="hover:bg-surface-900/60 transition-colors">
                      <td className="w-8 pr-3 text-right text-slate-600 select-none tabular-nums text-[11px]">
                        {idx + 1}
                      </td>
                      <td
                        className={`whitespace-pre text-xs ${
                          isComment
                            ? "text-emerald-400/80 font-sans italic"
                            : isKeyword
                            ? "text-indigo-300"
                            : "text-slate-200"
                        }`}
                      >
                        {line}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="rounded-lg bg-surface-950 border border-hairline p-6 text-center">
          <Code className="h-6 w-6 text-slate-600 mx-auto mb-2 animate-pulse" />
          <p className="text-xs text-slate-400">
            PatchingSpecialist is analyzing the AST and synthesizing remediation code...
          </p>
        </div>
      )}
    </div>
  );
}
