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
  Loader2,
} from "lucide-react";
import { IncidentItem, IncidentSeverity } from "@/lib/types";

interface IncidentTableProps {
  incidents: IncidentItem[];
  onRefresh?: () => void;
}

export function IncidentTable({ incidents }: IncidentTableProps) {
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
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            P0 CRITICAL
          </span>
        );
      case "P1":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            P1 HIGH
          </span>
        );
      case "P2":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">
            P2 MEDIUM
          </span>
        );
      case "P3":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-sky-500/15 text-sky-400 border border-sky-500/30">
            P3 LOW
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-surface-800 text-slate-400 border border-hairline">
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
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3" />
            Resolved
          </span>
        );
      case "paused_at_breakpoint":
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
            <Clock className="h-3 w-3" />
            Awaiting HITL
          </span>
        );
      case "escalated":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-3 w-3" />
            Escalated
          </span>
        );
      case "processing":
      case "active":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Loader2 className="h-3 w-3 animate-spin" />
            Investigating
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <ShieldAlert className="h-3 w-3" />
            {status || "Active"}
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="font-semibold text-white text-sm">
            Autonomous Incident Stream
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Checkpointed operations recorded in local SQLite with WAL persistence
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Search Input with hotkey hint */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search thread or service..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-60 pl-8 pr-8 py-1 rounded-lg bg-surface-850 border border-hairline text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/60"
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 kbd-cap">/</span>
          </div>

          {/* Severity Filter Tabs */}
          <div className="flex items-center bg-surface-850 rounded-lg p-0.5 border border-hairline">
            {["ALL", "P0", "P1", "P2", "P3"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium transition-colors ${
                  severityFilter === sev
                    ? "bg-surface-700 text-white"
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
            <tr className="border-b border-hairline text-slate-400 font-medium text-[11px]">
              <th className="pb-2.5 pl-2 font-mono">THREAD ID</th>
              <th className="pb-2.5">SERVICE</th>
              <th className="pb-2.5">SEVERITY</th>
              <th className="pb-2.5">STATE</th>
              <th className="pb-2.5">MITIGATION ACTION</th>
              <th className="pb-2.5 pr-2 text-right">CONTROLS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-hairline">
            {filteredIncidents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                  No incidents matching search criteria found.
                </td>
              </tr>
            ) : (
              filteredIncidents.map((incident) => (
                <tr
                  key={incident.thread_id}
                  className="hover:bg-surface-850/40 transition-colors group"
                >
                  <td className="py-3 pl-2 font-mono font-semibold text-white">
                    <Link
                      href={`/incidents/${incident.thread_id}`}
                      className="hover:text-indigo-400 transition-colors"
                    >
                      {incident.thread_id}
                    </Link>
                  </td>
                  <td className="py-3 font-mono text-slate-300">
                    <span className="px-1.5 py-0.5 rounded bg-surface-800 text-[11px] border border-hairline">
                      {incident.service_name}
                    </span>
                  </td>
                  <td className="py-3">{getSeverityBadge(incident.severity)}</td>
                  <td className="py-3">{getStatusBadge(incident.status)}</td>
                  <td className="py-3 text-slate-300 max-w-xs truncate text-[11px]">
                    {incident.mitigation_action || "Investigation running..."}
                  </td>
                  <td className="py-3 pr-2 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Link
                        href={`/incidents/${incident.thread_id}`}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors text-[11px]"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span>Command</span>
                      </Link>
                      <Link
                        href={`/post-mortems/${incident.thread_id}`}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-800 text-slate-300 border border-hairline hover:bg-surface-700 transition-colors text-[11px]"
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
