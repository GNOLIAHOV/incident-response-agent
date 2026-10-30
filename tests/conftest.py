import sqlite3
import pytest

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Tự động dọn dẹp các bản ghi giả lập của unit test khỏi cơ sở dữ liệu SQLite sau mỗi lần chạy test."""
    yield
    try:
        conn = sqlite3.connect("data/incidents.db")
        conn.execute(
            "DELETE FROM thread_checkpoints "
            "WHERE thread_id LIKE 'INC-TEST-%' OR thread_id LIKE 'HEALTH-CHECK-%'"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
