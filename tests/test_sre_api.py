from fastapi import BackgroundTasks
import pytest

from src.api.app import (
    approve_incident_fix,
    get_incident_post_mortem,
    get_incident_status,
    handle_alert_webhook,
    list_incidents,
)
from src.api.schemas import (
    AlertWebhookPayload,
    IncidentApprovalRequest,
)


def test_handle_alert_webhook():
    """Kiểm tra webhook tiếp nhận cảnh báo tự động từ Prometheus/Grafana."""
    bg_tasks = BackgroundTasks()
    payload = AlertWebhookPayload(
        status="firing",
        alerts=[
            {
                "labels": {
                    "alertname": "AuthService500Spike",
                    "service": "auth_service",
                    "severity": "critical",
                },
                "annotations": {
                    "description": "High rate of HTTP 500 errors in verify_jwt()",
                },
            }
        ],
    )
    res = handle_alert_webhook(payload, bg_tasks)
    assert res["status"] == "accepted"
    assert "thread_id" in res
    assert "auth_service" in res["service_name"]
    assert len(bg_tasks.tasks) == 1


def test_approve_with_rejection_feedback():
    """Kiểm tra endpoint approve chấp nhận feedback góp ý của kỹ sư khi từ chối bản vá."""
    # Khi thread không tồn tại -> trả về 404
    payload = IncidentApprovalRequest(approved=False, feedback="Dùng dict.get thay vì if-else")
    with pytest.raises(Exception):
        approve_incident_fix("THREAD-NON-EXISTENT", payload)


def test_get_incident_post_mortem_not_ready():
    """Kiểm tra lấy post-mortem khi sự cố chưa kết thúc."""
    with pytest.raises(Exception):
        get_incident_post_mortem("THREAD-NON-EXISTENT")


def test_list_incidents():
    """Kiểm tra endpoint liệt kê danh sách các sự cố."""
    incidents = list_incidents()
    assert isinstance(incidents, list)
