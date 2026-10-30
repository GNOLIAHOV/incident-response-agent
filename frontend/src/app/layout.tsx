import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "SRE SWARM | Enterprise Autonomous Incident Response",
  description:
    "Executive Command Center & Multi-Agent Autonomous SRE Swarm for Production Infrastructure",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="dark">
      <body className="min-h-screen bg-obsidian-900 text-slate-100 flex flex-col antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800 bg-obsidian-950/80 py-6 text-xs text-slate-500 text-center">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block"></span>
              <span>Enterprise In-VPC SRE Cluster Active</span>
              <span className="text-slate-600">|</span>
              <span>Zero-Egress AST Enforcement</span>
            </div>
            <div>
              <span>SRE Swarm Multi-Agent Architecture © 2026. All rights reserved.</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
