"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Search,
  FileText,
  Clock,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

interface CatalogItem {
  id: string;
  service: string;
  severity: "P0" | "P1" | "P2";
  date: string;
  mttr: string;
  title: string;
  summary: string;
}

const POST_MORTEMS: CatalogItem[] = [
  {
    id: "INC-PROD-001",
    service: "payment_service",
    severity: "P0",
    date: "2026-10-31",
    mttr: "28s",
    title: "Cascading 504 Gateway Timeouts During Peak Traffic",
    summary:
      "Socket pool starvation caused downstream checkout transactions to fail. Remediation Specialist triggered circuit breaker while Patching Specialist inserted safe timeout AST patch.",
  },
  {
    id: "INC-AUTH-882",
    service: "auth_service",
    severity: "P1",
    date: "2026-10-30",
    mttr: "35s",
    title: "JWT Token Signature Verification Loop",
    summary:
      "Infinite verification retry loop pinned CPU usage at 95%. Automated cache invalidation and token refresh patch safely mitigated the issue.",
  },
  {
    id: "INC-INV-109",
    service: "inventory_service",
    severity: "P2",
    date: "2026-10-29",
    mttr: "19s",
    title: "Postgres Connection Pool Exhaustion",
    summary:
      "Connection leaks during stock validation drained connection pool. Swarm automatically scaled the pool size and generated a connection context manager fix.",
  },
];

function PostMortemsCatalogPage() {
  const [search, setSearch] = useState("");

  const filtered = POST_MORTEMS.filter(
    (item) =>
      item.id.toLowerCase().includes(search.toLowerCase()) ||
      item.service.toLowerCase().includes(search.toLowerCase()) ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.summary.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BookOpen className="h-5 w-5 text-indigo-400" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Google SRE Post-Mortem Knowledge Base
            </h1>
          </div>
          <p className="text-sm text-slate-400 max-w-2xl">
            Autonomous post-incident documentation generated following Google's Blameless Post-Mortem framework.
            Institutional memory automatically preserved for architectural hardening.
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search post-mortems..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-72 pl-9 pr-4 py-2 rounded-xl bg-obsidian-850 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="rounded-2xl bg-obsidian-850/80 border border-slate-800 p-6 flex flex-col justify-between hover:border-slate-700 transition-all hover:shadow-xl hover:shadow-indigo-500/5 group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs font-bold text-white px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700">
                  {item.id}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold ${
                    item.severity === "P0"
                      ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                      : item.severity === "P1"
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      : "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30"
                  }`}
                >
                  {item.severity}
                </span>
              </div>

              <h3 className="font-semibold text-white text-base mb-2 group-hover:text-indigo-400 transition-colors">
                {item.title}
              </h3>

              <p className="text-xs text-slate-400 leading-relaxed line-clamp-3 mb-4">
                {item.summary}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-slate-500 font-mono">
                <Clock className="h-3.5 w-3.5 text-emerald-400" />
                <span>MTTR: {item.mttr}</span>
              </div>

              <Link
                href={`/post-mortems/${item.id}`}
                className="inline-flex items-center gap-1 font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <span>Read Report</span>
                <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PostMortemsCatalogPage;
