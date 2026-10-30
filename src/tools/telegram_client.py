"""Client tương tác với Telegram Bot API để gửi cảnh báo khẩn cấp lên điện thoại
và nhận quyết định phê duyệt (Approve / Reject) từ xa qua Inline Keyboard Buttons.
Tích hợp chế độ Graceful Offline Fallback khi chưa cấu hình Bot Token.
"""

import logging
from typing import Any, Dict, Optional
import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)


class TelegramClient:
    """Client tích hợp Telegram Bot phục vụ SRE War Room và Human-in-the-Loop từ xa."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = (bot_token if bot_token is not None else settings.TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id if chat_id is not None else settings.TELEGRAM_CHAT_ID).strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_configured(self) -> bool:
        """Kiểm tra cấu hình Telegram Bot Token và Chat ID."""
        return bool(self.bot_token and self.chat_id)

    def send_message(
        self,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown",
    ) -> Dict[str, Any]:
        """Gửi thông điệp văn bản hoặc thẻ điều khiển kèm bàn phím Inline."""
        if not self.is_configured():
            logger.info("Telegram chưa được cấu hình. Kích hoạt chế độ mô phỏng gửi tin nhắn.")
            return {
                "ok": True,
                "simulated": True,
                "result": {
                    "message_id": 9999,
                    "text": text,
                    "chat": {"id": self.chat_id or "simulated_chat"},
                    "reply_markup": reply_markup or {},
                },
                "message": "Simulated Telegram message dispatched (token not configured).",
            }

        payload: Dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}/sendMessage", json=payload)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Telegram sendMessage trả về HTTP {resp.status_code}: {resp.text}")
                return {"ok": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as exc:
            logger.error(f"Lỗi khi gửi tin nhắn Telegram: {exc}", exc_info=True)
            return {"ok": False, "error": str(exc)}

    def send_incident_alert(
        self,
        incident_id: str,
        service_name: str,
        severity: str,
        action_taken: str,
        extra_details: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Phát thông báo cứu nạn khẩn cấp lên nhóm Telegram SRE trực ban."""
        icon = "🔴" if severity == "P1" else ("🟠" if severity == "P2" else "🟡")
        action_safe = action_taken.replace("_", " ")
        card = (
            f"🚨 *[SRE WAR ROOM ALERT] {icon} {severity} - {service_name.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Incident ID:* `{incident_id}`\n"
            f"• *Service:* `{service_name}`\n"
            f"• *Hành động đã xử lý:* {action_safe}\n"
        )
        if extra_details:
            card += f"• *Chi tiết bổ sung:* {extra_details.replace('_', ' ')}\n"
        card += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        return self.send_message(card)

    def send_approval_request(
        self,
        incident_id: str,
        service_name: str,
        severity: str,
        fix_summary: str,
    ) -> Dict[str, Any]:
        """Gửi thẻ yêu cầu phê duyệt kèm 2 nút bấm tương tác [Approve] và [Reject] trực tiếp trên điện thoại."""
        icon = "🔴" if severity == "P1" else ("🟠" if severity == "P2" else "🟡")
        # Loại bỏ các cặp backtick lồng nhau để đảm bảo Telegram Markdown v1 hiển thị chuẩn xác
        clean_code = fix_summary.replace("```python", "").replace("```", "").strip()
        clean_code = clean_code[:350] + ("..." if len(clean_code) > 350 else "")

        card = (
            f"⚠️ *[APPROVAL REQUIRED] YÊU CẦU PHÊ DUYỆT BẢN VÁ*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Incident ID:* `{incident_id}`\n"
            f"• *Dịch vụ:* `{service_name}` ({icon} {severity})\n\n"
            f"*Đề xuất sửa đổi mã nguồn:*\n"
            f"```python\n{clean_code}\n```\n\n"
            f"👉 *Kỹ sư On-call vui lòng bấm nút để kích hoạt hành động:*"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Duyệt & Mở GitHub PR",
                        "callback_data": f"approve:{incident_id}",
                    },
                    {
                        "text": "❌ Từ chối bản vá",
                        "callback_data": f"reject:{incident_id}",
                    },
                ],
                [
                    {
                        "text": "📊 Kiểm tra trạng thái",
                        "callback_data": f"status:{incident_id}",
                    }
                ],
            ]
        }

        return self.send_message(card, reply_markup=reply_markup)

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> Dict[str, Any]:
        """Phản hồi callback_query để tắt trạng thái loading trên ứng dụng di động Telegram."""
        if not self.is_configured():
            return {"ok": True, "simulated": True, "result": True}

        payload: Dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            payload["text"] = text

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}/answerCallbackQuery", json=payload)
                if resp.status_code == 200:
                    return resp.json()
                return {"ok": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as exc:
            logger.error(f"Lỗi khi trả lời callback query Telegram: {exc}")
            return {"ok": False, "error": str(exc)}

    def edit_message_text(
        self,
        chat_id: Any,
        message_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown",
    ) -> Dict[str, Any]:
        """Cập nhật nội dung tin nhắn gốc sau khi kỹ sư đã bấm nút phê duyệt hoặc từ chối."""
        if not self.is_configured():
            return {
                "ok": True,
                "simulated": True,
                "result": {"message_id": message_id, "text": text},
            }

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}/editMessageText", json=payload)
                if resp.status_code == 200:
                    return resp.json()
                return {"ok": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as exc:
            logger.error(f"Lỗi khi sửa tin nhắn Telegram: {exc}")
            return {"ok": False, "error": str(exc)}


telegram_client = TelegramClient()
