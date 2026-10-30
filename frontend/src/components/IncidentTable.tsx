"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  ExternalLink,
  FileText,
  Search,
  ShieldAlert,
} from "lucide-react";
import { IncidentItem, IncidentSeverity } from "@/lib/types";

interface IncidentTableProps {
  incidents: IncidentItem[];
  onRefresh?: () => void;
}

export function IncidentTable({ incidents, onRefresh }: IncidentTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  const filteredIncidents = incidents.filter((item) => {
    const matchesSearch =
      item.thread_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.service_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.mitigation_action &&
        item.mitigation_action.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesSeverity =
      severityFilter === "ALL" || item.severity === severityFilter;

    return matchesSearch && matchesSeverity;
  });

  const getSeverityBadge = (severity?: IncidentSeverity) => {
    switch (severity) {
      case "P0":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            P0 CRITICAL
          </span>
        );
      case "P1":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            P1 HIGH
          </span>
        );
      case "P2":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">
            P2 MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-slate-700/40 text-slate-300 border border-slate-600/30">
            {severity || "P3 LOW"}
          </span>
        );
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "completed":
      case "approved":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="h-3 w-3" />
            Resolved
          </span>
        );
      case "paused_at_breakpoint":
      case "pending":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse">
            <Clock className="h-3 w-3" />
            Awaiting HITL
          </span>
        );
      case "escalated":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertCircle className="h-3 w-3" />
            Escalated
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
            <ShieldAlert className="h-3 w-3" />
            {status || "Active"}
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="font-semibold text-white text-base">
            Incident Operations Log
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Historical and active production incidents handled by autonomous multi-agent swarm
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search service, thread ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 pl-9 pr-3 py-1.5 rounded-lg bg-obsidian-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Severity Filter Tabs */}
          <div className="flex items-center bg-obsidian-900 rounded-lg p-1 border border-slate-800">
            {["ALL", "P0", "P1", "P2"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                  severityFilter === sev
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-medium">
              <th className="pb-3 pl-2">INCIDENT THREAD</th>
              <th className="pb-3">TARGET SERVICE</th>
              <th className="pb-3">SEVERITY</th>
              <th className="pb-3">LIFECYCLE STATUS</th>
              <th className="pb-3">AUTONOMOUS ACTION TAKEN</th>
              <th className="pb-3 pr-2 text-right">ACTION LINKS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {filteredIncidents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No matching incidents found in system checkpointer.
                </td>
              </tr>
            ) : (
              filteredIncidents.map((incident) => (
                <tr
                  key={incident.thread_id}
                  className="hover:bg-slate-800/30 transition-colors group"
                >
                  <td className="py-3.5 pl-2 font-mono font-semibold text-white">
                    <Link
                      href={`/incidents/${incident.thread_id}`}
                      className="hover:text-indigo-400 flex items-center gap-1"
                    >
                      {incident.thread_id}
                    </Link>
                  </td>
                  <td className="py-3.5 font-mono text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/50">
                      {incident.service_name}
                    </span>
                  </td>
                  <td className="py-3.5">{getSeverityBadge(incident.severity)}</td>
                  <td className="py-3.5">{getStatusBadge(incident.status)}</td>
                  <td className="py-3.5 text-slate-300 max-w-xs truncate">
                    {incident.mitigation_action || "Autonomous investigation running..."}
                  </td>
                  <td className="py-3.5 pr-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/incidents/${incident.thread_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors"
                        title="Open Live Command Center"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span>Command</span>
                      </Link>
                      <Link
                        href={`/post-mortems/${incident.thread_id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition-colors"
                        title="View Google SRE Post-Mortem"
                      >
                        <FileText className="h-3 w-3" />
                        <span>Report</span>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
