# Autonomous SRE Engine (Phase 1) Design Document

**Date:** 2026-10-30  
**Project:** `incident-response-agent`  
**Status:** In Review  
**Target Approach:** Monolithic Multi-Stage SRE Graph  

---

## 1. Intent & Purpose

Transform `incident-response-agent` from a simple code-patch assistant into an **end-to-end Autonomous Site Reliability Engineering (SRE) Engine** operating under the golden principle:
> **"Mitigate First, Fix Later"** — Immediately stabilize the failing service, dispatch war-room communications, then synthesize and verify root-cause code fixes with Human-in-the-Loop review, concluding with automated Post-Mortem reporting.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
1. **Automated Alert Ingestion & Triage:** Accept alert payloads (Prometheus Alertmanager / Grafana / Datadog style) via `/alerts/webhook` and classify incident severity (`P1-Critical`, `P2-High`, `P3-Medium`).
2. **Immediate Emergency Mitigation (Dập lửa khẩn cấp):** Execute remediation actions (e.g., restart crashed service, rollback recent deployment, apply circuit-breaker) to restore uptime before deep code inspection.
3. **War Room Notification Dispatch:** Post live incident status updates, actions taken, and approval requests to team communication channels (Slack/Discord/Telegram webhook).
4. **Persistent State Storage (`SqliteSaver`):** Replace in-memory checkpointer with SQLite database storage (`data/incidents.db`) so active incidents and breakpoints persist across application restarts.
5. **Interactive Human Feedback Loop:** Allow reviewers to reject proposed fixes with specific guidance (e.g. *"Use dict.get with default value instead of try-except"*), prompting the agent to ingest feedback and synthesize a revised patch.
6. **Automated Post-Mortem & Prevention:** Upon incident resolution, automatically generate a Google SRE-standard Post-Mortem document (including Timeline, MTTD, MTTR, 5 Whys, and preventive Action Items) and file tracking issues on GitHub.
7. **Enhanced Web Dashboard:** Display the complete lifecycle: Alert intake, Mitigation timeline, HITL patch review with rejection feedback, and Post-Mortem reader.

### Non-Goals
* Managing real multi-cluster Kubernetes production nodes (mitigation actions will execute against local Docker / simulated service managers with extensible interfaces).
* Replacing human on-call engineers for high-risk manual database migrations.

### Anti-Goals
* **No Uncontrolled Production Modification:** Under no circumstances should source code changes or PR merging bypass the Human-in-the-Loop gate.
* **No Opaque AI Black Box:** Every diagnostic hypothesis, mitigation decision, and LLM reasoning step must be recorded in the incident state and timeline.

---

## 3. Approaches Considered

### Approach 1: Monolithic Multi-Stage SRE Graph (Selected)
* **Architecture:** Expand the single LangGraph `StateGraph` into clear, deterministic SRE lifecycle stages:
  `Ingest Alert -> Triage -> Mitigate & War Room -> Deep RCA -> HITL Gate -> (Approve: Open PR & Post-Mortem | Reject: Feedback Loop)`.
* **Trade-offs:** 
  - *Pros:* Easiest to debug, single unified state schema, 100% testable, and establishes the exact tools and data contracts needed for future sub-agents.
  - *Cons:* Single graph handles multiple responsibilities sequentially.
* **Why Selected:** Solidifies all core SRE capabilities immediately without introducing multi-agent orchestration overhead prematurely.

### Approach 2: Multi-Agent SRE Swarm (Future Upgrade Path)
* **Architecture:** A central Incident Commander Agent orchestrating 3 specialized sub-agents: Remediation Agent, Coding Agent, Scribe/Comms Agent.
* **Trade-offs:** High architectural modularity, but higher token usage and latency. Will be migrated directly from Approach 1 by wrapping its existing stage nodes into dedicated sub-agents.

---

## 4. System Architecture & Lifecycle Flow

