import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Đảm bảo nạp biến môi trường từ .env ngay từ đầu
load_dotenv()

# Đảm bảo import được code từ thư mục gốc của dự án
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import BackgroundTasks, HTTPException
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.nodes import (
    execute_fix_node,
    extract_text_content,
    plan_fix_node,
    route_investigation,
)
from src.agent.state import IncidentState
from src.api.app import (
    approve_incident_fix,
    get_incident_status,
    health_check,
    trigger_incident,
)
from src.api.schemas import (
    IncidentApprovalRequest,
    IncidentTriggerRequest,
)
from src.tools.incident_tools import create_github_pr, query_error_logs


# ============================================================================
# 1. KIỂM THỬ CÁC TOOLS (incident_tools.py)
# ============================================================================

def test_query_error_logs_existing_service():
    """Kiểm tra tool query_error_logs trả về log chính xác khi tìm đúng service."""
    result = query_error_logs.invoke({"service_name": "auth_service", "keyword": "TypeError"})
    assert "auth_service" in result
    assert "TypeError: 'NoneType' object is not subscriptable" in result
    assert "/app/auth/tokens.py" in result


def test_query_error_logs_without_keyword():
    """Kiểm tra tool query_error_logs vẫn chạy tốt khi không truyền tham số keyword."""
    result = query_error_logs.invoke({"service_name": "auth_service"})
    assert "auth_service" in result
    assert "TypeError" in result


def test_query_error_logs_unknown_service():
    """Kiểm tra tool query_error_logs xử lý khi service không tồn tại trong mock logs."""
    result = query_error_logs.invoke({"service_name": "unknown_service", "keyword": ""})
    assert "Khong tim thay log loi" in result


def test_create_github_pr_success():
    """Kiểm tra tool create_github_pr trả về chuỗi thông báo thành công."""
    result = create_github_pr.invoke(
        {
            "repo": "backend/auth-service",
            "branch": "fix/jwt-issue",
            "title": "fix(auth): handle null jwt",
            "changes": "def verify_jwt(): pass",
        }
    )
    assert "Success: Pull Request" in result
    assert "backend/auth-service" in result


# ============================================================================
# 2. KIỂM THỬ CÁC NODES VÀ LOGIC ĐIỀU HƯỚNG (nodes.py)
# ============================================================================

def test_extract_text_content_string():
    """Kiểm tra hàm extract_text_content với đầu vào là chuỗi text thuần."""
    assert extract_text_content("test content") == "test content"


def test_extract_text_content_gemini_format():
    """Kiểm tra hàm extract_text_content trích xuất đúng text từ cấu trúc list của Gemini."""
    gemini_data = [
        {"type": "text", "text": "Dong 1"},
        {"type": "text", "text": "Dong 2"},
    ]
    extracted = extract_text_content(gemini_data)
    assert extracted == "Dong 1\nDong 2"


def test_route_investigation_with_tool_calls():
    """Kiểm tra hàm route_investigation rẽ nhánh sang 'tools' khi message cuối có tool_calls."""
    mock_ai_message = MagicMock()
    mock_ai_message.tool_calls = [{"name": "query_error_logs", "args": {}}]
    state: IncidentState = {
        "messages": [mock_ai_message],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "",
        "approval_status": "pending",
    }
    next_node = route_investigation(state)
    assert next_node == "tools"


def test_route_investigation_without_tool_calls():
    """Kiểm tra hàm route_investigation rẽ nhánh sang 'plan_fix' khi không còn tool_calls."""
    mock_ai_message = MagicMock()
    mock_ai_message.tool_calls = []
    state: IncidentState = {
        "messages": [mock_ai_message],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "",
        "approval_status": "pending",
    }
    next_node = route_investigation(state)
    assert next_node == "plan_fix"


def test_plan_fix_node():
    """Kiểm tra node plan_fix trích xuất đúng nội dung đề xuất và đặt status pending."""
    ai_msg = AIMessage(content="De xuat sua loi tai dong 42")
    state: IncidentState = {
        "messages": [ai_msg],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "",
        "approval_status": "pending",
    }
    result = plan_fix_node(state)
    assert result["proposed_fix"] == "De xuat sua loi tai dong 42"
    assert result["approval_status"] == "pending"


def test_execute_fix_node_rejected():
    """Kiểm tra node execute_fix dừng lại và không tạo PR khi bị từ chối."""
    state: IncidentState = {
        "messages": [],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "code fix",
        "approval_status": "rejected",
    }
    result = execute_fix_node(state)
    assert len(result["messages"]) == 1
    content_lower = result["messages"][0].content.lower()
    assert "từ chối" in content_lower or "tu choi" in content_lower


def test_execute_fix_node_approved():
    """Kiểm tra node execute_fix tạo PR thành công khi được duyệt với service_name động."""
    state: IncidentState = {
        "messages": [],
        "service_name": "payment_service",
        "issue_description": "Connection timeout to payment gateway",
        "proposed_fix": "code fix",
        "approval_status": "approved",
    }
    result = execute_fix_node(state)
    assert result["approval_status"] == "approved"
    assert "Success: Pull Request" in result["messages"][0].content
    assert "backend/payment-service" in result["messages"][0].content


# ============================================================================
# 3. KIỂM THỬ CÁC ENDPOINT FASTAPI (app.py)
# ============================================================================

def test_api_health_check():
    """Kiểm tra endpoint /health trả về status 200 và đúng format JSON."""
    result = health_check()
    assert result == {"status": "ok", "service": "incident-response-agent"}


def test_api_trigger_incident_background():
    """Kiểm tra endpoint trigger incident tạo background task và phản hồi 202."""
    bg_tasks = BackgroundTasks()
    payload = IncidentTriggerRequest(
        service_name="auth_service",
        issue_description="Lỗi 500 xác thực token",
        thread_id="TEST-THREAD-001",
    )
    result = trigger_incident(payload, bg_tasks)
    assert result.thread_id == "TEST-THREAD-001"
    assert result.status == "processing"
    # Kiểm tra tác vụ nền đã được thêm vào BackgroundTasks
    assert len(bg_tasks.tasks) == 1


def test_api_get_status_initial():
    """Kiểm tra endpoint GET status khi state vừa khởi tạo."""
    result = get_incident_status("TEST-THREAD-001")
    assert result.thread_id == "TEST-THREAD-001"
    assert result.status in ["processing", "paused_at_breakpoint", "completed"]


def test_api_approve_not_paused():
    """Kiểm tra API chặn thao tác approve khi graph chưa ở trạng thái chờ duyệt."""
    payload = IncidentApprovalRequest(approved=True)
    with pytest.raises(HTTPException) as exc_info:
        approve_incident_fix("THREAD-KHONG-TON-TAI", payload)
    assert exc_info.value.status_code in [400, 404]
