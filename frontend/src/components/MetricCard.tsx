"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  icon: LucideIcon;
  variant?: "emerald" | "indigo" | "sky" | "amber" | "rose";
}

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendDirection = "up",
  icon: Icon,
  variant = "indigo",
}: MetricCardProps) {
  const variantStyles = {
    emerald: {
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
      text: "text-emerald-400",
      glow: "hover:shadow-emerald-500/10",
    },
    indigo: {
      bg: "bg-indigo-500/10",
      border: "border-indigo-500/20",
      text: "text-indigo-400",
      glow: "hover:shadow-indigo-500/10",
    },
    sky: {
      bg: "bg-sky-500/10",
      border: "border-sky-500/20",
      text: "text-sky-400",
      glow: "hover:shadow-sky-500/10",
    },
    amber: {
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
      text: "text-amber-400",
      glow: "hover:shadow-amber-500/10",
    },
    rose: {
      bg: "bg-rose-500/10",
      border: "border-rose-500/20",
      text: "text-rose-400",
      glow: "hover:shadow-rose-500/10",
    },
  }[variant];

  return (
    <div
      className={`rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 backdrop-blur-sm transition-all duration-300 hover:border-slate-700 hover:shadow-xl ${variantStyles.glow}`}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
          {title}
        </span>
        <div
          className={`h-10 w-10 rounded-xl ${variantStyles.bg} ${variantStyles.border} border flex items-center justify-center`}
        >
          <Icon className={`h-5 w-5 ${variantStyles.text}`} />
        </div>
      </div>

      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-3xl font-extrabold tracking-tight text-white font-mono">
          {value}
        </span>
        {trend && (
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              trendDirection === "up"
                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                : trendDirection === "down"
                ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                : "bg-slate-700 text-slate-300"
            }`}
          >
            {trend}
          </span>
        )}
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">{subtitle}</p>
    </div>
  );
}
