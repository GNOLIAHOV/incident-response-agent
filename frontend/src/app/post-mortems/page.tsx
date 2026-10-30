"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BookOpen,
  Search,
  FileText,
  Clock,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { fetchIncidents } from "@/lib/api";

interface CatalogItem {
  id: string;
  service: string;
  severity: "P0" | "P1" | "P2";
  date: string;
  mttr: string;
  title: string;
  summary: string;
}

const FALLBACK_POST_MORTEMS: CatalogItem[] = [
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
  const [items, setItems] = useState<CatalogItem[]>(FALLBACK_POST_MORTEMS);

  useEffect(() => {
    fetchIncidents().then((incidentList) => {
      const resolved = incidentList.filter(
        (i) => i.status === "completed" || i.status === "approved"
      );

      if (resolved.length > 0) {
        const dynamicItems: CatalogItem[] = resolved.map((inc) => ({
          id: inc.thread_id,
          service: inc.service_name || "service",
          severity: (inc.severity as "P0" | "P1" | "P2") || "P2",
          date: inc.created_at ? inc.created_at.split("T")[0] : "2026-10-31",
          mttr: "28s",
          title: `Google SRE Post-Mortem: ${inc.service_name} Remediation`,
          summary:
            inc.mitigation_action ||
            "Full Google SRE Post-Mortem compiled with 5 Whys Root Cause Analysis and automated GitHub Pull Request dispatch.",
        }));
        setItems(dynamicItems);
      }
    });
  }, []);

  const filtered = items.filter(
    (item) =>
      item.id.toLowerCase().includes(search.toLowerCase()) ||
      item.service.toLowerCase().includes(search.toLowerCase()) ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.summary.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-hairline">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BookOpen className="h-4 w-4 text-indigo-400" />
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Google SRE Post-Mortem Knowledge Base
            </h1>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl">
            Autonomous post-incident documentation generated following Google's Blameless Post-Mortem framework.
            Institutional memory automatically preserved for architectural hardening.
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search post-mortems..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-64 pl-8 pr-3 py-1.5 rounded-lg bg-surface-900 border border-hairline text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/60"
          />
        </div>
      </div>

      {/* Catalog Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="rounded-xl bg-surface-900 border border-hairline p-5 flex flex-col justify-between hover:border-slate-700 transition-colors group"
          >
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <span className="font-mono text-xs font-bold text-white px-2 py-0.5 rounded bg-surface-850 border border-hairline">
                  {item.id}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
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

              <h3 className="font-semibold text-white text-sm mb-1.5 group-hover:text-indigo-300 transition-colors">
                {item.title}
              </h3>

              <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-3 mb-3">
                {item.summary}
              </p>
            </div>

            <div className="pt-3 border-t border-hairline flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[11px]">
                <Clock className="h-3 w-3 text-emerald-400" />
                <span>MTTR: {item.mttr}</span>
              </div>

              <Link
                href={`/post-mortems/${item.id}`}
                className="inline-flex items-center gap-1 font-semibold text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <span>Read Report</span>
                <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PostMortemsCatalogPage;
