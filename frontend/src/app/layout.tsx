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
      <body className="min-h-screen bg-canvas text-slate-100 flex flex-col antialiased selection:bg-indigo-500/20 selection:text-indigo-200">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-hairline bg-surface-950 py-4 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] font-mono">
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block"></span>
              <span>Enterprise In-VPC SRE Cluster Active</span>
              <span className="text-slate-700">|</span>
              <span>Zero-Egress AST Enforcer</span>
            </div>
            <div>
              <span>SRE Swarm Multi-Agent Architecture © 2026.</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
