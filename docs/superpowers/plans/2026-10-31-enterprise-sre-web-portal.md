# Enterprise SRE Web Portal Implementation Plan (Phase 3)

**Date:** 2026-10-31  
**Spec Reference:** [`docs/superpowers/specs/2026-10-31-enterprise-sre-web-portal-design.md`](file:///D:/Projects/incident-response-agent/docs/superpowers/specs/2026-10-31-enterprise-sre-web-portal-design.md)  
**Target Directory:** `frontend/`  
**Backend Reference:** `src/api/app.py` (`http://localhost:8000`)

---

## 1. Plan Overview & Architectural Decisions

This implementation plan delivers a modern, production-ready **Enterprise SRE Web Portal** built with **Next.js 14 App Router, TypeScript, and Tailwind CSS**.

The portal communicates directly with our existing FastAPI backend:
* `GET /incidents` -> Lists all active and historical incidents.
* `GET /incidents/{thread_id}/status` -> Polls live incident state, timeline, AST-validated fix, and pause status.
* `GET /incidents/{thread_id}/post-mortem` -> Fetches complete Google SRE Post-Mortem markdown.
* `POST /incidents/{thread_id}/approve` -> Sends approval / rejection / revision decisions.
* `POST /incidents/trigger` -> Dispatches new emergency incidents.

The backend Multi-Agent Swarm remains completely intact with 100% test pass rate (59/59 tests).

---

## 2. File Structure Map

```text
frontend/
├── Dockerfile                      # Standalone multi-stage Next.js production build
├── .dockerignore
├── .env.local                      # NEXT_PUBLIC_API_URL=http://localhost:8000
├── package.json                    # Next.js 14, React 18, Lucide React, Tailwind
├── tsconfig.json                   # Strict TypeScript configuration
├── tailwind.config.ts              # Custom SRE dark mode theme tokens (Obsidian, Emerald, Rose)
├── postcss.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root Layout (Nav, Global Header, Theme provider)
│   │   ├── page.tsx                # Page 1: Executive CTO Dashboard (Golden Metrics, Service Map)
│   │   ├── incidents/
│   │   │   └── [id]/
│   │   │       └── page.tsx        # Page 2: Incident Command Center (War Room Timeline, Patch Diff, HITL)
│   │   ├── post-mortems/
│   │   │   ├── page.tsx            # Page 3: Post-Mortem Knowledge Base Catalog
│   │   │   └── [id]/
│   │   │       └── page.tsx        # Post-Mortem Reader & Export Document
│   │   └── globals.css             # Tailwind imports & custom scrollbar / theme CSS
│   ├── components/
│   │   ├── Navbar.tsx              # Enterprise top navigation & status indicator
│   │   ├── MetricCard.tsx          # Golden SRE metric card (MTTR, MTTD, SLA, Count)
│   │   ├── ServiceHealthMap.tsx    # Live operational status of microservices
│   │   ├── IncidentTable.tsx       # Filterable table with severity badges
│   │   ├── TimelineVisualizer.tsx  # Step-by-step War Room progression tracker
│   │   ├── CodePatchViewer.tsx     # AST-validated syntax highlighted patch viewer
│   │   ├── HITLActionBar.tsx       # Dual-channel approve/reject/feedback action bar
│   │   ├── PostMortemViewer.tsx    # Google SRE Post-Mortem Markdown renderer
│   │   └── QuickTriggerModal.tsx   # Modal to dispatch live simulated incident
│   └── lib/
│       ├── api.ts                  # Typed client interacting with FastAPI backend
│       └── types.ts                # TypeScript interfaces (Incident, State, PostMortem)
```

---

## 3. Step-by-Step Task Decomposition

### Task 1: Scaffolding the Next.js 14 TypeScript Project in `frontend/`
* **Files:**
  - `frontend/package.json`
  - `frontend/tsconfig.json`
  - `frontend/tailwind.config.ts`
  - `frontend/postcss.config.js`
  - `frontend/.env.local`
  - `frontend/.gitignore`
* **Actions:**
  1. Define dependencies: `next`, `react`, `react-dom`, `lucide-react`, `tailwindcss`, `postcss`, `autoprefixer`, `typescript`, `@types/react`, `@types/node`.
  2. Configure Tailwind with dark mode palette (Obsidian `#0B0F17`, Slate `#0F172A`, Surface `#1E293B`, Emerald `#10B981`, Rose `#F43F5E`).
  3. Run `npm install` inside `frontend/`.
* **Verification:** `npm run build` or Next.js CLI loads without error.

---

### Task 2: Type Contracts & API Client Layer
* **Files:**
  - `frontend/src/lib/types.ts`
  - `frontend/src/lib/api.ts`
* **Actions:**
  1. Define TypeScript contracts matching FastAPI Pydantic schemas:
     - `IncidentItem`, `IncidentDetail`, `TimelineEvent`, `PostMortemData`, `ApprovalPayload`.
  2. Implement client functions with fallback mode (returns mock data if backend server is unreachable during isolated frontend preview):
     - `fetchIncidents()`
     - `fetchIncidentStatus(threadId)`
     - `fetchPostMortem(threadId)`
     - `submitApproval(threadId, approved, feedback)`
     - `triggerNewIncident(serviceName, issueDesc)`
* **Verification:** Unit test or node script verifying API client serialization.

---

### Task 3: Design System Foundation & Global Layout
* **Files:**
  - `frontend/src/app/globals.css`
  - `frontend/src/components/Navbar.tsx`
  - `frontend/src/app/layout.tsx`
* **Actions:**
  1. Setup dark background `#0B0F17`, modern typography, and clean contrast.
  2. Build `Navbar.tsx` with logo, active link indicators, and live backend connection pulse dot (Emerald = Connected, Amber = Disconnected/Offline).
  3. Create Root Layout wrapping all pages.
* **Verification:** Render layout and verify no hydration mismatch.

---

### Task 4: Executive CTO Dashboard (`frontend/src/app/page.tsx`)
* **Files:**
  - `frontend/src/components/MetricCard.tsx`
  - `frontend/src/components/ServiceHealthMap.tsx`
  - `frontend/src/components/IncidentTable.tsx`
  - `frontend/src/components/QuickTriggerModal.tsx`
  - `frontend/src/app/page.tsx`
* **Actions:**
  1. Build `MetricCard.tsx`: Displays MTTR (~30s), MTTD (~8s), 99.98% SLA, Total Incidents.
  2. Build `ServiceHealthMap.tsx`: Operational badges for `payment_service`, `auth_service`, `inventory_service`.
  3. Build `IncidentTable.tsx`: Live list with Severity indicators, status pills, mitigation actions taken, and links to detail views.
  4. Build `QuickTriggerModal.tsx`: Allows users/CTOs to trigger a demo incident directly from the browser.
* **Verification:** Verify dashboard renders all metrics, handles empty states, and triggers incidents cleanly.

---

### Task 5: Incident Command Center (`frontend/src/app/incidents/[id]/page.tsx`)
* **Files:**
  - `frontend/src/components/TimelineVisualizer.tsx`
  - `frontend/src/components/CodePatchViewer.tsx`
  - `frontend/src/components/HITLActionBar.tsx`
  - `frontend/src/app/incidents/[id]/page.tsx`
* **Actions:**
  1. Build `TimelineVisualizer.tsx`: Step-by-step interactive timeline matching the multi-agent swarm stages (`triage` -> `remediation` -> `investigator` -> `patching` -> `hitl_gate` -> `scribe`).
  2. Build `CodePatchViewer.tsx`: Syntax highlighted code block with AST Validation Passed badge.
  3. Build `HITLActionBar.tsx`: Buttons for `[✅ Approve & Open PR]`, `[🔄 Request Revision with Feedback]`, `[❌ Reject]`. When clicked, calls `POST /incidents/{id}/approve`.
* **Verification:** Test navigating to an incident (e.g. `INC-PROD-001`), approving, and seeing status transition.

---

### Task 6: Google SRE Post-Mortem Knowledge Base (`frontend/src/app/post-mortems/`)
* **Files:**
  - `frontend/src/components/PostMortemViewer.tsx`
  - `frontend/src/app/post-mortems/page.tsx`
  - `frontend/src/app/post-mortems/[id]/page.tsx`
* **Actions:**
  1. Build Catalog view (`/post-mortems`) listing all past resolved incidents with MTTR/MTTD tags.
  2. Build Detail view (`/post-mortems/[id]`) with clean markdown formatting:
     - 5 Whys Deduction, Timeline table, Action Items.
     - Export to Markdown button (copies clean markdown to clipboard).
* **Verification:** Verify markdown parsing of real post-mortem reports saved in SQLite database.

---

### Task 7: Dockerfile & Multi-Container Docker Compose Integration
* **Files:**
  - `frontend/Dockerfile`
  - `docker-compose.yml`
* **Actions:**
  1. Create multi-stage `frontend/Dockerfile` using Node.js Alpine base.
  2. Update `docker-compose.yml` to define two services:
     - `backend`: port 8000
     - `frontend`: port 3000
  3. Set environment variable `NEXT_PUBLIC_API_URL=http://localhost:8000`.
* **Verification:** `docker compose config` validates schema.

---

### Task 8: End-to-End Audit & Documentation
* **Files:**
  - `README.md`
* **Actions:**
  1. Run `npm run build` inside `frontend/` to confirm 0 build errors.
  2. Run `pytest tests/ -v` inside root to confirm all 59 backend tests remain 100% green.
  3. Document Web Portal usage and screenshot in `README.md`.
  4. Commit all files locally to git (STRICTLY LOCAL GIT ONLY - NO GIT PUSH).
