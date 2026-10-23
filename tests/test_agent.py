import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

# Dam bao import duoc code tu thu muc goc cua du an
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent.nodes import (
    execute_fix_node,
    extract_text_content,
    plan_fix_node,
    route_investigation,
)
from src.agent.state import IncidentState
from src.api.app import app
from src.tools.incident_tools import create_github_pr, query_error_logs

client = TestClient(app)


# ============================================================================
# 1. KIEM THU CAC TOOLS (incident_tools.py)
# ============================================================================

def test_query_error_logs_existing_service():
    """Kiem tra tool query_error_logs tra ve log chinh xac khi tim dung service."""
    result = query_error_logs.invoke({"service_name": "auth_service", "keyword": "TypeError"})
    assert "auth_service" in result
    assert "TypeError: 'NoneType' object is not subscriptable" in result
    assert "/app/auth/tokens.py" in result


def test_query_error_logs_without_keyword():
    """Kiem tra tool query_error_logs van chay tot khi khong truyen tham so keyword."""
    result = query_error_logs.invoke({"service_name": "auth_service"})
    assert "auth_service" in result
    assert "TypeError" in result


def test_query_error_logs_unknown_service():
    """Kiem tra tool query_error_logs xu ly khi service khong ton tai trong mock logs."""
    result = query_error_logs.invoke({"service_name": "unknown_service", "keyword": ""})
    assert "Khong tim thay log loi" in result


def test_create_github_pr_success():
    """Kiem tra tool create_github_pr tra ve chuoi thong bao thanh cong."""
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
# 2. KIEM THU CAC NODES VA LOGIC DIEU HUONG (nodes.py)
# ============================================================================

def test_extract_text_content_string():
    """Kiem tra ham extract_text_content voi dau vao la chuoi text thuan."""
    assert extract_text_content("test content") == "test content"


def test_extract_text_content_gemini_format():
    """Kiem tra ham extract_text_content trich xuat dung text tu cau truc list cua Gemini."""
    gemini_data = [
        {"type": "text", "text": "Dong 1"},
        {"type": "text", "text": "Dong 2"},
    ]
    extracted = extract_text_content(gemini_data)
    assert extracted == "Dong 1\nDong 2"


def test_route_investigation_with_tool_calls():
    """Kiem tra ham route_investigation re nhanh sang 'tools' khi message cuoi co tool_calls."""
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
    """Kiem tra ham route_investigation re nhanh sang 'plan_fix' khi khong con tool_calls."""
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
    """Kiem tra node plan_fix trich xuat dung noi dung de xuat va dat status pending."""
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
    """Kiem tra node execute_fix dung lai va khong tao PR khi bi tu choi."""
    state: IncidentState = {
        "messages": [],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "code fix",
        "approval_status": "rejected",
    }
    result = execute_fix_node(state)
    assert len(result["messages"]) == 1
    assert "Ke hoach da bi tu choi" in result["messages"][0].content


def test_execute_fix_node_approved():
    """Kiem tra node execute_fix tao PR thanh cong khi duoc duyet."""
    state: IncidentState = {
        "messages": [],
        "service_name": "auth_service",
        "issue_description": "test",
        "proposed_fix": "code fix",
        "approval_status": "approved",
    }
    result = execute_fix_node(state)
    assert result["approval_status"] == "approved"
    assert "Success: Pull Request" in result["messages"][0].content


# ============================================================================
# 3. KIEM THU CAC ENDPOINT FASTAPI (app.py)
# ============================================================================

def test_api_health_check():
    """Kiem tra endpoint /health tra ve status 200 va dung format JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "incident-response-agent"}


@patch("src.api.app.run_agent_workflow_task")
def test_api_trigger_incident_background(mock_task):
    """Kiem tra endpoint /incidents/trigger tiep nhan yeu cau va phan hoi ngay 202 ma khong can goi LLM that."""
    payload = {
        "service_name": "auth_service",
        "issue_description": "Loi 500 xac thuc token",
        "thread_id": "TEST-THREAD-001",
    }
    response = client.post("/incidents/trigger", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["thread_id"] == "TEST-THREAD-001"
    assert data["status"] == "processing"
    # Kiem tra xem tac vu nen da duoc dang ky goi hay chua
    mock_task.assert_called_once()


def test_api_get_status_initial():
    """Kiem tra endpoint GET status khi state vua khoi tao."""
    response = client.get("/incidents/TEST-THREAD-001/status")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "TEST-THREAD-001"
    assert "status" in data


def test_api_approve_not_paused():
    """Kiem tra API chan thao tac approve khi graph chua o trang thai cho duyet."""
    response = client.post(
        "/incidents/THREAD-KHONG-TON-TAI/approve",
        json={"approved": True},
    )
    assert response.status_code in [400, 404]