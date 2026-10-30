"""Unit tests for Telegram Bot Client and Remote HITL Webhook.
Tests both offline simulation fallback mode and mocked live HTTP interactions.
"""

from unittest.mock import MagicMock, patch
from fastapi import BackgroundTasks
import pytest

from src.core.config import settings
from src.tools.telegram_client import TelegramClient, telegram_client
from src.api.app import handle_telegram_webhook
from src.agent.graph import incident_app


# ============================================================================
# 1. KIỂM THỬ TELEGRAM CLIENT TRONG CHẾ ĐỘ MÔ PHỎNG (FALLBACK MODE)
# ============================================================================

def test_telegram_client_fallback_mode():
    """Kiểm tra TelegramClient hoạt động an toàn ở chế độ mô phỏng khi chưa có token."""
    client = TelegramClient(bot_token="", chat_id="")
    assert not client.is_configured()

    # 1. Gửi tin nhắn thông thường
    res_msg = client.send_message("Test message")
    assert res_msg["ok"] is True
    assert res_msg["simulated"] is True
    assert res_msg["result"]["message_id"] == 9999

    # 2. Gửi cảnh báo khẩn cấp
    res_alert = client.send_incident_alert(
        incident_id="INC-TEL-001",
        service_name="auth_service",
        severity="P1",
        action_taken="Container restarted",
    )
    assert res_alert["ok"] is True
    assert res_alert["simulated"] is True
    assert "INC-TEL-001" in res_alert["result"]["text"]

    # 3. Gửi thẻ yêu cầu phê duyệt với inline buttons
    res_approval = client.send_approval_request(
        incident_id="INC-TEL-001",
        service_name="auth_service",
        severity="P1",
        fix_summary="def verify_jwt(): pass",
    )
    assert res_approval["ok"] is True
    assert res_approval["simulated"] is True
    keyboard = res_approval["result"]["reply_markup"]["inline_keyboard"]
    assert any("approve:INC-TEL-001" in btn.get("callback_data", "") for row in keyboard for btn in row)
    assert any("reject:INC-TEL-001" in btn.get("callback_data", "") for row in keyboard for btn in row)

    # 4. Trả lời callback query và sửa message
    res_cb = client.answer_callback_query("cb_123", text="Done")
    assert res_cb["ok"] is True
    assert res_cb["simulated"] is True

    res_edit = client.edit_message_text(chat_id="12345", message_id=9999, text="Updated text")
    assert res_edit["ok"] is True
    assert res_edit["simulated"] is True


# ============================================================================
# 2. KIỂM THỬ TELEGRAM CLIENT VỚI HTTP MOCK (LIVE MODE)
# ============================================================================

def test_telegram_client_live_mocked_success():
    """Kiểm tra TelegramClient gửi HTTP request đúng format khi có token."""
    client = TelegramClient(bot_token="TEST_BOT_TOKEN_123", chat_id="987654321")
    assert client.is_configured()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 101, "text": "Hello"}}

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        # Gửi tin nhắn
        res = client.send_message("Hello from test")
        assert res["ok"] is True
        assert res["result"]["message_id"] == 101
        assert mock_post.called

        called_url = mock_post.call_args[0][0]
        called_json = mock_post.call_args[1]["json"]
        assert "sendMessage" in called_url
        assert called_json["chat_id"] == "987654321"
        assert called_json["text"] == "Hello from test"


def test_telegram_client_live_mocked_approval_request():
    """Kiểm tra thẻ duyệt gửi đúng inline buttons qua API."""
    client = TelegramClient(bot_token="TEST_BOT_TOKEN_123", chat_id="987654321")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 102}}

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = client.send_approval_request(
            incident_id="INC-999",
            service_name="payment_service",
            severity="P2",
            fix_summary="Increase timeout to 5000ms",
        )
        assert res["ok"] is True
        called_json = mock_post.call_args[1]["json"]
        assert "inline_keyboard" in called_json["reply_markup"]
        keyboard = called_json["reply_markup"]["inline_keyboard"]
        assert keyboard[0][0]["callback_data"] == "approve:INC-999"
        assert keyboard[0][1]["callback_data"] == "reject:INC-999"


