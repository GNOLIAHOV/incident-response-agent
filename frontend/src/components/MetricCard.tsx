"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  benchmark?: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  icon: LucideIcon;
  variant?: "emerald" | "indigo" | "sky" | "amber" | "rose";
}

export function MetricCard({
  title,
  value,
  subtitle,
  benchmark,
  trend,
  trendDirection = "up",
  icon: Icon,
  variant = "indigo",
}: MetricCardProps) {
  const signalColor = {
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    indigo: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    sky: "text-sky-400 bg-sky-500/10 border-sky-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    rose: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  }[variant];

  return (
    <div className="rounded-xl bg-surface-900 border border-hairline p-5 transition-colors duration-150 hover:border-slate-700/80">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          {title}
        </span>
        <div className={`p-1.5 rounded-lg border ${signalColor}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2 mb-2">
        <span className="text-3xl font-bold tracking-tight text-white font-mono tabular-nums">
          {value}
        </span>
        {trend && (
          <span
            className={`text-[11px] font-mono font-medium px-2 py-0.5 rounded-md ${
              trendDirection === "up"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : trendDirection === "down"
                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                : "bg-surface-800 text-slate-400"
            }`}
          >
            {trend}
          </span>
        )}
      </div>

      <div className="space-y-1 pt-1 border-t border-hairline">
        <p className="text-[11px] text-slate-400 leading-normal line-clamp-2">
          {subtitle}
        </p>
        {benchmark && (
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
            <span>Benchmark:</span>
            <span className="text-slate-400">{benchmark}</span>
          </div>
        )}
      </div>
    </div>
  );
}
