"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, ShieldCheck, Terminal, BookOpen, Send, CheckCircle2, AlertCircle } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      const ok = await checkBackendHealth();
      if (isMounted) setBackendOnline(ok);
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 12000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { href: "/", label: "Executive Dashboard", icon: Activity },
    { href: "/incidents/INC-PROD-001", label: "War Room Center", icon: Terminal },
    { href: "/post-mortems", label: "Post-Mortem KB", icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-surface-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Brand & Platform Identity */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="h-8 w-8 rounded-lg bg-surface-850 border border-hairline flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/40 transition-colors">
                <ShieldCheck className="h-4.5 w-4.5 text-indigo-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                    SRE SWARM
                  </span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-850 text-slate-400 border border-hairline font-mono">
                    v2.1
                  </span>
                </div>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href.split("/")[1] ? `/${item.href.split("/")[1]}` : item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-surface-850 text-white border border-hairline shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-surface-900"
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Live System & Bot Status */}
          <div className="flex items-center gap-2.5">
            {/* Telegram HITL Badge */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-900 border border-hairline text-sky-400 text-[11px] font-mono">
              <Send className="h-3 w-3" />
              <span>Telegram HITL Active</span>
            </div>

            {/* Backend Swarm Health Indicator */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono border ${
                backendOnline === null
                  ? "bg-surface-900 text-slate-400 border-hairline"
                  : backendOnline
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }`}
            >
              <div
                className={`h-1.5 w-1.5 rounded-full ${
                  backendOnline === null
                    ? "bg-slate-500"
                    : backendOnline
                    ? "bg-emerald-400 animate-pulse"
                    : "bg-amber-400"
                }`}
              />
              <span className="hidden sm:inline">
                {backendOnline === null
                  ? "Connecting..."
                  : backendOnline
                  ? "Swarm Online"
                  : "Demo Standby"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
