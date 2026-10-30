"use client";

import React from "react";
import { Server, CheckCircle2, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";

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
    latency: "34ms (P99)",
    uptime: "99.98%",
    activeGuard: "MitigationSpecialist (Circuit Breaker)",
  },
  {
    id: "auth_service",
    name: "auth_service",
    category: "Security & IAM",
    status: "healthy",
    latency: "12ms (P99)",
    uptime: "100.00%",
    activeGuard: "TriageSpecialist (Anomaly Watch)",
  },
  {
    id: "inventory_service",
    name: "inventory_service",
    category: "Catalog & Stock",
    status: "healthy",
    latency: "18ms (P99)",
    uptime: "99.95%",
    activeGuard: "PatchingSpecialist (AST Enforcer)",
  },
  {
    id: "notification_service",
    name: "notification_service",
    category: "Telegram / Alerts",
    status: "healthy",
    latency: "45ms (P99)",
    uptime: "100.00%",
    activeGuard: "ScribeSpecialist (Audit Logging)",
  },
];

export function ServiceHealthMap() {
  return (
    <div className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-white text-base">
              Microservices Swarm Health Map
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time topology monitored by autonomous SRE agents in zero-egress VPC
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            All 4 Clusters Healthy
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {SERVICES.map((srv) => {
          const isMitigated = srv.status === "mitigated";
          const isHealthy = srv.status === "healthy";

          return (
            <div
              key={srv.id}
              className={`rounded-xl border p-4 transition-all duration-200 ${
                isMitigated
                  ? "bg-amber-950/20 border-amber-500/30 hover:border-amber-500/50"
                  : "bg-obsidian-900/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-mono text-sm font-semibold text-white">
                    {srv.name}
                  </h4>
                  <span className="text-[11px] text-slate-400">
                    {srv.category}
                  </span>
                </div>
                {isHealthy ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                )}
              </div>

              <div className="space-y-1.5 text-xs border-t border-slate-800/80 pt-3">
                <div className="flex justify-between text-slate-400">
                  <span>Latency:</span>
                  <span className="font-mono text-slate-200">{srv.latency}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Uptime:</span>
                  <span className="font-mono text-emerald-400">{srv.uptime}</span>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-indigo-400/90 pt-1">
                  <ShieldCheck className="h-3 w-3 shrink-0" />
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
