from typing import Literal, Optional
from pydantic import BaseModel, Field


class IncidentTriggerRequest(BaseModel):
    service_name: str = Field(..., description="Ten service xay ra su co, vi du: auth_service")
    issue_description: str = Field(..., description="Mo ta chi tiet su co hoac thong bao loi")
    thread_id: Optional[str] = Field(None, description="ID phien lam viec. Neu bo trong se tu dong tao moi")


class IncidentTriggerResponse(BaseModel):
    thread_id: str
    status: Literal["processing", "paused_at_breakpoint", "completed"]
    next_node: Optional[str] = None
    proposed_fix: Optional[str] = None
    message: str


class IncidentStatusResponse(BaseModel):
    thread_id: str
    status: Literal["processing", "paused_at_breakpoint", "completed", "not_found"]
    approval_status: Optional[str] = None
    next_node: Optional[str] = None
    proposed_fix: Optional[str] = None
    is_paused: bool


class IncidentApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True neu phe duyet ban va, False neu tu choi")


class IncidentApprovalResponse(BaseModel):
    thread_id: str
    status: Literal["approved", "rejected"]
    final_output: str