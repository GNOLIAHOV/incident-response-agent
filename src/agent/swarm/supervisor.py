"""Incident Commander (Supervisor Agent) node for the Multi-Agent SRE Swarm.
Evaluates lifecycle status, enforces circuit breaking, and delegates to specialized workers.
"""

from datetime import datetime, timezone
from src.agent.state import IncidentState
from src.tools.communication_tools import post_war_room_alert


def supervisor_node(state: IncidentState) -> dict:
    """Incident Commander: Đánh giá trạng thái sự cố và điều phối bước tiếp theo."""
    incident_id = state.get("incident_id", "INC-UNKNOWN")
    service_name = state.get("service_name", "app_service")
    severity = state.get("severity", "P2")
    timeline = list(state.get("timeline") or [])

    current_iterations = state.get("swarm_iterations", 0) + 1

    # 1. Kiểm tra Circuit Breaker (Tối đa 5 lượt điều phối)
    if current_iterations > 5:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        post_war_room_alert.invoke(
            {
                "incident_id": incident_id,
                "service_name": service_name,
                "severity": "P1",
                "stage": "Manual Escalation",
                "action_taken": "🚨 Ngắt mạch: Vượt quá 5 lượt điều phối tự động. Yêu cầu kỹ sư On-call can thiệp thủ công.",
            }
        )
        timeline.append(
            {
                "time": now,
                "event": "[Incident Commander] 🚨 Ngắt mạch: Vượt quá 5 lượt điều phối. Chuyển giao can thiệp thủ công.",
                "stage": "governance",
            }
        )
        return {
            "next_worker": "escalate",
            "swarm_iterations": current_iterations,
            "timeline": timeline,
        }

    # 2. Đánh giá trạng thái nghiệp vụ để giao việc cho Agent phù hợp
    mitigation_taken = state.get("mitigation_action_taken")
    mitigation_status = state.get("mitigation_status")
    rca_done = bool(state.get("investigation_summary"))
    fix_done = bool(state.get("proposed_fix"))
    approval = state.get("approval_status", "pending")

    if not mitigation_taken or mitigation_status != "success":
        next_worker = "remediation"
    elif not rca_done:
        next_worker = "investigator"
    elif approval in ("rejected", "revising") or not fix_done:
        next_worker = "patching"
    elif approval == "pending":
        next_worker = "hitl"
    elif approval == "approved":
        next_worker = "scribe"
    else:
        next_worker = "FINISH"

    return {
        "next_worker": next_worker,
        "swarm_iterations": current_iterations,
    }
