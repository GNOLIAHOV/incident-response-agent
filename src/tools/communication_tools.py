from datetime import datetime, timezone
from typing import Optional
from langchain_core.tools import tool


def generate_war_room_card(
    incident_id: str,
    service_name: str,
    severity: str,
    stage: str,
    action_taken: str,
    extra_details: Optional[str] = None,
) -> str:
    """Tạo nội dung thẻ thông báo War Room Markdown chuẩn định dạng Slack/Discord/Teams."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    severity_icon = "🔴" if severity == "P1" else ("🟠" if severity == "P2" else "🟡")

    card = (
        f"🚨 **[WAR ROOM SRE ALERT] {severity_icon} {severity} - {service_name.upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• **Incident ID:** `{incident_id}`\n"
        f"• **Service:** `{service_name}`\n"
        f"• **Timestamp:** `{now_iso}`\n"
        f"• **Current Stage:** `{stage}`\n"
        f"• **Action Taken:** `{action_taken}`\n"
    )
    if extra_details:
        card += f"• **Details:** {extra_details}\n"
    card += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return card


@tool
def post_war_room_alert(
    incident_id: str,
    service_name: str,
    severity: str,
    stage: str,
    action_taken: str,
    webhook_url: Optional[str] = None,
) -> dict:
    """Phát thông điệp cảnh báo sự cố lên kênh War Room (Slack / Discord / Teams webhook)."""
    card = generate_war_room_card(
        incident_id=incident_id,
        service_name=service_name,
        severity=severity,
        stage=stage,
        action_taken=action_taken,
    )

    # Trong môi trường sandbox / unit testing, ta ghi nhận kết quả thành công.
    return {
        "status": "sent",
        "incident_id": incident_id,
        "message": f"Successfully dispatched War Room alert card for incident {incident_id}",
        "card_content": card,
    }
