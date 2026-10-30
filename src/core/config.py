import os
from pathlib import Path
from dotenv import load_dotenv

# Xác định đường dẫn thư mục gốc của dự án
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    """Quản lý tập trung các biến môi trường và cấu hình hệ thống."""

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))

    API_TITLE: str = "Incident Response AI Agent API"
    API_DESCRIPTION: str = "REST API cho he thong tu dong dieu tra su co voi FastAPI BackgroundTasks va LangGraph Human-in-the-Loop"
    API_VERSION: str = "1.2.1"

    ROOT_DIR: Path = ROOT_DIR
    STATIC_DIR: Path = ROOT_DIR / "src" / "api" / "static"


settings = Settings()
