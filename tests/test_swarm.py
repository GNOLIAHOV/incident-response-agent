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