```text
                     [ Prometheus / Grafana / Sentry Alert ]
                                       │
                                       ▼ (POST /alerts/webhook)
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: INGESTION & TRIAGE (FastAPI -> Background Task)                     │
│  ├── Parse alert payload (service, error_type, metrics, stack trace)          │
│  └── Determine Severity: P1-Critical / P2-High / P3-Medium                    │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: EMERGENCY MITIGATION & WAR ROOM (Node: mitigate_node)                │
│  ├── Execute immediate runbook: Restart container / Rollback image / Traffic  │
│  ├── Dispatch War Room Alert (Slack/Discord Webhook + Web Dashboard)          │
│  └── Record Mitigation Timestamp (for MTTD / MTTR calculation)                │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 3: DEEP ROOT CAUSE ANALYSIS & PATCH SYNTHESIS (Node: investigate_node)  │
│  ├── Query error logs & stack traces                                          │
│  ├── Analyze code and synthesize minimal safe patch                           │
│  └── Validate code syntax with Python AST                                     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 4: HUMAN-IN-THE-LOOP GATE (LangGraph Breakpoint)                        │
│  ├── System Pauses at 'execute_fix'                                           │
│  ├── Operator Reviews Proposed Patch on Web Dashboard / API                   │
│  │                                                                            │
│  ├── [ REJECT WITH FEEDBACK ] ──────────────────────────────────────────┐     │
│  │    Operator: "Use dict.get instead"                                  │     │
│  │    Agent loops back to Stage 3, adapts code, and pauses again        │     │
│  │                                                                      ▼     │
│  └── [ APPROVE PATCH ] ──> Resumes Graph ───────────────────────────────┘     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 5: RESOLUTION & POST-MORTEM (Node: execute_fix_node)                    │
│  ├── Create GitHub Branch & Open Pull Request                                 │
│  ├── Generate Google SRE-style Post-Mortem Report (Timeline, 5 Whys, MTTR)    │
│  ├── Create GitHub Prevention Issue for engineering backlog                   │
│  └── Update War Room with Resolution Summary                                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Technical Specifications

### 5.1 Updated State Schema (`IncidentState`)
Located in `src/agent/state.py`:
```python
class IncidentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Ingestion & Triage
    incident_id: str
    service_name: str
    severity: Literal["P1", "P2", "P3"]
    issue_description: str
    alert_source: str  # e.g., "prometheus", "grafana", "manual"
    
    # Mitigation & War Room
    mitigation_action_taken: str
    mitigation_status: Literal["success", "failed", "skipped"]
    timeline: list[dict]  # [{"time": ISO, "event": str, "stage": str}]
    
    # RCA & Code Patch
    investigation_summary: str
    proposed_fix: str
    reviewer_feedback: Optional[str]  # Human feedback upon rejection
    
    # HITL Gate
    approval_status: Literal["pending", "approved", "rejected", "revising"]
    
    # Resolution & Post-Mortem
    github_pr_url: Optional[str]
    post_mortem_report: Optional[str]
```

### 5.2 Persistent Storage (`SqliteSaver`)
* Path: `d:/Projects/incident-response-agent/data/incidents.db`
* Configured in `src/agent/graph.py` using `langgraph.checkpoint.sqlite.SqliteSaver`.
* Guarantees that any server reload or restart preserves active incident state and pending breakpoints.

### 5.3 Tooling Extensions (`src/tools/`)
1. **`mitigation_tools.py`**:
   - `execute_service_remediation(service_name, action)`: Supports `"restart_container"`, `"rollback_deployment"`, `"apply_circuit_breaker"`.
2. **`communication_tools.py`**:
   - `post_war_room_message(channel, title, text, severity)`: Dispatches formatted alert to webhooks (Slack/Discord format compatible).
3. **`postmortem_tools.py`**:
   - `generate_post_mortem(incident_id, timeline, rca_summary, fix_applied)`: Renders full markdown Google SRE post-mortem.
   - `create_github_issue(repo, title, body, labels)`: Tracks preventive action items.

### 5.4 API Endpoints
1. `POST /alerts/webhook`: Universal alert receiver (Prometheus Alertmanager / Grafana format).
2. `POST /incidents/{id}/approve`: Accepts `{ "approved": true }` OR `{ "approved": false, "feedback": "string" }`.
3. `GET /incidents/{id}/post-mortem`: Returns the generated post-mortem markdown report.
4. `GET /incidents`: Lists all historical and active incidents stored in SQLite.

---

## 6. Verification & Quality Plan

1. **Automated Pytest Suite:**
   - Test alert webhook ingestion & severity mapping.
   - Test mitigation tool execution and timeline tracking.
   - Test human feedback loop: Reject with feedback ➔ verify state switches to `revising` and updates patch.
   - Test post-mortem generation and SQLite state persistence across graph reload.
2. **Interactive Dashboard E2E:**
   - Trigger alert ➔ View instant mitigation in War Room ➔ Inspect synthesized fix ➔ Provide feedback ➔ Approve revised fix ➔ Inspect generated Post-Mortem.
