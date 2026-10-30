# Multi-Agent SRE Swarm (Phase 2) Design Document

**Date:** 2026-10-30  
**Project:** `incident-response-agent`  
**Status:** Approved by Human Partner  
**Target Approach:** Approach 2A (Supervisor-Worker Hierarchical SRE Swarm with Hybrid Worker Autonomy)

---

## 1. Intent & Purpose

Elevate `incident-response-agent` into an **Enterprise Multi-Agent SRE Swarm**. Under this architecture, a central **Incident Commander (Supervisor Agent)** dynamically evaluates incident progress and orchestrates four autonomous specialist agents:
1. 🚒 **Remediation Agent:** Rapid emergency infrastructure mitigation (restart, rollback, traffic shedding) and War Room alert dispatch.
2. 🔍 **Investigator Agent:** Autonomous ReAct diagnostic loop querying logs, stack traces, and deducing 5 Whys root causes.
3. 🛠️ **Patching Agent:** Source code fix synthesis with AST validation and iterative refinement using human feedback.
4. 📋 **Scribe & Governance Agent:** Official Google SRE Post-Mortem compilation, GitHub Pull Request creation, and prevention issue filing upon approval.

Strict governance is enforced via an independent **`hitl_gate`** (Human-in-the-Loop Gate) ensuring no code modification or PR submission occurs without verified human sign-off.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
1. **Role Specialization & Clean Context Separation:**
   - Each specialist agent operates with its own domain-specific system prompt and dedicated subset of tools, eliminating prompt bloat and context dilution.
2. **Hybrid Worker Model (Decision 1A):**
   - **Investigator Agent:** Autonomous ReAct loop querying error logs iteratively to pinpoint root cause.
   - **Remediation & Scribe Agents:** Deterministic SRE runbook execution with structured tool calling for 100% operational reliability.
   - **Patching Agent:** Dedicated code synthesizer with syntax validation and feedback adaptation.
3. **Dedicated HITL Gate Topology:**
   - Independent `hitl_gate` node with conditional routing. Guarantees `scribe_agent` is NEVER invoked without explicit human approval.
4. **On-Call Escalation Circuit Breaker (Decision 2A):**
   - Limit supervisor delegations to `max 5 iterations`. If unresolved at turn 5, posts an emergency War Room escalation card and pauses for on-call manual intervention.
5. **100% Backward Compatibility:**
   - Preserve all existing tools, SQLite persistence (`PersistentSqliteSaver`), REST API contracts, and Web Dashboard functionality with zero test regressions.

### Non-Goals
* Running agents as separate distributed OS microservices (all agents execute within the Python process / Docker container orchestrated via LangGraph).
* Auto-merging Pull Requests without human review.

### Anti-Goals
* **No Uncontrolled Agent Loops:** Circuit breaker enforces bounded execution.
* **No Bypassing the Approval Gate:** Scribe cannot run without `approval_status == 'approved'`.

---

## 3. Swarm Architecture & Topology

```text
                     [ Prometheus / Grafana / Sentry Alert ]
                                       │
                                       ▼ (POST /alerts/webhook)
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 0: INGESTION & TRIAGE (Node: triage_node)                               │
│  ├── Parse alert payload (service, error_type, metrics, stack trace)          │
│  └── Classify Severity: P1-Critical / P2-High / P3-Medium                     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│              STAGE 1: INCIDENT COMMANDER (Node: supervisor_node)              │
│  ├── Inspects IncidentState (mitigation, investigation, fix, approval)        │
│  ├── Increments swarm_iterations counter                                      │
│  └── Dispatches to Next Worker:                                               │
│       ├── If not mitigated ──────────────► Remediation Agent                  │
│       ├── If not investigated ───────────► Investigator Agent                 │
│       ├── If fix needed / feedback ──────► Patching Agent                     │
│       ├── If approved ───────────────────► Scribe Agent                       │
│       └── If iterations >= 5 ────────────► Emergency Escalation Pause         │
└───────┬───────────────────┬───────────────────┬───────────────────┬───────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ REMEDIATION  │    │ INVESTIGATOR │    │   PATCHING   │    │    SCRIBE    │
│    AGENT     │    │    AGENT     │    │    AGENT     │    │    AGENT     │
│ (Runbook     │    │ (ReAct Log   │    │ (AST Code    │    │ (GitHub PR   │
│  Mitigation) │    │  Analysis)   │    │  Synthesis)  │    │  Post-Mortem)│
└───────┬──────┘    └───────┬──────┘    └───────┬──────┘    └───────┬──────┘
        │                   │                   │                   │
        └───────────────────┴───────────────────┼───────────────────┘
                                                ▼
                                   ┌─────────────────────────┐
                                   │     HITL_GATE NODE      │
                                   │  (Interrupt / Break)    │
                                   └────────────┬────────────┘
                                                │
                                ┌───────────────┴───────────────┐
                                ▼                               ▼
                        [ REJECT + FEEDBACK ]            [ APPROVE PATCH ]
                                │                               │
                                └──────► Back to Supervisor ◄───┘
```

