import logging
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage

from src.core.config import settings
from src.agent.graph import incident_app
from src.agent.nodes import extract_text_content
from src.api.schemas import (
    IncidentApprovalRequest,
    IncidentApprovalResponse,
    IncidentStatusResponse,
    IncidentTriggerRequest,
    IncidentTriggerResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("incident-api")

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)


def run_agent_workflow_task(thread_id: str, initial_input: dict):
    """Tác vụ chạy nền cho Agent: điều tra sự cố cho tới khi gặp breakpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    logger.info(f"Bắt đầu tác vụ nền điều tra cho thread: {thread_id}")
    try:
        for _ in incident_app.stream(initial_input, config=config):
            pass
        logger.info(f"Tác vụ nền hoàn tất hoặc đã tạm dừng tại breakpoint cho thread: {thread_id}")
    except Exception as exc:
        logger.error(f"Lỗi trong tác vụ nền cho thread {thread_id}: {str(exc)}", exc_info=True)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Giao diện trực quan 3 bước giúp kiểm thử toàn bộ luồng hoạt động của Agent."""
    dashboard_file = settings.STATIC_DIR / "dashboard.html"
    if dashboard_file.exists():
        return HTMLResponse(content=dashboard_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard template not found</h1>", status_code=404)


@app.get("/health", tags=["System"])
def health_check():
    """Kiểm tra trạng thái hoạt động của dịch vụ."""
    return {"status": "ok", "service": "incident-response-agent"}


@app.post(
    "/incidents/trigger",
    response_model=IncidentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Incidents"],
)
def trigger_incident(payload: IncidentTriggerRequest, background_tasks: BackgroundTasks):
    """Tiếp nhận sự cố và đẩy vào tác vụ chạy nền (BackgroundTasks), phản hồi ngay lập tức."""
    thread_id = payload.thread_id or f"INCIDENT-{uuid.uuid4().hex[:8].upper()}"

    initial_input = {
        "messages": [
            HumanMessage(
                content=f"Service '{payload.service_name}' gap su co: {payload.issue_description}. Hay tra cuu log va phan tich."
            )
        ],
        "service_name": payload.service_name,
        "issue_description": payload.issue_description,
        "proposed_fix": "",
        "approval_status": "pending",
    }

    # Đẩy quy trình vào chạy nền
    background_tasks.add_task(run_agent_workflow_task, thread_id, initial_input)

    return IncidentTriggerResponse(
        thread_id=thread_id,
        status="processing",
        next_node=None,
        proposed_fix=None,
        message="Agent đã tiếp nhận sự cố và đang xử lý trong background. Kiểm tra trạng thái qua endpoint GET /incidents/{thread_id}/status.",
    )


@app.get(
    "/incidents/{thread_id}/status",
    response_model=IncidentStatusResponse,
    tags=["Incidents"],
)
def get_incident_status(thread_id: str):
    """Kiểm tra tiến độ, lấy bản vá đề xuất khi Agent đã chạm breakpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

    # Trường hợp Agent chưa khởi tạo hoặc chưa có dữ liệu
    if not snapshot or not snapshot.values:
        return IncidentStatusResponse(
            thread_id=thread_id,
            status="processing",
            approval_status="pending",
            next_node=None,
            proposed_fix=None,
            is_paused=False,
        )

    next_nodes = list(snapshot.next) if snapshot.next else []
    proposed_fix = snapshot.values.get("proposed_fix")

    # Điểm ngắt chỉ thực sự bật khi Agent đã chạy xong plan_fix và đang dừng trước execute_fix
    is_paused = ("execute_fix" in next_nodes) and bool(proposed_fix)

    if is_paused:
        current_status = "paused_at_breakpoint"
    elif snapshot.values.get("approval_status") in ["approved", "rejected"]:
        current_status = "completed"
    else:
        current_status = "processing"

    return IncidentStatusResponse(
        thread_id=thread_id,
        status=current_status,
        approval_status=snapshot.values.get("approval_status"),
        next_node=next_nodes[0] if next_nodes else None,
        proposed_fix=proposed_fix,
        is_paused=is_paused,
    )


@app.post(
    "/incidents/{thread_id}/approve",
    response_model=IncidentApprovalResponse,
    tags=["Incidents"],
)
def approve_incident_fix(thread_id: str, payload: IncidentApprovalRequest):
    """Gửi quyết định phê duyệt để Agent tiếp tục thực thi tạo PR hoặc hủy bỏ."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiên làm việc với thread_id '{thread_id}'.",
        )

    if not snapshot.next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phiên làm việc '{thread_id}' không ở trạng thái chờ duyệt.",
        )

    decision = "approved" if payload.approved else "rejected"

    incident_app.update_state(
        config,
        {"approval_status": decision},
        as_node="plan_fix",
    )

    try:
        # Resume đồ thị để hoàn tất node execute_fix
        for _ in incident_app.stream(None, config=config):
            pass

        final_snapshot = incident_app.get_state(config)
        messages = final_snapshot.values.get("messages", [])
        final_output = extract_text_content(messages[-1].content) if messages else ""

        return IncidentApprovalResponse(
            thread_id=thread_id,
            status=decision,
            final_output=final_output,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi resume Agent: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)
