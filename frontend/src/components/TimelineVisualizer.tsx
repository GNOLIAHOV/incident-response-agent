"use client";

import React from "react";
import {
  CheckCircle2,
  Clock,
  CircleDot,
  Radio,
  ShieldAlert,
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
    <div className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="font-semibold text-white text-base">
            Multi-Agent Swarm Execution Flow
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time stage transitions coordinated by LangGraph Supervisor
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono">
          <CircleDot className="h-3 w-3 animate-pulse" />
          <span>Live Checkpoint Stream</span>
        </div>
      </div>

      <div className="relative pl-6 space-y-8 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {STAGES.map((stage, idx) => {
          const matchingEvent = events.find((e) =>
            e.stage ? e.stage.toLowerCase() === stage.key : false
          );
          const hasOccurred = !!matchingEvent;
          const isPausedAtThis =
            stage.key === "hitl_gate" && currentStatus === "paused_at_breakpoint";
          const isLastCompleted =
            hasOccurred &&
            (currentStatus === "completed" || idx <= events.length - 1);

          const Icon = stage.icon;

          return (
            <div key={stage.key} className="relative group">
              {/* Timeline Node Indicator */}
              <div
                className={`absolute -left-6 top-0.5 h-6 w-6 rounded-full flex items-center justify-center transition-all ${
                  isPausedAtThis
                    ? "bg-amber-500 text-obsidian-950 ring-4 ring-amber-500/20 animate-pulse"
                    : hasOccurred
                    ? "bg-emerald-500 text-obsidian-950 ring-4 ring-emerald-500/10"
                    : "bg-obsidian-900 border border-slate-700 text-slate-500"
                }`}
              >
                {hasOccurred ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : isPausedAtThis ? (
                  <Clock className="h-3.5 w-3.5" />
                ) : (
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-600" />
                )}
              </div>

              {/* Stage Content */}
              <div className="pl-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-semibold text-sm ${
                        isPausedAtThis
                          ? "text-amber-400"
                          : hasOccurred
                          ? "text-white"
                          : "text-slate-400"
                      }`}
                    >
                      {stage.name}
                    </span>
                    <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      {stage.agent}
                    </span>
                  </div>

                  {matchingEvent?.timestamp && (
                    <span className="text-xs text-slate-500 font-mono">
                      {matchingEvent.timestamp}
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-400 mb-2">
                  {stage.desc}
                </p>

                {matchingEvent && (
                  <div className="p-3 rounded-xl bg-obsidian-900 border border-slate-800 text-xs text-slate-300 font-sans leading-relaxed">
                    <span className="text-emerald-400 font-mono font-medium block mb-1">
                      Action Dispatched:
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