---

## 4. Technical Specifications

### 4.1 Updated State Schema (`src/agent/state.py`)
```python
class IncidentState(TypedDict):
    # Core Fields
    messages: Annotated[list[BaseMessage], add_messages]
    incident_id: str
    service_name: str
    severity: Literal["P1", "P2", "P3"]
    issue_description: str
    alert_source: str
    
    # Lifecycle & Telemetry
    mitigation_action_taken: str
    mitigation_status: Literal["success", "failed", "skipped"]
    timeline: list[dict]
    investigation_summary: str
    proposed_fix: str
    reviewer_feedback: Optional[str]
    approval_status: Literal["pending", "approved", "rejected", "revising"]
    github_pr_url: Optional[str]
    post_mortem_report: Optional[str]
    
    # Swarm Orchestration Fields
    next_worker: Optional[Literal["remediation", "investigator", "patching", "scribe", "hitl", "escalate", "FINISH"]]
    swarm_iterations: int  # Starts at 0, max 5
```

### 4.2 Swarm Specialist Implementations (`src/agent/swarm/`)

1. **`prompts.py`**:
   - `SUPERVISOR_PROMPT`: Rules for routing state to appropriate worker.
   - `REMEDIATION_PROMPT`: Directs the remediation specialist on runbook execution.
   - `INVESTIGATOR_PROMPT`: Guides the ReAct diagnosis and 5 Whys deduction.
   - `PATCHING_PROMPT`: Guides safe AST code patching and feedback incorporation.
   - `SCRIBE_PROMPT`: Guides the post-mortem compilation and PR generation.

2. **`workers.py`**:
   - `remediation_worker(state)`: Selects and executes emergency mitigation runbook, dispatches War Room alert, updates timeline.
   - `investigator_worker(state)`: Runs ReAct tool loop with `query_error_logs`, builds 5 Whys, sets `investigation_summary`.
   - `patching_worker(state)`: Synthesizes minimal safe patch, validates Python syntax, sets `proposed_fix` and `approval_status="pending"`.
   - `hitl_gate_node(state)`: Evaluation gateway. When reached, graph pauses for human input. When resumed with `approved`, routes to supervisor for `scribe`; when `rejected`, routes to supervisor for `patching`.
   - `scribe_worker(state)`: Calls `create_github_pr`, `create_github_prevention_issue`, `generate_google_sre_postmortem`.

3. **`supervisor.py`**:
   - `supervisor_node(state)`: Inspects state flags, enforces the $\ge 5$ iteration circuit breaker, and sets `next_worker`.

### 4.3 Graph Compilation (`src/agent/graph.py`)
- `workflow = StateGraph(IncidentState)`
- Add nodes: `triage`, `supervisor`, `remediation`, `investigator`, `patching`, `hitl_gate`, `scribe`.
- Add conditional edges from `supervisor` based on `next_worker`.
- Add conditional edges from `hitl_gate` to `supervisor`.
- Interrupt configured before `hitl_gate`: `interrupt_before=["hitl_gate"]`.
- Compiled with `PersistentSqliteSaver`.

---

## 5. Verification Plan

1. **Unit Testing (`tests/test_swarm.py`):**
   - Test `supervisor_node` routing logic across all lifecycle phases.
   - Test circuit breaker escalation when iterations reach 5.
   - Test `remediation_worker` execution and War Room alert emission.
   - Test `investigator_worker` ReAct tool loop and 5 Whys output.
   - Test `patching_worker` with and without `reviewer_feedback`.
   - Test `hitl_gate` routing on approval vs rejection.
2. **Regression Testing:**
   - Verify all 38 existing tests pass with zero failures.
3. **Full Swarm Integration Test:**
   - Simulate Prometheus alert ➔ verify Swarm lifecycle ➔ HITL approval ➔ verify PR and Post-Mortem.
