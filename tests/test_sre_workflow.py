from langchain_core.messages import HumanMessage
from src.agent.nodes import (
    mitigate_node,
    plan_fix_node,
    triage_node,
    execute_fix_node,
)
from src.agent.state import IncidentState


def test_triage_node():
    """Kiểm tra triage_node phân loại mức độ nghiêm trọng và cập nhật timeline."""
    state: IncidentState = {
        "messages": [HumanMessage(content="Critical 500 internal server error")],
        "incident_id": "INC-TEST-TRIAGE",
        "service_name": "payment_service",
        "issue_description": "ConnectionTimeout: Failed to connect to payment gateway after 3000ms",
        "timeline": [],
    }
    result = triage_node(state)
    assert result["severity"] in ["P1", "P2"]
    assert len(result["timeline"]) == 1
    assert result["timeline"][0]["stage"] == "triage"


def test_mitigate_node():
    """Kiểm tra mitigate_node thực hiện dập lửa khẩn cấp và cập nhật timeline."""
    state: IncidentState = {
        "messages": [],
        "incident_id": "INC-TEST-MITIGATE",
        "service_name": "payment_service",
        "severity": "P2",
        "issue_description": "Timeout",
        "timeline": [],
    }
    result = mitigate_node(state)
    assert result["mitigation_status"] == "success"
    assert "mitigation_action_taken" in result
    assert len(result["timeline"]) == 1
    assert result["timeline"][0]["stage"] == "mitigation"


def test_plan_fix_node_with_human_feedback():
    """Kiểm tra plan_fix_node tích hợp phản hồi góp ý của kỹ sư khi bị từ chối."""
    state: IncidentState = {
        "messages": [],
        "incident_id": "INC-TEST-FEEDBACK",
        "service_name": "auth_service",
        "proposed_fix": "try: return token['user_id'] except KeyError: return None",
        "reviewer_feedback": "Khong nen dung try-except, hay dung token.get('user_id')",
        "approval_status": "revising",
        "timeline": [],
    }
    result = plan_fix_node(state)
    assert "token.get('user_id')" in result["proposed_fix"] or "Khong nen dung try-except" in result["proposed_fix"]
    assert result["approval_status"] == "pending"


def test_execute_fix_node_generates_postmortem():
    """Kiểm tra execute_fix_node khi duyệt xong sẽ sinh báo cáo Post-Mortem hoàn chỉnh."""
    state: IncidentState = {
        "messages": [],
        "incident_id": "INC-TEST-EXECUTE",
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "TypeError in verify_jwt",
        "proposed_fix": "Use safe token.get('user_id')",
        "approval_status": "approved",
        "timeline": [
            {"time": "10:00 UTC", "event": "Alert received", "stage": "triage"},
            {"time": "10:01 UTC", "event": "Container restarted", "stage": "mitigation"},
        ],
    }
    result = execute_fix_node(state)
    assert result["approval_status"] == "approved"
    assert "post_mortem_report" in result
    assert "Google SRE Incident Post-Mortem Report" in result["post_mortem_report"]
    assert "INC-TEST-EXECUTE" in result["post_mortem_report"]
    assert "github_pr_url" in result
    assert result["github_pr_url"].startswith("https://github.com")
