import logging
import uuid
from typing import Any, Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage

from src.core.config import settings
from src.agent.graph import incident_app
from src.agent.nodes import extract_text_content
from src.api.schemas import (
    AlertWebhookPayload,
    IncidentApprovalRequest,
    IncidentApprovalResponse,
    IncidentStatusResponse,
    IncidentTriggerRequest,
    IncidentTriggerResponse,
    PostMortemResponse,
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
    "/alerts/webhook",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Alert Ingestion"],
)
def handle_alert_webhook(payload: AlertWebhookPayload, background_tasks: BackgroundTasks):
    """Tiếp nhận cảnh báo tự động từ Prometheus Alertmanager / Grafana Webhook."""
    if not payload.alerts:
        service_name = "unknown_service"
        issue_desc = "Cảnh báo không có chi tiết cụ thể"
    else:
        first_alert = payload.alerts[0]
        service_name = first_alert.labels.get("service") or first_alert.labels.get("job") or "auth_service"
        issue_desc = (
            first_alert.annotations.get("description")
            or first_alert.annotations.get("summary")
            or first_alert.labels.get("alertname")
            or "Phát hiện bất thường qua hệ thống giám sát"
        )

    thread_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"

    initial_input = {
        "messages": [
            HumanMessage(
                content=f"[WEBHOOK ALERT] Dịch vụ '{service_name}' kích hoạt cảnh báo: {issue_desc}."
            )
        ],
        "incident_id": thread_id,
        "service_name": service_name,
        "issue_description": issue_desc,
        "alert_source": "prometheus_webhook",
        "proposed_fix": "",
        "approval_status": "pending",
        "timeline": [],
    }

    background_tasks.add_task(run_agent_workflow_task, thread_id, initial_input)

    return {
        "status": "accepted",
        "thread_id": thread_id,
        "service_name": service_name,
        "message": f"Alert received for {service_name}. Autonomous SRE workflow dispatched in background.",
    }


