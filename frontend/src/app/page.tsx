"use client";

import React, { useEffect, useState } from "react";
import {
  Clock,
  ShieldCheck,
  Zap,
  TrendingUp,
  RefreshCw,
  AlertOctagon,
  Sparkles,
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
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              SLO 99.99% HEALTHY
            </span>
            <span className="text-xs text-slate-400 font-mono">
              In-VPC Self-Hosted Swarm
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Autonomous SRE Operations Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time observability and supervisor-coordinated response across microservices.
            Mitigates outages in seconds using AST-validated patches and dual HITL review.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-obsidian-850 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
            title="Refresh Incident Stream"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <QuickTriggerModal onSuccess={() => loadData()} />
        </div>
      </div>

      {/* 4 Golden SRE Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Mean Time To Recover (MTTR)"
          value="28s"
          subtitle="From Prometheus alert trigger to circuit breaker & AST patch generation."
          trend="-98.9%"
          trendDirection="up"
          icon={Zap}
          variant="emerald"
        />

        <MetricCard
          title="Mean Time To Detect (MTTD)"
          value="6s"
          subtitle="Real-time log ingestion & correlation by Supervisor Specialist swarm."
          trend="-92.1%"
          trendDirection="up"
          icon={Clock}
          variant="indigo"
        />

        <MetricCard
          title="Cluster SLA Uptime"
          value="99.99%"
          subtitle="P99 SLO error budget intact across payment, auth, and inventory services."
          trend="+0.04%"
          trendDirection="up"
          icon={ShieldCheck}
          variant="sky"
        />

        <MetricCard
          title="Autonomous Resolution"
          value="92.4%"
          subtitle="Incidents resolved without code rewrite or emergency pager escalations."
          trend="+14.2%"
          trendDirection="up"
          icon={TrendingUp}
          variant="amber"
        />
      </div>

      {/* Microservices Swarm Health Map */}
      <ServiceHealthMap />

      {/* Incident Operations Table */}
      <IncidentTable incidents={incidents} onRefresh={loadData} />
    </div>
  );
}
