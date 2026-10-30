"use client";

import React, { useEffect, useState } from "react";
import {
  Clock,
  ShieldCheck,
  Zap,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { ServiceHealthMap } from "@/components/ServiceHealthMap";
import { IncidentTable } from "@/components/IncidentTable";
import { QuickTriggerModal } from "@/components/QuickTriggerModal";
import { fetchIncidents } from "@/lib/api";
import { IncidentItem } from "@/lib/types";

export default function DashboardPage() {
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
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner / Mission Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-hairline">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              CLUSTER SLO 99.99% HEALTHY
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              In-VPC Self-Hosted Swarm
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Autonomous SRE Operations Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
            Real-time multi-agent supervisor coordination across microservices.
            Mitigates outages in seconds using AST-validated patches and dual HITL authorization.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            className="p-1.5 rounded-lg bg-surface-900 border border-hairline text-slate-400 hover:text-white transition-colors"
            title="Refresh Incident Stream"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <QuickTriggerModal onSuccess={() => loadData()} />
        </div>
      </div>

      {/* 4 Golden SRE Metric Cards with Benchmarks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          title="Mean Time To Recover (MTTR)"
          value="28.4s"
          subtitle="Alert trigger to circuit breaker & AST patch generation."
          benchmark="Industry avg: 45 min"
          trend="-98.9%"
          trendDirection="up"
          icon={Zap}
          variant="emerald"
        />

        <MetricCard
          title="Mean Time To Detect (MTTD)"
          value="6.1s"
          subtitle="Real-time log ingestion & correlation by Supervisor swarm."
          benchmark="Industry avg: 15 min"
          trend="-92.1%"
          trendDirection="up"
          icon={Clock}
          variant="indigo"
        />

        <MetricCard
          title="Cluster SLA Availability"
          value="99.992%"
          subtitle="P99 SLO error budget intact across all services."
          benchmark="SLA target: 99.95%"
          trend="+0.04%"
          trendDirection="up"
          icon={ShieldCheck}
          variant="sky"
        />

        <MetricCard
          title="Autonomous Resolution"
          value="92.4%"
          subtitle="Incidents resolved without code rewrite or emergency on-call."
          benchmark="SRE target: > 80%"
          trend="+14.2%"
          trendDirection="up"
          icon={TrendingUp}
          variant="amber"
        />
      </div>

      {/* Microservices Swarm Topology Map */}
      <ServiceHealthMap />

      {/* Incident Operations Stream */}
      <IncidentTable incidents={incidents} onRefresh={loadData} />
    </div>
  );
}
