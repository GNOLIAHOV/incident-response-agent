import sys
import os
from pathlib import Path

# Fix Windows console unicode printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure root dir is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.config import settings
from src.tools.telegram_client import TelegramClient

def main():
    print("Testing Live Telegram Bot Integration...")
    print(f"Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...{settings.TELEGRAM_BOT_TOKEN[-5:]}")
    print(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
    
    client = TelegramClient(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID,
    )
    
    if not client.is_configured():
        print("Error: Client is not configured!")
        sys.exit(1)
        
    print("\n1. Sending test welcome message...")
    welcome_text = (
        "🚀 *[KẾT NỐI THÀNH CÔNG]*\n"
        "Xin chào anh *Võ Long*!\n\n"
        "Hệ thống *Autonomous SRE AI Agent* đã được liên kết trực tiếp với tài khoản Telegram của anh.\n"
        "Từ bây giờ, mọi sự cố hệ thống và thẻ phê duyệt bản vá sẽ được gửi trực tiếp về đây."
    )
    res1 = client.send_message(welcome_text)
    print("Result 1:", res1)
    
    print("\n2. Sending interactive approval card with buttons...")
    res2 = client.send_approval_request(
        incident_id="INC-DEMO-001",
        service_name="payment_service",
        severity="P1",
        fix_summary=(
            "def verify_jwt(token: str):\n"
            "    payload = decode_jwt(token)\n"
            "    user_id = payload.get('user_id')\n"
            "    return user_id"
        ),
    )
    print("Result 2:", res2)

if __name__ == "__main__":
    main()
