# Enterprise SRE Web Portal Design Document (Phase 3)

**Date:** 2026-10-31  
**Project:** `incident-response-agent`  
**Status:** In Review (Awaiting Human Partner Approval)  
**Target Architecture:** Next.js 14 Enterprise Web Portal (`frontend/`) communicating with FastAPI Multi-Agent Swarm Backend (`src/`)

---

## 1. Intent & Purpose

Elevate the **Autonomous SRE AI Agent** from a headless backend engine into a commercial-grade, end-to-end **Enterprise SRE Incident Response & Governance Platform**.

While engineers on-call continue to triage and approve emergency patches on mobile via **Telegram Bot**, the **Enterprise Web Portal** provides CTOs, SRE Leads, and Engineering Managers with:
1. **Executive Overview:** Golden SRE metrics (MTTD, MTTR, 99.98% SLA Availability), service health maps, and severity distributions.
2. **Incident Command Center:** Live step-by-step War Room visualizer, AST-verified code diff inspection, and dual-channel Human-in-the-Loop (HITL) approval.
3. **Google SRE Post-Mortem Knowledge Base:** Centralized, searchable, and exportable repository of all historical incident investigations, 5 Whys deductions, and prevention tracking items.

---

## 2. Architecture & System Topology

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         ENTERPRISE WEB PORTAL (Next.js 14)                  │
 │                               (Port 3000)                                   │
 │  ┌───────────────────────┬─────────────────────────┬─────────────────────┐  │
 │  │  Executive Dashboard  │ Incident Command Center │ Post-Mortem Library │  │
 │  │  (SRE Golden Metrics) │ (Live War Room & HITL)  │ (Google SRE Report) │  │
 │  └───────────────────────┴─────────────────────────┴─────────────────────┘  │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ REST API (JSON / HTTP)
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                     BACKEND ENGINE: MULTI-AGENT SWARM                       │
 │                           FastAPI (Port 8000)                               │
 │                                                                             │
 │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
 │  │   Supervisor    │◄──►│ 4 Specialists   │◄──►│ SQLite Checkpointer     │  │
 │  │ (Commander Swarm│    │ (Remediation,   │    │ (data/incidents.db      │  │
 │  │  Circuit Break) │    │  Investigator,  │    │  Multi-Process Sync)    │  │
 │  └────────┬────────┘    │  Patching,      │    └─────────────────────────┘  │
 │           │             │  Scribe)        │                                 │
 │           ▼             └─────────────────┘                                 │
 │     [ HITL Gate ]                                                           │
 │           ▲                                                                 │
 └───────────┼─────────────────────────────────────────────────────────────────┘
             │ Webhook Callbacks
             ▼
 📱 Telegram Bot & Mobile Alerts (Engineers On-Call)
 🌐 GitHub REST API v3 (Branch, PR #1, Prevention Issue)
```

---

## 3. Technology Stack & Design System

* **Framework:** **Next.js 14+ (App Router)** with **TypeScript**.
* **Styling Engine:** **Tailwind CSS** with custom enterprise dark mode palette:
  - Backgrounds: Obsidian (`#0B0F17`), Slate Slate-900 (`#0F172A`), Surface Card (`#1E293B`).
  - Brand Accents: Emerald (`#10B981` - Healthy/Approved), Cyan/Sky (`#0EA5E9` - Investigating/Swarm), Amber (`#F59E0B` - Pending HITL), Rose (`#F43F5E` - Critical P1).
* **Icons:** **Lucide React** (modern, crisp developer-focused icons: `ShieldAlert`, `Terminal`, `Activity`, `CheckCircle2`, `GitPullRequest`, `FileText`, `Flame`).
* **Markdown & Code Rendering:** `react-markdown` + syntax styling for Google SRE Post-Mortem reports and code patches.
* **Component Model:** Modular, reusable UI components (`MetricCard`, `IncidentTable`, `TimelineVisualizer`, `CodePatchViewer`, `PostMortemViewer`).

---

## 4. Detailed Screen Specifications

### 4.1 Executive Dashboard (`/`)
* **Header & Status Bar:** Global system health badge (*"All Autonomous Systems Operational"*), Swarm iteration engine indicator, active SQLite checkpointer connection.
* **Golden SRE Metric Cards:**
  1. **Mean Time to Recovery (MTTR):** Average time from alert ingestion to mitigation / fix (~32 seconds).
  2. **Mean Time to Detect (MTTD):** Average time to triage & deduce root cause (~8 seconds).
  3. **Availability SLA:** Simulated uptime percentage (`99.98%`).
  4. **Incidents Resolved:** Total count grouped by severity (`P1 Critical`, `P2 High`, `P3 Medium`).
* **Active Incidents Table:** Real-time list of incidents with:
  - Thread ID (e.g. `INC-PROD-001`)
  - Target Service (`payment_service`, `auth_service`, `order_service`)
  - Severity badge with pulse dot (`P1` red, `P2` orange, `P3` yellow)
  - Mitigation Status (`Rolled back`, `Restarted`, `Rate-limited`)
  - Approval Status (`pending`, `approved`, `revising`, `rejected`)
  - One-click navigation to detail view.
* **Quick Incident Simulator:** Button to dispatch a test incident directly from the web interface for demonstration purposes.

### 4.2 Incident Live Command Center (`/incidents/[id]`)
* **Header:** Incident ID, service name, severity, creation timestamp, GitHub PR badge (link to real PR on `github.com`).
* **Interactive War Room Timeline:**
  - Visual vertical step-by-step tracker showing each completed stage:
    1. 🚨 **Triage:** Severity classification.
    2. 🚒 **Remediation Specialist:** Emergency mitigation executed & War Room alert sent.
    3. 🔍 **Investigator Specialist:** Log analysis & 5 Whys RCA.
    4. 🛠️ **Patching Specialist:** Safe code synthesized with AST syntax validation badge (`Passed ✅`).
    5. 🚪 **HITL Gate:** Current pause state or human decision recorded.
    6. 📋 **Scribe Specialist:** PR created & Google SRE Post-Mortem filed.
* **Proposed Code Patch Card:**
  - Syntax-highlighted code block.
  - Reviewer feedback input box for iterative refinement (`Human Feedback Loop`).
* **HITL Action Bar:**
  - `[✅ Approve & Open GitHub PR]` (Triggers backend resumption, opens PR, and compiles Post-Mortem).
  - `[🔄 Request Revision with Feedback]` (Revises patch via supervisor loop).
  - `[❌ Reject Fix]` (Cancels patch execution).

### 4.3 Google SRE Post-Mortem Knowledge Base (`/post-mortems` & `/post-mortems/[id]`)
* **Incident Archive:** Searchable catalog of all historical resolved incidents.
* **Document Viewer:**
  - Formatted Google SRE Post-Mortem layout:
    - Executive Summary & Service Impact.
    - MTTD and MTTR metrics.
    - Verified Chronological Timeline table.
    - 5 Whys Root Cause Analysis.
    - Prevention Action Items & GitHub Issue tracking link.
* **Actions:**
  - **Copy Markdown** to clipboard.
  - **Print / Save as PDF** styling.

---

## 5. API Client Integration Layer (`lib/api.ts`)

The Next.js frontend interacts with the FastAPI backend via clean typed client functions:

```typescript
export interface Incident {
  thread_id: string;
  service_name: string;
  severity: "P1" | "P2" | "P3";
  status: "processing" | "paused_at_breakpoint" | "approved" | "rejected" | "escalated";
  mitigation_action?: string;
  timeline?: Array<{ time: string; event: string; stage: string }>;
  proposed_fix?: string;
  github_pr_url?: string;
  post_mortem_report?: string;
}

// Client Methods
export async function getIncidents(): Promise<Incident[]>;
export async function getIncidentStatus(threadId: string): Promise<Incident>;
export async function getIncidentPostMortem(threadId: string): Promise<string>;
export async function approveIncident(threadId: string, approved: boolean, feedback?: string): Promise<any>;
export async function triggerIncident(serviceName: string, issueDescription: string): Promise<any>;
```

---

## 6. Deployment & Containerization Strategy

Update `docker-compose.yml` to orchestrate both Backend and Frontend:
* **`backend` service:** Python 3.10 FastAPI (port 8000) with `./data` volume.
* **`frontend` service:** Node.js Next.js production build (port 3000) with `NEXT_PUBLIC_API_URL=http://backend:8000`.
* Both services run on the same Docker network with auto-restart.

---

## 7. Verification & Acceptance Criteria

1. **Build Integrity:** `npm run build` inside `frontend/` succeeds with 0 TypeScript/ESLint errors.
2. **Backend Zero-Regression:** Full pytest suite (`pytest tests/ -v`) passes 59/59 tests (100%).
3. **End-to-End Operational Flow:**
   - User triggers incident on Web or Telegram.
   - Web shows real-time timeline progressing to `hitl_gate`.
   - Clicking `[Approve]` on Web opens real GitHub PR, generates Post-Mortem, and marks status completed.
   - Clicking `[Approve]` on Telegram reflects instantaneously on the Web Portal.
