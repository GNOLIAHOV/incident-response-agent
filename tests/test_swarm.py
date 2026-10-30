import pytest
from unittest.mock import MagicMock, patch
from src.agent.state import IncidentState
from src.agent.swarm.prompts import (
    SUPERVISOR_PROMPT,
    REMEDIATION_PROMPT,
    INVESTIGATOR_PROMPT,
    PATCHING_PROMPT,
    SCRIBE_PROMPT,
)
from src.agent.swarm.workers import (
    remediation_worker,
    investigator_worker,
    patching_worker,
    hitl_gate_node,
    scribe_worker,
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


def test_remediation_worker():
    state: IncidentState = {
        "incident_id": "INC-SWARM-REM",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "TypeError crash",
        "timeline": [],
    }
    result = remediation_worker(state)
    assert result["mitigation_status"] == "success"
    assert "restart" in result["mitigation_action_taken"]
    assert len(result["timeline"]) > 0


def test_investigator_worker():
    state: IncidentState = {
        "incident_id": "INC-SWARM-INV",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "TypeError in verify_jwt",
        "timeline": [],
    }
    result = investigator_worker(state)
    assert "investigation_summary" in result
    assert "auth_service" in result["investigation_summary"].lower() or "token" in result["investigation_summary"].lower()
    assert len(result["timeline"]) > 0


def test_patching_worker_without_feedback():
    state: IncidentState = {
        "incident_id": "INC-SWARM-PATCH",
        "service_name": "auth_service",
        "investigation_summary": "Missing user_id key in payload dictionary",
        "reviewer_feedback": None,
        "timeline": [],
    }
    result = patching_worker(state)
    assert "proposed_fix" in result
    assert result["approval_status"] == "pending"
    assert len(result["timeline"]) > 0


def test_patching_worker_with_feedback():
    state: IncidentState = {
        "incident_id": "INC-SWARM-PATCH-FB",
        "service_name": "auth_service",
        "investigation_summary": "Missing user_id",
        "reviewer_feedback": "Use payload.get('user_id', None) instead of try-except block.",
        "timeline": [],
    }
    result = patching_worker(state)
    assert "proposed_fix" in result
    assert "payload.get" in result["proposed_fix"] or "get" in result["proposed_fix"]
    assert result["approval_status"] == "pending"


def test_hitl_gate_node():
    state: IncidentState = {
        "incident_id": "INC-SWARM-HITL",
        "approval_status": "pending",
        "proposed_fix": "code fix",
        "timeline": [],
    }
    result = hitl_gate_node(state)
    assert "timeline" in result


def test_scribe_worker_approved():
    state: IncidentState = {
        "incident_id": "INC-SWARM-SCRIBE",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "Null user_id crash",
        "proposed_fix": "payload.get('user_id')",
        "approval_status": "approved",
        "timeline": [],
    }
    result = scribe_worker(state)
    assert result["approval_status"] == "approved"
    assert "github_pr_url" in result
    assert "post_mortem_report" in result
    assert "Google SRE Incident Post-Mortem Report" in result["post_mortem_report"]


def test_scribe_worker_rejected():
    state: IncidentState = {
        "incident_id": "INC-SWARM-REJ",
        "service_name": "auth_service",
        "approval_status": "rejected",
    }
    result = scribe_worker(state)
    assert "Hủy thao tác" in result["messages"][0].content or "từ chối" in result["messages"][0].content.lower()


def test_supervisor_routing_progression():
    from src.agent.swarm.supervisor import supervisor_node

    # 1. Ban đầu chưa dập lửa -> remediation
    state: IncidentState = {
        "incident_id": "INC-ROUTING-01",
        "service_name": "auth_service",
        "mitigation_action_taken": "",
        "mitigation_status": "skipped",
        "swarm_iterations": 0,
    }
    r1 = supervisor_node(state)
    assert r1["next_worker"] == "remediation"
    assert r1["swarm_iterations"] == 1

    # 2. Đã dập lửa nhưng chưa RCA -> investigator
    state.update({"mitigation_action_taken": "restart", "mitigation_status": "success", "swarm_iterations": 1})
    r2 = supervisor_node(state)
    assert r2["next_worker"] == "investigator"
    assert r2["swarm_iterations"] == 2

    # 3. Đã có RCA nhưng chưa có fix -> patching
    state.update({"investigation_summary": "RCA done", "swarm_iterations": 2})
    r3 = supervisor_node(state)
    assert r3["next_worker"] == "patching"
    assert r3["swarm_iterations"] == 3

    # 4. Đã có fix nhưng pending review -> hitl
    state.update({"proposed_fix": "fix code", "approval_status": "pending", "swarm_iterations": 3})
    r4 = supervisor_node(state)
    assert r4["next_worker"] == "hitl"

    # 5. Đã duyệt -> scribe
    state.update({"approval_status": "approved", "swarm_iterations": 3})
    r5 = supervisor_node(state)
    assert r5["next_worker"] == "scribe"


def test_supervisor_circuit_breaker_escalation():
    from src.agent.swarm.supervisor import supervisor_node

    # Khi iterations >= 5 -> kích hoạt ngắt mạch escalate
    state: IncidentState = {
        "incident_id": "INC-BREAKER-01",
        "service_name": "auth_service",
        "severity": "P1",
        "approval_status": "revising",
        "swarm_iterations": 5,
        "timeline": [],
    }
    res = supervisor_node(state)
    assert res["next_worker"] == "escalate"
    assert res["swarm_iterations"] == 6
    assert any("Ngắt mạch" in t.get("event", "") for t in res.get("timeline", []))


def test_swarm_graph_full_lifecycle_and_pause():
    from src.agent.graph import create_incident_graph
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import HumanMessage

    app = create_incident_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "TEST-SWARM-E2E"}}

    initial_input = {
        "messages": [HumanMessage(content="Auth service throwing TypeError")],
        "incident_id": "INC-SWARM-E2E",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "TypeError: 'NoneType' object is not subscriptable",
        "alert_source": "prometheus",
        "approval_status": "pending",
        "timeline": [],
    }

    # 1. Chạy đồ thị cho đến khi chạm breakpoint tại hitl_gate
    for _ in app.stream(initial_input, config=config):
        pass

    snapshot = app.get_state(config)
    assert snapshot.next == ("hitl_gate",)
    assert snapshot.values["mitigation_status"] == "success"
    assert "investigation_summary" in snapshot.values
    assert "proposed_fix" in snapshot.values

    # 2. Kỹ sư duyệt bản vá -> chạy tiếp tới hoàn tất
    app.update_state(config, {"approval_status": "approved"})
    for _ in app.stream(None, config=config):
        pass

    final_snapshot = app.get_state(config)
    assert not final_snapshot.next
    assert final_snapshot.values["approval_status"] == "approved"
    assert "github_pr_url" in final_snapshot.values
    assert "post_mortem_report" in final_snapshot.values
