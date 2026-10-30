import contextlib
import logging
import uuid
from typing import Any, Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from src.core.config import settings
from src.agent.graph import incident_app
from src.agent.nodes import extract_text_content
from src.tools.telegram_client import telegram_client
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

# Enable CORS for Enterprise Web Portal and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


def resume_agent_workflow_task(thread_id: str, notify_telegram: bool = True):
    """Tác vụ nền tiếp tục chạy workflow của Agent sau khi nhận phê duyệt từ xa (Telegram / API)."""
    config = {"configurable": {"thread_id": thread_id}}
    logger.info(f"Bắt đầu tiếp tục xử lý workflow cho thread: {thread_id}")
    try:
        for _ in incident_app.stream(None, config=config):
            pass
        logger.info(f"Workflow cho thread {thread_id} đã hoàn tất.")
    except Exception as exc:
        logger.error(f"Lỗi trong tác vụ tiếp tục workflow cho thread {thread_id}: {str(exc)}", exc_info=True)


@app.get("/", tags=["System"])
def root():
    """Thông tin API Autonomous SRE Incident Response Agent & đường dẫn tài liệu."""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "portal_url": "http://localhost:3002",
    }


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
    approval_status = snapshot.values.get("approval_status", "pending")

    is_paused = (("hitl_gate" in next_nodes) or ("execute_fix" in next_nodes) or bool(proposed_fix)) and approval_status == "pending"

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
    "/incidents/{thread_id}/resume",
    response_model=IncidentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Incidents"],
)
def resume_incident_pipeline(thread_id: str, background_tasks: BackgroundTasks):
    """Khởi động lại hoặc tiếp tục điều tra Swarm cho sự cố đang bị gián đoạn hoặc chưa chạy."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy phiên làm việc '{thread_id}'.",
        )

    background_tasks.add_task(resume_agent_workflow_task, thread_id)
    return IncidentTriggerResponse(
        thread_id=thread_id,
        status="processing",
        next_node=None,
        proposed_fix=None,
        message=f"Đã kích hoạt lại tiến trình SRE Swarm cho sự cố {thread_id}.",
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

    # Idempotent: Nếu đã duyệt hoặc hoàn tất trước đó thì trả về thành công thay vì báo lỗi 400
    current_approval = snapshot.values.get("approval_status")
    if current_approval in ["approved", "completed"]:
        return IncidentApprovalResponse(
            thread_id=thread_id,
            status="approved",
            final_output="Sự cố đã được phê duyệt và hoàn tất trước đó.",
            post_mortem_report=snapshot.values.get("post_mortem_report"),
        )

    has_proposed_fix = bool(snapshot.values.get("proposed_fix"))
    if not snapshot.next and not has_proposed_fix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phiên làm việc '{thread_id}' đang trong tiến trình phân tích tự động, chưa tới điểm dừng chờ duyệt. Vui lòng đợi trong giây lát.",
        )

    # 1. Trường hợp phê duyệt
    if payload.approved:
        decision = "approved"
        incident_app.update_state(
            config,
            {"approval_status": "approved"},
            as_node="hitl_gate",
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
            as_node="hitl_gate",
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
            as_node="hitl_gate",
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
    checkpointer = getattr(incident_app, "checkpointer", None)
    thread_ids = []

    # 1. Đọc trực tiếp danh sách thread_id từ SQLite nếu có checkpointer bền vững
    if checkpointer and hasattr(checkpointer, "_get_connection"):
        try:
            with contextlib.closing(checkpointer._get_connection()) as conn:
                cursor = conn.execute(
                    "SELECT thread_id FROM thread_checkpoints "
                    "WHERE thread_id NOT LIKE 'INC-TEST-%' AND thread_id NOT LIKE 'HEALTH-CHECK-%' "
                    "ORDER BY updated_at DESC"
                )
                thread_ids = [row[0] for row in cursor.fetchall()]
        except Exception:
            pass

    # 2. Dự phòng lấy từ RAM nếu SQLite chưa sẵn sàng
    if not thread_ids and checkpointer and hasattr(checkpointer, "storage"):
        thread_ids = [
            t for t in checkpointer.storage.keys()
            if not t.startswith("INC-TEST-") and not t.startswith("HEALTH-CHECK-")
        ]

    results = []
    for tid in thread_ids:
        st = incident_app.get_state({"configurable": {"thread_id": tid}})
        if st and st.values:
            next_nodes = list(st.next) if st.next else []
            proposed_fix = st.values.get("proposed_fix")
            approval_status = st.values.get("approval_status", "pending")
            is_paused = (("hitl_gate" in next_nodes) or ("execute_fix" in next_nodes) or bool(proposed_fix)) and approval_status == "pending"

            if is_paused:
                lifecycle_status = "paused_at_breakpoint"
            elif approval_status in ["approved", "rejected"]:
                lifecycle_status = "completed"
            elif approval_status == "escalated":
                lifecycle_status = "escalated"
            else:
                lifecycle_status = "processing"

            results.append(
                {
                    "thread_id": tid,
                    "service_name": st.values.get("service_name") or "service",
                    "severity": st.values.get("severity") or "P2",
                    "status": lifecycle_status,
                    "approval_status": approval_status or "pending",
                    "mitigation_action": st.values.get("mitigation_action_taken"),
                    "created_at": getattr(st, "created_at", None),
                }
            )
    return results


@app.post(
    "/telegram/webhook",
    status_code=status.HTTP_200_OK,
    tags=["Telegram Remote HITL"],
)
def handle_telegram_webhook(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Tiếp nhận sự kiện tương tác từ Telegram Bot (Inline Buttons Approve/Reject hoặc Text Commands)."""
    # 1. Xử lý Callback Query khi người dùng bấm nút Inline trên Telegram
    if "callback_query" in payload:
        cb = payload["callback_query"]
        cb_id = cb.get("id", "")
        data = cb.get("data", "")
        user = cb.get("from", {}).get("username") or cb.get("from", {}).get("first_name", "Engineer")
        msg = cb.get("message", {})
        chat_id = msg.get("chat", {}).get("id") or settings.TELEGRAM_CHAT_ID
        msg_id = msg.get("message_id")

        action, thread_id = data.split(":", 1) if ":" in data else (data, "")
        config = {"configurable": {"thread_id": thread_id}}

        if action == "approve":
            snapshot = incident_app.get_state(config)
            if not snapshot or not snapshot.values:
                telegram_client.answer_callback_query(cb_id, text=f"Không tìm thấy sự cố {thread_id}!")
                return {"ok": False, "error": f"Incident {thread_id} not found"}

            current_status = snapshot.values.get("approval_status")
            if current_status in ["approved", "completed"]:
                telegram_client.answer_callback_query(cb_id, text="Sự cố này đã được phê duyệt trước đó!")
                return {"ok": True, "action": "already_approved", "thread_id": thread_id, "user": user}

            telegram_client.answer_callback_query(cb_id, text=f"✅ Đã duyệt bởi @{user}!")
            if msg_id and chat_id:
                telegram_client.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=(
                        f"✅ *[ĐÃ PHÊ DUYỆT BỞI @{user}]*\n"
                        f"Bản vá cho sự cố `{thread_id}` đã được thông qua.\n"
                        f"Agent đang tiến hành mở Pull Request và biên soạn Post-Mortem..."
                    ),
                )
            incident_app.update_state(config, {"approval_status": "approved"}, as_node="hitl_gate")
            background_tasks.add_task(resume_agent_workflow_task, thread_id, True)
            return {"ok": True, "action": "approved", "thread_id": thread_id, "user": user}

        elif action == "reject":
            snapshot = incident_app.get_state(config)
            if not snapshot or not snapshot.values:
                telegram_client.answer_callback_query(cb_id, text=f"Không tìm thấy sự cố {thread_id}!")
                return {"ok": False, "error": f"Incident {thread_id} not found"}

            current_status = snapshot.values.get("approval_status")
            if current_status in ["rejected", "cancelled"]:
                telegram_client.answer_callback_query(cb_id, text="Sự cố này đã bị từ chối trước đó!")
                return {"ok": True, "action": "already_rejected", "thread_id": thread_id, "user": user}

            telegram_client.answer_callback_query(cb_id, text=f"❌ Đã từ chối bởi @{user}!")
            if msg_id and chat_id:
                telegram_client.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=(
                        f"❌ *[ĐÃ TỪ CHỐI BỞI @{user}]*\n"
                        f"Kế hoạch sửa đổi cho sự cố `{thread_id}` đã bị hủy bỏ bởi kỹ sư trực ban."
                    ),
                )
            incident_app.update_state(config, {"approval_status": "rejected"}, as_node="hitl_gate")
            background_tasks.add_task(resume_agent_workflow_task, thread_id, True)
            return {"ok": True, "action": "rejected", "thread_id": thread_id, "user": user}

        elif action == "status":
            st = incident_app.get_state(config)
            status_val = st.values.get("approval_status", "unknown") if st and st.values else "not found"
            telegram_client.answer_callback_query(cb_id, text=f"Trạng thái {thread_id}: {status_val}")
            return {"ok": True, "action": "status", "thread_id": thread_id, "status": status_val}

    # 2. Xử lý tin nhắn văn bản thông thường / lệnh bot (Text commands)
    if "message" in payload:
        msg = payload["message"]
        text = (msg.get("text") or "").strip()

        if text.startswith("/status"):
            parts = text.split()
            if len(parts) > 1:
                target_id = parts[1]
                config = {"configurable": {"thread_id": target_id}}
                st = incident_app.get_state(config)
                if st and st.values:
                    service = st.values.get("service_name", "N/A")
                    sev = st.values.get("severity", "N/A")
                    appr = st.values.get("approval_status", "N/A")
                    mit = st.values.get("mitigation_action_taken", "None")
                    reply_text = (
                        f"📊 *Trạng thái sự cố `{target_id}`:*\n"
                        f"• *Dịch vụ:* {service} ({sev})\n"
                        f"• *Tiến độ:* `{appr}`\n"
                        f"• *Dập lửa:* {mit}"
                    )
                else:
                    reply_text = f"⚠️ Không tìm thấy sự cố `{target_id}` trong cơ sở dữ liệu."
            else:
                reply_text = "Cú pháp tra cứu: `/status <thread_id>`"
            telegram_client.send_message(reply_text)
            return {"ok": True, "command": "status", "reply": reply_text}

        if text.startswith("/help") or text.startswith("/start"):
            reply_text = (
                "🤖 *Incident Response AI Agent - Telegram Controller*\n\n"
                "Danh sách lệnh hỗ trợ:\n"
                "• `/status <thread_id>`: Kiểm tra trạng thái và tiến độ xử lý của sự cố\n"
                "• `/help`: Hiển thị thông tin trợ giúp\n\n"
                "💡 Khi có sự cố cần can thiệp, Agent sẽ tự động gửi thông báo kèm nút [✅ Duyệt] và [❌ Từ chối] ngay tại đây!"
            )
            telegram_client.send_message(reply_text)
            return {"ok": True, "command": "help", "reply": reply_text}

    return {"ok": True, "message": "Ignored or unhandled update type"}
