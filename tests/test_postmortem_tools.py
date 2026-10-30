from src.tools.postmortem_tools import (
    create_github_prevention_issue,
    generate_google_sre_postmortem,
)


def test_generate_google_sre_postmortem():
    """Kiểm tra báo cáo Post-Mortem chuẩn Google SRE chứa đầy đủ các đề mục cốt lõi."""
    timeline = [
        {"time": "2026-10-30 10:00:00 UTC", "event": "Alert received (Prometheus)", "stage": "ingestion"},
        {"time": "2026-10-30 10:00:30 UTC", "event": "Service restarted (Uptime restored)", "stage": "mitigation"},
        {"time": "2026-10-30 10:02:00 UTC", "event": "Code patch synthesized and approved", "stage": "resolution"},
    ]
    report = generate_google_sre_postmortem(
        incident_id="INC-2026-001",
        service_name="auth_service",
        severity="P1",
        issue_description="HTTP 500 TypeError in verify_jwt()",
        timeline=timeline,
        rca_summary="JWT payload dictionary was missing 'user_id', causing subscript error.",
        fix_applied="Added safe .get('user_id') fallback check.",
        mttd_seconds=30,
        mttr_seconds=120,
    )
    assert "INC-2026-001" in report
    assert "Incident Summary" in report
    assert "Impact & SRE Metrics" in report
    assert "MTTD" in report and "30s" in report
    assert "MTTR" in report and "120s" in report
    assert "Timeline" in report
    assert "Root Cause Analysis (5 Whys)" in report
    assert "Preventative Action Items" in report


def test_create_github_prevention_issue():
    """Kiểm tra tool tạo Issue trên GitHub để theo dõi hành động phòng ngừa sau sự cố."""
    result = create_github_prevention_issue.invoke(
        {
            "repo": "backend/auth-service",
            "title": "[SRE Prevention] Add unit tests for null JWT user_id",
            "body": "Follow-up action item from Incident INC-2026-001.",
            "labels": ["sre", "prevention", "p1"],
        }
    )
    assert result["status"] == "created"
    assert "issue_url" in result
    assert "backend/auth-service" in result["message"]
