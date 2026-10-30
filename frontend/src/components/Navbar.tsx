"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, ShieldCheck, Terminal, BookOpen, Radio, Send } from "lucide-react";
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
    const interval = setInterval(verifyHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { href: "/", label: "Executive Dashboard", icon: Activity },
    { href: "/incidents/INC-PROD-001", label: "Command Center", icon: Terminal },
    { href: "/post-mortems", label: "Post-Mortem KB", icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-obsidian-900/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <ShieldCheck className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg tracking-tight text-white group-hover:text-indigo-400 transition-colors">
                    SRE SWARM
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                    v2.1 Enterprise
                  </span>
                </div>
                <p className="text-xs text-slate-400 hidden sm:block">
                  Autonomous Multi-Agent Incident Response
                </p>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
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
                  className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden md:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Live System & Bot Status */}
          <div className="flex items-center gap-3">
            {/* Telegram HITL Badge */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono">
              <Send className="h-3 w-3" />
              <span>Telegram HITL Active</span>
            </div>

            {/* Backend Swarm Health Indicator */}
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono border ${
                backendOnline === null
                  ? "bg-slate-800 text-slate-400 border-slate-700"
                  : backendOnline
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/30"
              }`}
            >
              <div
                className={`h-2 w-2 rounded-full ${
                  backendOnline === null
                    ? "bg-slate-500"
                    : backendOnline
                    ? "bg-emerald-400 animate-pulse-slow shadow-sm shadow-emerald-400"
                    : "bg-amber-400"
                }`}
              />
              <span className="hidden sm:inline">
                {backendOnline === null
                  ? "Connecting..."
                  : backendOnline
                  ? "FastAPI Swarm Online"
                  : "Standby / Demo Mode"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
