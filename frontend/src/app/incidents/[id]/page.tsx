"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  FileText,
  AlertTriangle,
  Flame,
  Radio,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { fetchIncidentStatus } from "@/lib/api";
import { IncidentDetail } from "@/lib/types";
import { TimelineVisualizer } from "@/components/TimelineVisualizer";
import { CodePatchViewer } from "@/components/CodePatchViewer";
import { HITLActionBar } from "@/components/HITLActionBar";

export default function IncidentCommandCenter() {
  const params = useParams();
  const threadId = (params?.id as string) || "INC-PROD-001";

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadStatus = async () => {
    try {
      const data = await fetchIncidentStatus(threadId);
      setIncident(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    // Poll every 3 seconds if actively processing or awaiting HITL
    const interval = setInterval(() => {
      loadStatus();
    }, 3000);
    return () => clearInterval(interval);
  }, [threadId]);

  const severity = incident?.severity || "P0";
  const isPaused = incident?.is_paused || false;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Breadcrumb */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Dashboard</span>
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-mono text-indigo-400 font-semibold">
              War Room Command Center
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white font-mono tracking-tight">
              {threadId}
            </h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                severity === "P0"
                  ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                  : severity === "P1"
                  ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                  : "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
              }`}
            >
              {severity} SEVERITY
            </span>
            <span className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
              Target: {incident?.service_name || "payment_service"}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={loadStatus}
            className="p-2.5 rounded-xl bg-obsidian-850 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh State Checkpoint"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>

          <Link
            href={`/post-mortems/${threadId}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-md shadow-indigo-600/20"
          >
            <FileText className="h-4 w-4" />
            <span>Google SRE Post-Mortem</span>
          </Link>
        </div>
      </div>

      {/* Overview Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-obsidian-850/80 border border-slate-800 p-4">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Radio className="h-4 w-4 text-emerald-400" />
            <span>Active Remediation Action</span>
          </div>
          <p className="text-sm font-semibold text-white font-mono truncate">
            {incident?.mitigation_action_taken || "Investigation in progress..."}
          </p>
        </div>

        <div className="rounded-xl bg-obsidian-850/80 border border-slate-800 p-4">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <ShieldCheck className="h-4 w-4 text-indigo-400" />
            <span>Approval Lifecycle</span>
          </div>
          <p className="text-sm font-semibold text-white font-mono uppercase">
            {incident?.approval_status || "Pending Verification"}
          </p>
        </div>

        <div className="rounded-xl bg-obsidian-850/80 border border-slate-800 p-4">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Flame className="h-4 w-4 text-rose-400" />
            <span>Swarm Execution Status</span>
          </div>
          <p className="text-sm font-semibold text-white font-mono uppercase">
            {incident?.status || "Processing"}
          </p>
        </div>
      </div>

      {/* Main Grid: Left = Timeline, Right = Code & HITL */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Multi-Agent Timeline */}
        <div className="lg:col-span-5 space-y-6">
          <TimelineVisualizer
            timeline={incident?.timeline}
            currentStatus={incident?.status || "processing"}
          />
        </div>

        {/* Right Column (7 cols): Code Patch & HITL Action Bar */}
        <div className="lg:col-span-7 space-y-6">
          <CodePatchViewer
            patchCode={incident?.proposed_fix}
            serviceName={incident?.service_name}
            isPaused={isPaused}
          />

          <HITLActionBar
            threadId={threadId}
            isPaused={isPaused}
            approvalStatus={incident?.approval_status}
            onDecisionSubmitted={loadStatus}
          />
        </div>
      </div>
    </div>
  );
}
