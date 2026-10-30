"""Telegram Long-Polling Runner for Local Testing.
Allows developers and SREs to test interactive approval buttons and bot commands
directly on their mobile phones without needing a public domain or ngrok tunnel.
"""

import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict
import httpx
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage

# Configure UTF-8 output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.config import settings
from src.agent.graph import incident_app
from src.api.app import handle_telegram_webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("telegram-runner")


def ensure_demo_incident_state(thread_id: str = "INC-DEMO-001"):
    """Đảm bảo sự cố mẫu INC-DEMO-001 đã có state sẵn sàng tại breakpoint hitl_gate."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)
    if not snapshot or not snapshot.values:
        logger.info(f"Khởi tạo sự cố mẫu {thread_id} chạy tới điểm ngắt HITL Gate...")
        initial_input = {
            "messages": [
                HumanMessage(
                    content=f"Dịch vụ 'payment_service' gặp sự cố: Connection timeout. Tiến hành cứu nạn và tạo bản vá."
                )
            ],
            "incident_id": thread_id,
            "service_name": "payment_service",
            "severity": "P1",
            "issue_description": "Connection timeout in payment gateway",
            "alert_source": "telegram_demo",
            "proposed_fix": "",
            "approval_status": "pending",
            "timeline": [],
        }
        for _ in incident_app.stream(initial_input, config=config):
            pass
        logger.info(f"Sự cố {thread_id} đã sẵn sàng chờ duyệt tại HITL Gate!")


def run_polling():
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.error("Vui lòng cấu hình TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong .env!")
        sys.exit(1)

    base_url = f"https://api.telegram.org/bot{token}"
    logger.info("=" * 60)
    logger.info("🚀 SRE Incident Telegram Polling Runner đã khởi động!")
    logger.info(f"🤖 Bot Token: {token[:10]}...{token[-5:]}")
    logger.info(f"📱 Chat ID giám sát: {chat_id}")
    logger.info("=" * 60)

    # 1. Đảm bảo trạng thái cho INC-DEMO-001
    ensure_demo_incident_state("INC-DEMO-001")

    # 2. Xóa Webhook cũ để chuyển sang Long-Polling mượt mà
    try:
        with httpx.Client(timeout=10.0) as client:
            client.get(f"{base_url}/deleteWebhook")
            logger.info("Đã xóa Webhook cũ, sẵn sàng nhận sự kiện qua Long-Polling.")
    except Exception as exc:
        logger.warning(f"Lỗi khi xóa Webhook: {exc}")

    offset = 0
    logger.info("Đang lắng nghe sự kiện từ Telegram... (Anh có thể bấm các nút trên điện thoại bây giờ!)")

    while True:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(
                    f"{base_url}/getUpdates",
                    params={"offset": offset, "timeout": 20},
                )
                if resp.status_code != 200:
                    logger.warning(f"getUpdates trả về HTTP {resp.status_code}: {resp.text}")
                    time.sleep(2)
                    continue

                data = resp.json()
                updates = data.get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1
                    bg_tasks = BackgroundTasks()

                    # Xử lý sự kiện thông qua Webhook handler chung
                    res = handle_telegram_webhook(update, bg_tasks)
                    logger.info(f"Đã xử lý sự kiện: {res}")

                    # Thực thi ngay các tác vụ nền nếu có (ví dụ resume workflow và mở PR)
                    for task in bg_tasks.tasks:
                        try:
                            task.func(*task.args, **task.kwargs)
                        except Exception as e:
                            logger.error(f"Lỗi khi thực thi background task: {e}", exc_info=True)

        except KeyboardInterrupt:
            logger.info("Đã dừng Polling Runner.")
            break
        except Exception as exc:
            logger.error(f"Lỗi polling: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    run_polling()
