from typing import Annotated, Literal, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class IncidentTimelineItem(TypedDict):
    """Mỗi mốc sự kiện trong dòng thời gian sự cố (Incident Timeline)."""

    time: str
    event: str
    stage: str


class IncidentState(TypedDict, total=False):
    """Định nghĩa cấu trúc dữ liệu State luân chuyển giữa các node trong Graph."""

    # add_messages tự động gộp các message mới vào danh sách hiện tại
    messages: Annotated[list[BaseMessage], add_messages]

    # Ingestion & Triage
    incident_id: str
    service_name: str
    severity: Literal["P1", "P2", "P3"]
    issue_description: str
    alert_source: str  # prometheus, grafana, sentry, manual

    # Mitigation & War Room
    mitigation_action_taken: str
    mitigation_status: Literal["success", "failed", "skipped"]
    timeline: list[dict]  # Danh sách các mốc sự kiện

    # RCA & Code Patch
    investigation_summary: str
    proposed_fix: str
    reviewer_feedback: Optional[str]  # Góp ý của kỹ sư khi từ chối bản vá

    # Trạng thái phê duyệt (Human-in-the-loop)
    approval_status: Literal["pending", "approved", "rejected", "revising", "escalated"]

    # Resolution & Post-Mortem
    github_pr_url: Optional[str]
    post_mortem_report: Optional[str]

    # Multi-Agent Swarm Orchestration
    next_worker: Optional[Literal["remediation", "investigator", "patching", "hitl", "scribe", "escalate", "FINISH"]]
    swarm_iterations: int  # Giới hạn tối đa 5 lượt điều phối (Circuit Breaker)