def test_telegram_client_http_error_graceful_handling():
    """Kiểm tra xử lý lỗi kết nối mạng an toàn, không làm văng exception."""
    client = TelegramClient(bot_token="TEST_BOT_TOKEN_123", chat_id="987654321")

    with patch("httpx.Client.post", side_effect=Exception("Network connection failed")):
        res = client.send_message("Fail test")
        assert res["ok"] is False
        assert "Network connection failed" in res["error"]


# ============================================================================
# 3. KIỂM THỬ WEBHOOK FASTAPI NHẬN PHẢN HỒI TỪ XA (REMOTE HITL WEBHOOK)
# ============================================================================

def test_telegram_webhook_callback_approve():
    """Kiểm tra webhook nhận callback Approve từ inline button trên điện thoại."""
    thread_id = "INC-TEST-TEL-APP"
    config = {"configurable": {"thread_id": thread_id}}

    incident_app.update_state(
        config,
        {
            "incident_id": thread_id,
            "service_name": "auth_service",
            "severity": "P1",
            "proposed_fix": "code fix",
            "approval_status": "pending",
            "timeline": [],
        },
    )

    update_payload = {
        "update_id": 123456,
        "callback_query": {
            "id": "cb_query_001",
            "from": {"id": 111, "username": "sre_lead", "first_name": "Nam"},
            "message": {
                "message_id": 444,
                "chat": {"id": 999},
                "text": "Approval required",
            },
            "data": f"approve:{thread_id}",
        },
    }

    bg_tasks = BackgroundTasks()
    data = handle_telegram_webhook(update_payload, bg_tasks)
    assert data["ok"] is True
    assert data["action"] == "approved"
    assert data["thread_id"] == thread_id
    assert len(bg_tasks.tasks) == 1

    st = incident_app.get_state(config)
    assert st.values.get("approval_status") == "approved"


def test_telegram_webhook_callback_reject():
    """Kiểm tra webhook nhận callback Reject từ inline button trên điện thoại."""
    thread_id = "INC-TEST-TEL-REJ"
    config = {"configurable": {"thread_id": thread_id}}

    incident_app.update_state(
        config,
        {
            "incident_id": thread_id,
            "service_name": "payment_service",
            "severity": "P2",
            "proposed_fix": "code fix",
            "approval_status": "pending",
            "timeline": [],
        },
    )

    update_payload = {
        "update_id": 123457,
        "callback_query": {
            "id": "cb_query_002",
            "from": {"id": 222, "username": "oncall_dev", "first_name": "Trang"},
            "message": {
                "message_id": 445,
                "chat": {"id": 999},
                "text": "Approval required",
            },
            "data": f"reject:{thread_id}",
        },
    }

    bg_tasks = BackgroundTasks()
    data = handle_telegram_webhook(update_payload, bg_tasks)
    assert data["ok"] is True
    assert data["action"] == "rejected"
    assert data["thread_id"] == thread_id
    assert len(bg_tasks.tasks) == 1

    st = incident_app.get_state(config)
    assert st.values.get("approval_status") == "rejected"


def test_telegram_webhook_text_command_status():
    """Kiểm tra lệnh text '/status <thread_id>' gửi từ Telegram chat."""
    thread_id = "INC-TEST-CMD"
    config = {"configurable": {"thread_id": thread_id}}

    incident_app.update_state(
        config,
        {
            "incident_id": thread_id,
            "service_name": "order_service",
            "severity": "P2",
            "approval_status": "revising",
            "mitigation_action_taken": "Restarted container",
            "timeline": [],
        },
    )

    update_payload = {
        "update_id": 123458,
        "message": {
            "message_id": 446,
            "from": {"id": 333, "username": "sre_bot_user"},
            "chat": {"id": 999},
            "text": f"/status {thread_id}",
        },
    }

    bg_tasks = BackgroundTasks()
    data = handle_telegram_webhook(update_payload, bg_tasks)
    assert data["ok"] is True
    assert data["command"] == "status"
    assert "order_service" in data["reply"]


def test_telegram_webhook_text_command_help():
    """Kiểm tra lệnh text '/help' gửi từ Telegram chat."""
    update_payload = {
        "update_id": 123459,
        "message": {
            "message_id": 447,
            "from": {"id": 333, "username": "sre_bot_user"},
            "chat": {"id": 999},
            "text": "/help",
        },
    }

    bg_tasks = BackgroundTasks()
    data = handle_telegram_webhook(update_payload, bg_tasks)
    assert data["ok"] is True
    assert data["command"] == "help"
    assert "Incident Response AI Agent" in data["reply"]
