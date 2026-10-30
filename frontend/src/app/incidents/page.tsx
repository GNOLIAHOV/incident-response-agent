"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Terminal,
  ArrowLeft,
  Flame,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { fetchIncidents } from "@/lib/api";
import { IncidentItem } from "@/lib/types";
import { IncidentTable } from "@/components/IncidentTable";
import { QuickTriggerModal } from "@/components/QuickTriggerModal";

export default function IncidentsHubPage() {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchIncidents();
      setIncidents(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const activeIncidents = incidents.filter(
    (i) => i.status === "paused_at_breakpoint" || i.status === "processing"
  );
  const resolvedIncidents = incidents.filter(
    (i) => i.status === "completed" || i.status === "approved"
  );

  const primaryActive = activeIncidents[0] || null;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-hairline">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              <span>Executive Dashboard</span>
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-[11px] font-mono text-indigo-400 font-semibold">
              War Room Operations
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <Terminal className="h-5 w-5 text-indigo-400" />
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              War Room Command Hub
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time incident response threads coordinated across LangGraph Multi-Agent SRE Swarm.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            className="p-1.5 rounded-lg bg-surface-900 border border-hairline text-slate-400 hover:text-white transition-colors"
            title="Refresh Threads"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <QuickTriggerModal onSuccess={() => loadData()} />
        </div>
      </div>

      {/* Prominent Active War Room Banner if an incident is in-flight, else calm status */}
      {primaryActive ? (
        <div className="rounded-xl bg-surface-900 border border-indigo-500/30 p-4 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                <span className="text-[11px] font-mono font-semibold text-indigo-400 uppercase">
                  {primaryActive.status === "paused_at_breakpoint"
                    ? "Action Required • Human-in-the-Loop Gate"
                    : "Active Incident In Session"}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    primaryActive.severity === "P0"
                      ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      : primaryActive.severity === "P1"
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      : primaryActive.severity === "P3"
                      ? "bg-sky-500/15 text-sky-400 border border-sky-500/30"
                      : "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                  }`}
                >
                  {primaryActive.severity}
                </span>
              </div>
              <h2 className="text-base font-bold text-white font-mono">
                {primaryActive.thread_id} — {primaryActive.service_name}
              </h2>
              <p className="text-xs text-slate-300">
                {primaryActive.mitigation_action || "Specialist agents formulating remediation plan..."}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Link
                href={`/incidents/${primaryActive.thread_id}`}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors"
              >
                <span>Enter Command Center</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl bg-surface-900 border border-emerald-500/20 p-4">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center shrink-0">
              <CheckCircle2 className="h-4.5 w-4.5" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-white">
                All Systems Operational • Zero Active Incidents
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                All recorded incidents in SQLite checkpointer have been autonomously resolved. LangGraph SRE Swarm is standing by.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stat Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg bg-surface-900 border border-hairline p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-0.5">
            <Flame className="h-3.5 w-3.5 text-rose-400" />
            <span>Active Swarm Threads</span>
          </div>
          <p className="text-xl font-bold text-white font-mono tabular-nums">
            {activeIncidents.length}
          </p>
        </div>

        <div className="rounded-lg bg-surface-900 border border-hairline p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-0.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            <span>Resolved Incidents</span>
          </div>
          <p className="text-xl font-bold text-white font-mono tabular-nums">
            {resolvedIncidents.length}
          </p>
        </div>

        <div className="rounded-lg bg-surface-900 border border-hairline p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mb-0.5">
            <Clock className="h-3.5 w-3.5 text-indigo-400" />
            <span>Total Recorded Operations</span>
          </div>
          <p className="text-xl font-bold text-white font-mono tabular-nums">
            {incidents.length}
          </p>
        </div>
      </div>

      {/* Incidents Stream Table */}
      <IncidentTable incidents={incidents} onRefresh={loadData} />
    </div>
  );
}
