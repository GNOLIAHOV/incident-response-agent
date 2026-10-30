# Multi-Agent SRE Swarm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the monolithic SRE graph into a hierarchical Multi-Agent SRE Swarm with a central Incident Commander Supervisor coordinating 4 specialized agents (Remediation, Investigator, Patching, Scribe) and an independent Human-in-the-Loop Gate.

**Architecture:** A central `supervisor_node` evaluates incident state flags and delegates tasks dynamically to specialized workers (`remediation_worker`, `investigator_worker`, `patching_worker`, `hitl_gate_node`, `scribe_worker`). The graph enforces bounded iterations (circuit breaker $\ge 5$), isolates prompt contexts per worker, and persists checkpoints via `PersistentSqliteSaver`.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, langchain-google-genai, SQLite (WAL mode), Docker, Pytest.

**Spec:** [docs/superpowers/specs/2026-10-30-multi-agent-sre-swarm-design.md](file:///d:/Projects/incident-response-agent/docs/superpowers/specs/2026-10-30-multi-agent-sre-swarm-design.md)

## Global Constraints

- **Strict Local Git:** NEVER run `git push`. All commits must remain strictly local.
- **Backward Compatibility:** All existing 38 pytest tests must pass without breaking contracts.
- **Human Governance:** Under no circumstances may `scribe_worker` create Pull Requests or issues without verified human approval (`approval_status == 'approved'`).
- **Circuit Breaker:** Supervisor must enforce a strict maximum of 5 delegations, escalating to War Room if exceeded.

## Review Focus

1. **Approval Enforcement at Scribe:** Ensure `scribe_worker` cannot be reached if an operator rejects a patch with feedback.
2. **Rejection Feedback Loop:** When reviewer feedback is provided, verify state transitions back to `patching_worker` and updates the proposed patch.
3. **Circuit Breaker Escalation:** When `swarm_iterations >= 5`, verify supervisor dispatches an emergency escalation card and halts graph execution safely.
4. **Context Isolation:** Verify each worker receives an isolated prompt context without inheriting unrelated system messages or raw tool calls from other workers.
5. **State Checkpointing Across Breakpoints:** Ensure SQLite saver persists `next_worker` and `swarm_iterations` across process reboots.

---

### Task 1: Swarm State Schema & Specialist Prompts

**Files:**
- Modify: `src/agent/state.py`
- Create: `src/agent/swarm/__init__.py`
- Create: `src/agent/swarm/prompts.py`
- Create: `tests/test_swarm.py`

**Interfaces:**
- Consumes: Existing `IncidentState` fields.
- Produces: `IncidentState` with `next_worker` and `swarm_iterations` fields; specialist system prompts in `src.agent.swarm.prompts`.

- [ ] **Step 1: Write failing test in `tests/test_swarm.py`**

```python
import pytest
from src.agent.state import IncidentState
from src.agent.swarm.prompts import (
    SUPERVISOR_PROMPT,
    REMEDIATION_PROMPT,
    INVESTIGATOR_PROMPT,
    PATCHING_PROMPT,
    SCRIBE_PROMPT,
)

def test_swarm_state_schema_and_prompts():
    state: IncidentState = {
        "messages": [],
        "incident_id": "INC-SWARM-01",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "Deadlock detected",
        "alert_source": "prometheus",
        "mitigation_action_taken": "",
        "mitigation_status": "skipped",
        "timeline": [],
        "investigation_summary": "",
        "proposed_fix": "",
        "reviewer_feedback": None,
        "approval_status": "pending",
        "github_pr_url": None,
        "post_mortem_report": None,
        "next_worker": "remediation",
        "swarm_iterations": 0,
    }
    assert state["next_worker"] == "remediation"
    assert state["swarm_iterations"] == 0
    assert "Incident Commander" in SUPERVISOR_PROMPT
    assert "Remediation" in REMEDIATION_PROMPT
    assert "Investigator" in INVESTIGATOR_PROMPT
    assert "Patching" in PATCHING_PROMPT
    assert "Scribe" in SCRIBE_PROMPT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_swarm.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'src.agent.swarm').

- [ ] **Step 3: Update `src/agent/state.py` and create `src/agent/swarm/prompts.py`**

- In `src/agent/state.py`: add `next_worker: Optional[Literal["remediation", "investigator", "patching", "hitl", "scribe", "escalate", "FINISH"]]` and `swarm_iterations: int`.
- In `src/agent/swarm/prompts.py`: define the 5 specialist prompts.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_swarm.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes locally**

```bash
git add src/agent/state.py src/agent/swarm/ tests/test_swarm.py
git commit -m "feat(swarm): extend IncidentState and define specialist system prompts"
```

---

### Task 2: Implement Specialist Swarm Workers

**Files:**
- Create: `src/agent/swarm/workers.py`
- Modify: `tests/test_swarm.py`

**Interfaces:**
- Consumes: `IncidentState`, tools (`mitigation_tools`, `incident_tools`, `postmortem_tools`, `github_client`).
- Produces: `remediation_worker`, `investigator_worker`, `patching_worker`, `hitl_gate_node`, `scribe_worker`.

- [ ] **Step 1: Write worker unit tests in `tests/test_swarm.py`**

Test each worker individually:
- `test_remediation_worker`: executes mitigation runbook and posts war room card.
- `test_investigator_worker`: performs log query and populates `investigation_summary`.
- `test_patching_worker`: synthesizes code fix and incorporates reviewer feedback.
- `test_hitl_gate_node`: preserves state for human decision.
- `test_scribe_worker`: calls GitHub PR and Post-Mortem generator.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_swarm.py -v`  
Expected: FAIL (cannot import workers).

- [ ] **Step 3: Implement workers in `src/agent/swarm/workers.py`**

- `remediation_worker`: analyzes symptoms, triggers remediation, posts War Room alert, updates timeline.
- `investigator_worker`: runs ReAct query on `query_error_logs`, builds 5 Whys, updates timeline.
- `patching_worker`: uses code generation prompt with AST validation, consumes `reviewer_feedback`, sets `approval_status="pending"`.
- `hitl_gate_node`: pass-through gateway before human review.
- `scribe_worker`: verifies `approval_status == "approved"`, creates PR, issue, post-mortem, updates timeline.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_swarm.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes locally**

```bash
git add src/agent/swarm/workers.py tests/test_swarm.py
git commit -m "feat(swarm): implement specialist workers for remediation, investigation, patching, and scribe"
```

---

### Task 3: Incident Commander Supervisor & Swarm Graph Compilation

**Files:**
- Create: `src/agent/swarm/supervisor.py`
- Modify: `src/agent/graph.py`
- Modify: `src/agent/nodes.py`
- Test: `tests/test_swarm.py`

**Interfaces:**
- Consumes: Workers from `src.agent.swarm.workers`, `IncidentState`.
- Produces: `supervisor_node`, compiled `app_workflow` in `src.agent.graph`.

- [ ] **Step 1: Write tests for supervisor routing and circuit breaker in `tests/test_swarm.py`**

- `test_supervisor_routing_logic`: initial -> remediation -> investigator -> patching -> hitl -> scribe -> FINISH.
- `test_supervisor_circuit_breaker`: when `swarm_iterations >= 5`, dispatches escalation card and routes to `escalate`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_swarm.py -k supervisor -v`  
Expected: FAIL (cannot import supervisor).

- [ ] **Step 3: Implement `supervisor_node` and update `src/agent/graph.py`**

- In `src/agent/swarm/supervisor.py`: implement `supervisor_node(state)` checking state flags and `swarm_iterations`.
- In `src/agent/graph.py`: assemble the Swarm StateGraph:
  - `triage` -> `supervisor`
  - Conditional edge from `supervisor` to `remediation`, `investigator`, `patching`, `scribe`, `hitl_gate`, `escalate`, or `END`.
  - Conditional edge from `hitl_gate` to `supervisor`.
  - Interrupt on `hitl_gate`: `interrupt_before=["hitl_gate"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_swarm.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes locally**

```bash
git add src/agent/swarm/supervisor.py src/agent/graph.py tests/test_swarm.py
git commit -m "feat(swarm): compile supervisor-driven swarm StateGraph with circuit breaker and HITL gate"
```

---

### Task 4: API & Dashboard Integration, Full Suite Regression, Documentation

**Files:**
- Modify: `src/api/app.py`
- Modify: `README.md`
- Test: Full test suite (`pytest tests/ -v`)

**Interfaces:**
- Exposes: FastAPI endpoints seamlessly managing Swarm graph lifecycle.
- Maintains: 100% backward compatibility with Web Dashboard and existing endpoints.

- [ ] **Step 1: Verify API integration and background task resume logic in `src/api/app.py`**

Ensure `POST /incidents/{id}/approve` with feedback resumes execution through the Swarm graph.

- [ ] **Step 2: Run complete test suite**

Run: `pytest tests/ -v`  
Expected: PASS (All 42+ tests pass with 0 regressions).

- [ ] **Step 3: Update `README.md` with Multi-Agent Swarm Architecture**

Add Swarm architecture diagram, specialist roles description, and circuit breaker documentation.

- [ ] **Step 4: Commit changes locally**

```bash
git add src/api/app.py README.md tests/
git commit -m "feat(swarm): wire API resumption, update documentation, and verify full test suite"
```
