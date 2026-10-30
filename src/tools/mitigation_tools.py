from typing import Optional
from langchain_core.tools import tool


@tool
def restart_service_container(service_name: str) -> dict:
    """Khởi động lại container / process của dịch vụ gặp sự cố để phục hồi uptime tức thời."""
    service_clean = service_name.strip().lower()
    return {
        "status": "success",
        "action": f"restart_container:{service_clean}",
        "message": f"Service container '{service_clean}' successfully restarted. Health probes returning 200 OK.",
    }


@tool
def rollback_service_deployment(service_name: str, target_version: str = "previous_stable") -> dict:
    """Rollback phiên bản triển khai của dịch vụ về phiên bản ổn định gần nhất trước đó."""
    service_clean = service_name.strip().lower()
    return {
        "status": "success",
        "action": f"rollback_deployment:{service_clean}",
        "target_version": target_version,
        "message": f"Deployment for '{service_clean}' rolled back to '{target_version}'. Traffic stabilized.",
    }


@tool
def apply_traffic_shedding(service_name: str, rate_limit_rps: int = 100) -> dict:
    """Kích hoạt giới hạn lưu lượng (rate limiting / circuit breaker) bảo vệ cơ sở dữ liệu và service."""
    service_clean = service_name.strip().lower()
    return {
        "status": "success",
        "action": f"apply_traffic_shedding:{service_clean}",
        "rate_limit_rps": rate_limit_rps,
        "message": f"Traffic shedding enabled on '{service_clean}' (capped at {rate_limit_rps} rps). Drop rate: 0%.",
    }


@tool
def execute_service_remediation(
    service_name: str,
    action_type: str,
    extra_param: Optional[str] = None,
) -> dict:
    """Bộ điều phối hành động dập lửa khẩn cấp (Emergency Mitigation Dispatcher).

    Hỗ trợ: 'restart', 'rollback', 'circuit_breaker', 'shed_traffic'.
    """
    action_type_lower = action_type.strip().lower()
    if action_type_lower == "restart":
        return restart_service_container.invoke({"service_name": service_name})
    elif action_type_lower == "rollback":
        target = extra_param or "previous_stable"
        return rollback_service_deployment.invoke(
            {"service_name": service_name, "target_version": target}
        )
    elif action_type_lower in ["circuit_breaker", "shed_traffic"]:
        limit = int(extra_param) if (extra_param and extra_param.isdigit()) else 100
        return apply_traffic_shedding.invoke(
            {"service_name": service_name, "rate_limit_rps": limit}
        )
    else:
        return {
            "status": "failed",
            "action": f"unknown:{action_type}",
            "message": f"Unknown remediation action '{action_type}' for service '{service_name}'. Supported: restart, rollback, circuit_breaker.",
        }