@app.post(
    "/incidents/trigger",
    response_model=IncidentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Incidents"],
)
def trigger_incident(payload: IncidentTriggerRequest, background_tasks: BackgroundTasks):
    """Tiếp nhận sự cố thủ công từ người dùng và đẩy vào tác vụ chạy nền."""
    thread_id = payload.thread_id or f"INCIDENT-{uuid.uuid4().hex[:8].upper()}"

    initial_input = {
        "messages": [
            HumanMessage(
                content=f"Service '{payload.service_name}' gặp sự cố: {payload.issue_description}. Hãy tra cứu log và phân tích."
            )
        ],
        "incident_id": thread_id,
        "service_name": payload.service_name,
        "issue_description": payload.issue_description,
        "alert_source": "manual",
        "proposed_fix": "",
        "approval_status": "pending",
        "timeline": [],
    }

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
    """Kiểm tra tiến độ, lấy trạng thái dập lửa, timeline và bản vá đề xuất."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

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

    is_paused = (("hitl_gate" in next_nodes) or ("execute_fix" in next_nodes)) and bool(proposed_fix)

    if is_paused:
        current_status = "paused_at_breakpoint"
    elif snapshot.values.get("approval_status") == "escalated" or snapshot.values.get("next_worker") == "escalate":
        current_status = "escalated"
    elif snapshot.values.get("approval_status") in ["approved", "rejected"]:
        current_status = "completed"
    else:
        current_status = "processing"

    return IncidentStatusResponse(
        thread_id=thread_id,
        status=current_status,
        severity=snapshot.values.get("severity"),
        service_name=snapshot.values.get("service_name"),
        approval_status=snapshot.values.get("approval_status"),
        next_node=next_nodes[0] if next_nodes else None,
        proposed_fix=proposed_fix,
        mitigation_action_taken=snapshot.values.get("mitigation_action_taken"),
        timeline=snapshot.values.get("timeline"),
        post_mortem_report=snapshot.values.get("post_mortem_report"),
        is_paused=is_paused,
    )


@app.post(
    "/incidents/{thread_id}/approve",
    response_model=IncidentApprovalResponse,
    tags=["Incidents"],
)
def approve_incident_fix(thread_id: str, payload: IncidentApprovalRequest):
    """Gửi quyết định phê duyệt hoặc từ chối kèm góp ý (Human Feedback Loop)."""
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

    # 1. Trường hợp phê duyệt
    if payload.approved:
        decision = "approved"
        incident_app.update_state(
            config,
            {"approval_status": "approved"},
        )
        for _ in incident_app.stream(None, config=config):
            pass

        final_snapshot = incident_app.get_state(config)
        messages = final_snapshot.values.get("messages", [])
        final_output = extract_text_content(messages[-1].content) if messages else "Đã hoàn tất."
        post_mortem = final_snapshot.values.get("post_mortem_report")

        return IncidentApprovalResponse(
            thread_id=thread_id,
            status="approved",
            final_output=final_output,
            post_mortem_report=post_mortem,
        )

    # 2. Trường hợp từ chối kèm góp ý (Human Feedback Loop)
    elif payload.feedback:
        incident_app.update_state(
            config,
            {
                "approval_status": "revising",
                "reviewer_feedback": payload.feedback,
            },
        )
        for _ in incident_app.stream(None, config=config):
            pass

        revised_snapshot = incident_app.get_state(config)
        if revised_snapshot.values.get("approval_status") == "escalated":
            return IncidentApprovalResponse(
                thread_id=thread_id,
                status="escalated",
                final_output="Sự cố đã vượt ngưỡng 5 lượt điều phối và chuyển giao cho kỹ sư trực ban (Escalated).",
                post_mortem_report=None,
            )

        return IncidentApprovalResponse(
            thread_id=thread_id,
            status="revising",
            final_output=f"Đã ghi nhận góp ý: '{payload.feedback}'. Agent đang tiến hành điều chỉnh bản vá...",
            post_mortem_report=None,
        )

    # 3. Trường hợp từ chối hoàn toàn
    else:
        incident_app.update_state(
            config,
            {"approval_status": "rejected"},
        )
        for _ in incident_app.stream(None, config=config):
            pass

        return IncidentApprovalResponse(
            thread_id=thread_id,
            status="rejected",
            final_output="Kế hoạch sửa đổi đã bị hủy bỏ bởi kỹ sư.",
            post_mortem_report=None,
        )


@app.get(
    "/incidents/{thread_id}/post-mortem",
    response_model=PostMortemResponse,
    tags=["Incidents"],
)
def get_incident_post_mortem(thread_id: str):
    """Lấy báo cáo Google SRE Post-Mortem hoàn chỉnh sau khi sự cố đã được giải quyết."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy sự cố với thread_id '{thread_id}'.",
        )

    report = snapshot.values.get("post_mortem_report")
    if not report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sự cố '{thread_id}' chưa hoàn tất hoặc chưa có báo cáo Post-Mortem.",
        )

    return PostMortemResponse(
        incident_id=thread_id,
        service_name=snapshot.values.get("service_name", "app_service"),
        severity=snapshot.values.get("severity", "P2"),
        post_mortem_markdown=report,
    )


@app.get(
    "/incidents",
    response_model=List[Dict[str, Any]],
    tags=["Incidents"],
)
def list_incidents():
    """Liệt kê danh sách tất cả các sự cố đang lưu trong cơ sở dữ liệu SQLite."""
    # Lấy danh sách các thread từ checkpointer nếu hỗ trợ
    checkpointer = getattr(incident_app, "checkpointer", None)
    if checkpointer and hasattr(checkpointer, "storage"):
        thread_ids = list(checkpointer.storage.keys())
        results = []
        for tid in thread_ids:
            st = incident_app.get_state({"configurable": {"thread_id": tid}})
            if st and st.values:
                results.append(
                    {
                        "thread_id": tid,
                        "service_name": st.values.get("service_name"),
                        "severity": st.values.get("severity"),
                        "status": st.values.get("approval_status"),
                        "mitigation_action": st.values.get("mitigation_action_taken"),
                    }
                )
        return results
    return []
