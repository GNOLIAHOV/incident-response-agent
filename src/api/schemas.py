from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)


class AlertWebhookPayload(BaseModel):
    """Payload cảnh báo chuẩn theo định dạng Prometheus Alertmanager / Grafana Webhook."""

    status: Optional[str] = Field("firing", description="firing hoặc resolved")
    alerts: List[AlertItem] = Field(default_factory=list)


class IncidentTriggerRequest(BaseModel):
    service_name: str = Field(..., description="Tên service xảy ra sự cố, ví dụ: auth_service")
    issue_description: str = Field(..., description="Mô tả chi tiết sự cố hoặc thông báo lỗi")
    thread_id: Optional[str] = Field(None, description="ID phiên làm việc. Nếu bỏ trống sẽ tự động tạo mới")


class IncidentTriggerResponse(BaseModel):
    thread_id: str
    status: Literal["processing", "paused_at_breakpoint", "completed"]
    next_node: Optional[str] = None
    proposed_fix: Optional[str] = None
    message: str


class IncidentStatusResponse(BaseModel):
    thread_id: str
    status: Literal["processing", "paused_at_breakpoint", "completed", "not_found"]
    severity: Optional[str] = None
    service_name: Optional[str] = None
    approval_status: Optional[str] = None
    next_node: Optional[str] = None
    proposed_fix: Optional[str] = None
    mitigation_action_taken: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    post_mortem_report: Optional[str] = None
    is_paused: bool


class IncidentApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True nếu phê duyệt bản vá, False nếu từ chối")
    feedback: Optional[str] = Field(
        None, description="Ý kiến góp ý cho Agent điều chỉnh bản vá nếu từ chối (Human Feedback Loop)"
    )


class IncidentApprovalResponse(BaseModel):
    thread_id: str
    status: Literal["approved", "rejected", "revising"]
    final_output: str
    post_mortem_report: Optional[str] = None


class PostMortemResponse(BaseModel):
    incident_id: str
    service_name: str
    severity: str
    post_mortem_markdown: str
