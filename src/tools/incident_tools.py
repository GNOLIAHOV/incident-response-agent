from typing import Optional
from langchain_core.tools import tool
from src.tools.github_client import github_client

MOCK_LOGS = {
    "auth_service": (
        "ERROR 2026-10-23 10:14:22 [auth_service] "
        "TypeError: 'NoneType' object is not subscriptable at /app/auth/tokens.py line 42 in verify_jwt(). "
        "Token payload is missing 'user_id'."
    ),
    "payment_service": (
        "ERROR 2026-10-23 10:15:01 [payment_service] "
        "ConnectionTimeout: Failed to connect to payment gateway at 10.0.4.12:443 after 3000ms."
    ),
    "inventory_service": (
        "CRITICAL 2026-10-23 20:30:15 [inventory_service] "
        "sqlalchemy.exc.OperationalError: (psycopg2.errors.DeadlockDetected) deadlock detected "
        "DETAIL: Process 18402 waits for ExclusiveLock on tuple (42, 18) of relation 'stock_items'; "
        "blocked by process 18405. Process 18405 waits for ShareLock on transaction 928174; "
        "blocked by process 18402. "
        "HINT: See server log for query details. "
        "Stack trace: /app/services/inventory.py:89 in deduct_stock_atomic() "
        "-> Current isolation level: REPEATABLE READ. Concurrent flash sale request volume spiked to 12,000 req/s."
    ),
}


@tool
def query_error_logs(service_name: str, keyword: str = "") -> str:
    """Tra cuu logs he thong de tim stack trace va nguyen nhan loi theo ten service va tu khoa tuy chon."""
    service_name_lower = service_name.lower()
    log_content = MOCK_LOGS.get(service_name_lower)

    if not log_content:
        return f"Khong tim thay log loi nao cho service '{service_name}'."

    if keyword and keyword.lower() not in log_content.lower():
        return f"Service '{service_name}' co log nhung khong chua tu khoa '{keyword}'."

    return log_content


@tool
def create_github_pr(
    repo: str,
    branch: str,
    title: str,
    changes: str,
    incident_id: str = "INC-AUTO",
    service_slug: str = "service",
) -> str:
    """Tao Pull Request tren GitHub de ap dung ban va sua loi sau khi duoc phe duyet."""
    result = github_client.create_patch_pull_request(
        repo=repo,
        branch=branch,
        title=title,
        patch_content=changes,
        incident_id=incident_id,
        service_slug=service_slug,
    )
    return result.get("message", f"Success: Pull Request #142 '{title}' created on {repo}:{branch}.")
