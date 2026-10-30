"use client";

import React from "react";
import {
  CheckCircle2,
  Clock,
  CircleDot,
  Radio,
  Flame,
  Search,
  Code2,
  Lock,
  FileCheck2,
} from "lucide-react";
import { TimelineEvent } from "@/lib/types";

interface TimelineVisualizerProps {
  timeline?: TimelineEvent[] | null;
  currentStatus: string;
}

const STAGES = [
  {
    key: "triage",
    name: "1. Incident Triage",
    agent: "TriageSpecialist",
    icon: Flame,
    desc: "Alert ingestion & severity scoring (P0/P1/P2)",
  },
  {
    key: "remediation",
    name: "2. Active Mitigation",
    agent: "MitigationSpecialist",
    icon: Radio,
    desc: "Circuit breaker / rate limiter to halt bleeding",
  },
  {
    key: "investigator",
    name: "3. Root Cause Investigation",
    agent: "RootCauseSpecialist",
    icon: Search,
    desc: "5 Whys analysis & log correlation",
  },
  {
    key: "patching",
    name: "4. AST Code Patching",
    agent: "PatchingSpecialist",
    icon: Code2,
    desc: "Syntactic AST validation & test patch generation",
  },
  {
    key: "hitl_gate",
    name: "5. Human-in-the-Loop Gate",
    agent: "HITLGate",
    icon: Lock,
    desc: "Dual authorization via Web Portal & Telegram Bot",
  },
  {
    key: "scribe",
    name: "6. Post-Mortem & GitHub PR",
    agent: "ScribeSpecialist",
    icon: FileCheck2,
    desc: "Google SRE post-mortem doc & automated PR dispatch",
  },
];

export function TimelineVisualizer({
  timeline,
  currentStatus,
}: TimelineVisualizerProps) {
  const events = timeline || [];

  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-5">
      <div className="flex items-center justify-between mb-5 pb-3 border-b border-hairline">
        <div>
          <h3 className="font-semibold text-white text-sm">
            Multi-Agent Swarm Progression
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Stage transitions coordinated by Supervisor in LangGraph
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-850 border border-hairline text-indigo-400 text-[10px] font-mono">
          <CircleDot className="h-2.5 w-2.5 animate-pulse" />
          <span>Live Checkpoint</span>
        </div>
      </div>

      <div className="relative pl-5 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-px before:bg-slate-800">
        {STAGES.map((stage) => {
          const matchingEvent = events.find((e) =>
            e.stage ? e.stage.toLowerCase() === stage.key : false
          );
          const hasOccurred = !!matchingEvent;
          const isPausedAtThis =
            stage.key === "hitl_gate" && currentStatus === "paused_at_breakpoint";

          return (
            <div key={stage.key} className="relative">
              {/* Timeline Node Indicator */}
              <div
                className={`absolute -left-5 top-0.5 h-5 w-5 rounded-full flex items-center justify-center transition-colors ${
                  isPausedAtThis
                    ? "bg-amber-500 text-surface-950 ring-4 ring-amber-500/20 animate-pulse"
                    : hasOccurred
                    ? "bg-emerald-500 text-surface-950"
                    : "bg-surface-950 border border-slate-700 text-slate-500"
                }`}
              >
                {hasOccurred ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : isPausedAtThis ? (
                  <Clock className="h-3 w-3" />
                ) : (
                  <div className="h-1 w-1 rounded-full bg-slate-600" />
                )}
              </div>

              {/* Stage Content */}
              <div className="pl-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-0.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-semibold text-xs ${
                        isPausedAtThis
                          ? "text-amber-400"
                          : hasOccurred
                          ? "text-white"
                          : "text-slate-400"
                      }`}
                    >
                      {stage.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-800 text-slate-400 font-mono border border-hairline">
                      {stage.agent}
                    </span>
                  </div>

                  {matchingEvent?.timestamp && (
                    <span className="text-[10px] text-slate-500 font-mono tabular-nums">
                      {matchingEvent.timestamp}
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-slate-400 mb-1.5">
                  {stage.desc}
                </p>

                {matchingEvent && (
                  <div className="p-2.5 rounded-lg bg-surface-950 border border-hairline text-[11px] text-slate-300 font-sans leading-relaxed">
                    <span className="text-emerald-400 font-mono text-[10px] font-semibold block mb-0.5">
                      Action Executed:
                    </span>
                    {matchingEvent.message || "Agent task executed and verified."}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
