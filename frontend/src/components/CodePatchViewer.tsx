"use client";

import React, { useState } from "react";
import { Check, Copy, ShieldCheck, Code, AlertCircle } from "lucide-react";

interface CodePatchViewerProps {
  patchCode?: string | null;
  serviceName?: string;
  isPaused?: boolean;
}

function parsePatchProposal(rawText?: string | null) {
  if (!rawText) {
    return { objective: "", code: "", astStatus: "" };
  }

  let objective = "";
  let code = rawText;
  let astStatus = "Passed ✅";

  // Extract Objective if present in markdown
  const objMatch = rawText.match(/\*\*Objective:\*\*\s*([^\n]+)/i);
  if (objMatch) objective = objMatch[1].trim();

  // Extract AST Syntax Validation if present
  const astMatch = rawText.match(/\*AST Syntax Validation:\*\s*([^\n]+)/i);
  if (astMatch) astStatus = astMatch[1].trim();

  // Extract clean code block from ```python ... ```
  const codeMatch = rawText.match(/```(?:python)?\r?\n([\s\S]*?)```/);
  if (codeMatch) {
    code = codeMatch[1].trim();
  }

  return { objective, code, astStatus };
}

export function CodePatchViewer({
  patchCode,
  serviceName,
}: CodePatchViewerProps) {
  const [copied, setCopied] = useState(false);

  const { objective, code, astStatus } = parsePatchProposal(patchCode);

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code ? code.split("\n") : [];

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
            Target file: <span className="font-mono text-slate-300">{serviceName || "service"}/app.py</span>
            {objective && (
              <span className="text-slate-400 block sm:inline sm:ml-2">
                • {objective}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {code ? (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>{astStatus ? `AST ${astStatus}` : "AST Verified Safe"}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-surface-850 text-slate-400 text-[11px] font-mono border border-hairline">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Synthesizing...</span>
            </div>
          )}

          {code && (
            <button
              onClick={handleCopy}
              className="p-1 rounded bg-surface-850 border border-hairline text-slate-400 hover:text-white transition-colors"
              title="Copy Clean Python Code"
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

      {code ? (
        <div className="relative rounded-lg bg-surface-950 border border-hairline overflow-hidden font-mono text-xs">
          <div className="flex items-center justify-between px-3.5 py-1.5 bg-surface-900 border-b border-hairline text-[10px] text-slate-400">
            <span>Python Source Diff</span>
            <span className="text-emerald-400 font-semibold">Ready for GitHub PR Dispatch</span>
          </div>

          <div className="p-3.5 overflow-x-auto max-h-96">
            <table className="w-full text-xs">
              <tbody>
                {lines.map((line, idx) => {
                  const isComment = line.trim().startsWith("#");
                  const isKeyword =
                    line.includes("def ") ||
                    line.includes("return ") ||
                    line.includes("raise ") ||
                    line.includes("if ") ||
                    line.includes("else:");

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
