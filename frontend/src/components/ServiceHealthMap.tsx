"use client";

import React from "react";
import { Server, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

interface ServiceItem {
  id: string;
  name: string;
  category: string;
  status: "healthy" | "mitigated" | "investigating";
  latency: string;
  uptime: string;
  activeGuard: string;
}

const SERVICES: ServiceItem[] = [
  {
    id: "payment_service",
    name: "payment_service",
    category: "Financial Gateway",
    status: "mitigated",
    latency: "34ms",
    uptime: "99.98%",
    activeGuard: "MitigationSpecialist",
  },
  {
    id: "auth_service",
    name: "auth_service",
    category: "Security & IAM",
    status: "healthy",
    latency: "12ms",
    uptime: "100.00%",
    activeGuard: "TriageSpecialist",
  },
  {
    id: "inventory_service",
    name: "inventory_service",
    category: "Catalog & Stock",
    status: "healthy",
    latency: "18ms",
    uptime: "99.95%",
    activeGuard: "PatchingSpecialist",
  },
  {
    id: "notification_service",
    name: "notification_service",
    category: "Telegram / Alerts",
    status: "healthy",
    latency: "45ms",
    uptime: "100.00%",
    activeGuard: "ScribeSpecialist",
  },
];

export function ServiceHealthMap() {
  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-indigo-400" />
            <h3 className="font-semibold text-white text-sm">
              Microservices Cluster Topology
            </h3>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Active telemetry monitored by LangGraph Supervisor Swarm in zero-egress VPC
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-md border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            All 4 Nodes Operational
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {SERVICES.map((srv) => {
          const isMitigated = srv.status === "mitigated";
          const isHealthy = srv.status === "healthy";

          return (
            <div
              key={srv.id}
              className={`rounded-lg border p-3.5 transition-colors duration-150 ${
                isMitigated
                  ? "bg-amber-950/20 border-amber-500/30"
                  : "bg-surface-850/60 border-hairline hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between mb-2.5">
                <div>
                  <h4 className="font-mono text-xs font-bold text-white">
                    {srv.name}
                  </h4>
                  <span className="text-[10px] text-slate-400 block">
                    {srv.category}
                  </span>
                </div>
                {isHealthy ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                )}
              </div>

              <div className="space-y-1 text-[11px] border-t border-hairline pt-2">
                <div className="flex justify-between text-slate-400">
                  <span>P99 Latency:</span>
                  <span className="font-mono tabular-nums text-slate-200">{srv.latency}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Availability:</span>
                  <span className="font-mono tabular-nums text-emerald-400">{srv.uptime}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-indigo-400/90 pt-1 font-mono">
                  <span>Guarded by:</span>
                  <span className="truncate">{srv.activeGuard}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
