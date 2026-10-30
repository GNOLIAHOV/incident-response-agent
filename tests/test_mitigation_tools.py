from src.tools.mitigation_tools import (
    apply_traffic_shedding,
    execute_service_remediation,
    restart_service_container,
    rollback_service_deployment,
)


def test_restart_service_container():
    """Kiểm tra hành động khởi động lại container dịch vụ bị sự cố."""
    result = restart_service_container.invoke({"service_name": "auth_service"})
    assert result["status"] == "success"
    assert "auth_service" in result["action"]
    assert "restarted" in result["message"].lower()


def test_rollback_service_deployment():
    """Kiểm tra hành động rollback bản deploy về phiên bản stable trước đó."""
    result = rollback_service_deployment.invoke(
        {"service_name": "payment_service", "target_version": "v1.2.0"}
    )
    assert result["status"] == "success"
    assert "payment_service" in result["action"]
    assert "v1.2.0" in result["message"]


def test_apply_traffic_shedding():
    """Kiểm tra kích hoạt hạ tải / circuit breaker khi hệ thống bị nghẽn tải."""
    result = apply_traffic_shedding.invoke(
        {"service_name": "inventory_service", "rate_limit_rps": 100}
    )
    assert result["status"] == "success"
    assert "100" in result["message"]


def test_execute_service_remediation_dispatcher():
    """Kiểm tra bộ điều phối hành động dập lửa khẩn cấp linh hoạt."""
    res_restart = execute_service_remediation.invoke(
        {"service_name": "auth_service", "action_type": "restart"}
    )
    assert res_restart["status"] == "success"

    res_rollback = execute_service_remediation.invoke(
        {"service_name": "payment_service", "action_type": "rollback"}
    )
    assert res_rollback["status"] == "success"

    res_unknown = execute_service_remediation.invoke(
        {"service_name": "auth_service", "action_type": "unknown_action"}
    )
    assert res_unknown["status"] == "failed"
