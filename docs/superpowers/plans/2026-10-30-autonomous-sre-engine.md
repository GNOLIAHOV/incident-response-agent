# Autonomous SRE Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `incident-response-agent` into a production-grade Autonomous SRE platform that implements automated alert triage, emergency remediation (Mitigate First), war room notifications, SQLite persistence, human feedback loop, and automated Post-Mortem reporting.

**Architecture:** Monolithic Multi-Stage SRE Graph with 5 deterministic lifecycle stages:
1. Ingest & Triage (`triage_node`)
2. Emergency Mitigation & War Room (`mitigate_node`)
3. Deep RCA & Syntax-Checked Patch Generation (`investigate_node`, `plan_fix_node`)
4. Human-in-the-Loop Gate with Rejection Feedback (`interrupt_before=["execute_fix"]`)
5. Resolution & Google SRE Post-Mortem (`execute_fix_node`)

**Tech Stack:** Python 3.10+, FastAPI, LangGraph 0.2+, Google Gemini (`gemini-2.5-flash`), SQLite3, Pytest.

**Spec:** [`docs/superpowers/specs/2026-10-30-autonomous-sre-engine-design.md`](file:///d:/Projects/incident-response-agent/docs/superpowers/specs/2026-10-30-autonomous-sre-engine-design.md)

---

## Global Constraints

- **Python Standard Library first:** Use `sqlite3` for persistence to avoid external network package dependencies in sandboxed environments.
- **Strict HITL Gate:** Under no circumstances should source code changes or PR creation occur without explicit `approval_status == "approved"`.
- **Test-Driven Development (TDD):** Every task MUST write its unit test first, verify failure, implement minimal code, verify pass, and commit.
- **Backward Compatibility:** Existing core endpoints (`/health`, `/incidents/{id}/status`) must continue functioning seamlessly.

## Review Focus

1. **Unrecognized alert formats:** Malformed webhook payloads must default safely to `P3` severity without crashing the ingestion worker.
2. **Mitigation failures:** If an automated remediation tool fails (e.g. service not found), the incident must not halt; it logs the failure and continues to RCA.
3. **Repeated rejection feedback:** Reviewer feedback loops must correctly accumulate previous feedback so the LLM does not repeat previous mistakes.
4. **SQLite lock contention:** Database checkpoints must safely support concurrent reads/writes via WAL mode or serialized connections.
5. **Empty / missing logs:** If log queries return empty, the RCA stage must report insufficient telemetry instead of hallucinating code fixes.

---

### Task 1: State Schema Evolution & SQLite Persistence

**Files:**
- Modify: `src/agent/state.py`
- Create: `src/agent/checkpointer.py`
- Modify: `src/agent/graph.py`
- Test: `tests/test_state_and_persistence.py`

**Interfaces:**
- Produces: `PersistentSqliteSaver` checkpointer and extended `IncidentState` with `severity`, `timeline`, `mitigation_action_taken`, `reviewer_feedback`, `post_mortem_report`.

- [ ] **Step 1: Write the failing test for SQLite persistence & state schema**
Write `tests/test_state_and_persistence.py` testing that `PersistentSqliteSaver` creates database file, saves checkpoints across instances, and preserves new state fields.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_state_and_persistence.py -v`
Expected: FAIL (module/fields not found)

- [ ] **Step 3: Implement `IncidentState` updates & `PersistentSqliteSaver`**
- Update `src/agent/state.py` with the 5 SRE lifecycle fields.
- Create `src/agent/checkpointer.py` implementing `PersistentSqliteSaver` inheriting from `InMemorySaver` with SQLite table synchronization.
- Update `src/agent/graph.py` to use `PersistentSqliteSaver`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_state_and_persistence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/agent/state.py src/agent/checkpointer.py src/agent/graph.py tests/test_state_and_persistence.py
git commit -m "feat(agent): add persistent sqlite checkpointer and extended incident state"
```

---

### Task 2: Emergency Mitigation & Remediation Tools

**Files:**
- Create: `src/tools/mitigation_tools.py`
- Modify: `src/agent/nodes.py` (tool registration)
- Test: `tests/test_mitigation_tools.py`

**Interfaces:**
- Consumes: `service_name: str`, `action: str`
- Produces: `execute_service_remediation`, `restart_service_container`, `rollback_service_deployment`, `apply_traffic_shedding`

- [ ] **Step 1: Write the failing test for mitigation tools**
Write `tests/test_mitigation_tools.py` testing each mitigation action (`restart`, `rollback`, `circuit_breaker`) and verifying correct status strings and error handling for unknown services.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_mitigation_tools.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `src/tools/mitigation_tools.py`**
Implement the mitigation tools with simulated runbooks and extensible execution hooks.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_mitigation_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/tools/mitigation_tools.py tests/test_mitigation_tools.py
git commit -m "feat(tools): add automated emergency mitigation and remediation tools"
```

---

### Task 3: War Room Communication & Webhook Notification Tools

**Files:**
- Create: `src/tools/communication_tools.py`
- Test: `tests/test_communication_tools.py`

**Interfaces:**
- Produces: `post_war_room_alert(incident_id, service_name, severity, status, action_taken)` and `generate_war_room_card`

- [ ] **Step 1: Write the failing test for communication tools**
Write `tests/test_communication_tools.py` testing formatted card output and webhook dispatch simulation.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_communication_tools.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `src/tools/communication_tools.py`**
Implement Slack/Discord-compatible markdown card generator and webhook dispatcher.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_communication_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/tools/communication_tools.py tests/test_communication_tools.py
git commit -m "feat(tools): add war room communication and incident card tools"
```

---

### Task 4: Post-Mortem & GitHub Issue Prevention Tools

**Files:**
- Create: `src/tools/postmortem_tools.py`
- Test: `tests/test_postmortem_tools.py`

**Interfaces:**
- Produces: `generate_google_sre_postmortem(incident_id, timeline, rca_summary, fix_applied, mttd_seconds, mttr_seconds)` and `create_github_prevention_issue`

- [ ] **Step 1: Write the failing test for post-mortem tools**
Write `tests/test_postmortem_tools.py` asserting Google SRE sections: Incident Summary, Timeline, Root Cause (5 Whys), Recovery/Mitigation, and Action Items.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_postmortem_tools.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `src/tools/postmortem_tools.py`**
Implement Markdown report generator and GitHub prevention issue creator.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_postmortem_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/tools/postmortem_tools.py tests/test_postmortem_tools.py
git commit -m "feat(tools): add google sre post-mortem generator and prevention issue tools"
```

---

### Task 5: 5-Stage Graph Orchestration & Human Feedback Loop

**Files:**
- Modify: `src/agent/nodes.py`
- Modify: `src/agent/graph.py`
- Test: `tests/test_sre_workflow.py`

**Interfaces:**
- Consumes: Tools from Tasks 2, 3, 4
- Produces: `triage_node`, `mitigate_node`, updated `plan_fix_node` with feedback loop, updated `execute_fix_node` with Post-Mortem

- [ ] **Step 1: Write the failing test for the 5-stage SRE workflow**
Write `tests/test_sre_workflow.py` testing:
1. Normal flow: Ingest -> Triage -> Mitigate -> RCA -> HITL Breakpoint.
2. Rejection with feedback: Rejection causes agent to loop back to plan_fix with `reviewer_feedback` in history.
3. Approval flow: Generates Post-Mortem and finishes.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_sre_workflow.py -v`
Expected: FAIL

- [ ] **Step 3: Implement SRE nodes and graph wiring**
- Implement `triage_node` and `mitigate_node` in `nodes.py`.
- Update `plan_fix_node` to account for `reviewer_feedback`.
- Wire `START -> triage -> mitigate -> investigate` and feedback routing in `graph.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_sre_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/agent/nodes.py src/agent/graph.py tests/test_sre_workflow.py
git commit -m "feat(agent): wire 5-stage sre graph with mitigation and human feedback loop"
```

---

### Task 6: FastAPI Webhook & Management API Endpoints

**Files:**
- Modify: `src/api/schemas.py`
- Modify: `src/api/app.py`
- Test: `tests/test_sre_api.py`

**Interfaces:**
- Produces: `POST /alerts/webhook`, `POST /incidents/{id}/approve` (with feedback), `GET /incidents/{id}/post-mortem`, `GET /incidents`

- [ ] **Step 1: Write the failing test for API endpoints**
Write `tests/test_sre_api.py` testing webhook ingestion, feedback submission, and post-mortem retrieval.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_sre_api.py -v`
Expected: FAIL

- [ ] **Step 3: Implement API endpoints & schemas**
- Update `schemas.py` with `AlertWebhookPayload`, `IncidentApprovalRequest` (with optional `feedback: str`), `PostMortemResponse`.
- Add route handlers in `app.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_sre_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add src/api/schemas.py src/api/app.py tests/test_sre_api.py
git commit -m "feat(api): add alert webhook, rejection feedback, and post-mortem endpoints"
```

---

### Task 7: Interactive Web Dashboard Upgrade

**Files:**
- Modify: `src/api/static/dashboard.html`

- [ ] **Step 1: Enhance Dashboard UI**
Add:
- War Room Live Mitigation Timeline banner.
- Rejection modal with feedback text input (*"Muốn Agent sửa lại như thế nào?"*).
- Post-Mortem viewer tab displaying generated markdown report with copy-to-clipboard.

- [ ] **Step 2: Verify all 25+ test cases pass**
Run: `pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**
```bash
git add src/api/static/dashboard.html
git commit -m "feat(ui): upgrade dashboard with war room timeline, feedback modal, and post-mortem viewer"
```
