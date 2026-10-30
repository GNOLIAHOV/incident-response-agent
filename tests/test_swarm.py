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
