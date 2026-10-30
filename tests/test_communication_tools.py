from src.tools.communication_tools import (
    generate_war_room_card,
    post_war_room_alert,
)


def test_generate_war_room_card():
    """Kiểm tra việc tạo thẻ thông báo War Room Markdown chuẩn định dạng Slack/Discord."""
    card = generate_war_room_card(
        incident_id="INC-2026-999",
        service_name="payment_service",
        severity="P1",
        stage="Emergency Mitigation",
        action_taken="Rolled back to v1.2.0",
    )
    assert "INC-2026-999" in card
    assert "P1" in card
    assert "payment_service" in card
    assert "Emergency Mitigation" in card
    assert "Rolled back to v1.2.0" in card


def test_post_war_room_alert_tool():
    """Kiểm tra tool post_war_room_alert phát thông điệp cứu nạn thành công."""
    result = post_war_room_alert.invoke(
        {
            "incident_id": "INC-2026-999",
            "service_name": "auth_service",
            "severity": "P2",
            "stage": "Triage",
            "action_taken": "Investigating log stack trace",
        }
    )
    assert result["status"] == "sent"
    assert "INC-2026-999" in result["message"]
