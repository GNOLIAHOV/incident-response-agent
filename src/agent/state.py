from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class IncidentState(TypedDict):
    """Định nghĩa cấu trúc dữ liệu State luân chuyển giữa các node trong Graph."""

    # add_messages tự động gộp các message mới vào danh sách hiện tại
    messages: Annotated[list[BaseMessage], add_messages]

    # Thông tin đầu vào của sự cố
    service_name: str
    issue_description: str

    # Kế hoạch sửa đổi do AI đề xuất
    proposed_fix: str

    # Trạng thái phê duyệt bởi con người (Human-in-the-loop)
    approval_status: Literal["pending", "approved", "rejected"]