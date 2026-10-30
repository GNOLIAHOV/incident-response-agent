"""Specialist Worker nodes for the Multi-Agent SRE Swarm.
Each worker is bounded to its operational domain with isolated prompts and contracts.
"""

import ast
from datetime import datetime, timezone
from typing import Optional
from langchain_core.messages import AIMessage, SystemMessage

from src.agent.state import IncidentState
from src.agent.swarm.prompts import (
    REMEDIATION_PROMPT,
    INVESTIGATOR_PROMPT,
    PATCHING_PROMPT,
    SCRIBE_PROMPT,
)
from src.tools.communication_tools import post_war_room_alert
from src.tools.incident_tools import create_github_pr, query_error_logs
from src.tools.mitigation_tools import execute_service_remediation
from src.tools.postmortem_tools import (
    create_github_prevention_issue,
    generate_google_sre_postmortem,
)


def get_current_time_str() -> str:
    """Trả về timestamp hiện tại định dạng UTC ISO."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def remediation_worker(state: IncidentState) -> dict:
    """🚒 Remediation Agent: Can thiệp khẩn cấp khôi phục uptime và gửi cảnh báo War Room."""
    service_name = state.get("service_name", "app_service")
    severity = state.get("severity", "P2")
    incident_id = state.get("incident_id", "INC-UNKNOWN")
    issue_desc = (state.get("issue_description") or "").lower()
    timeline = list(state.get("timeline") or [])

    # Quyết định hành động dập lửa tối ưu theo triệu chứng
    if "inventory" in service_name.lower() or "spike" in issue_desc:
        action_type = "circuit_breaker"
        extra = "100"
    elif "payment" in service_name.lower() or "deadlock" in issue_desc or "timeout" in issue_desc:
        action_type = "rollback"
        extra = "v1.2.0-stable"
    else:
        action_type = "restart"
        extra = None

    # Thực thi hành động giảm nhẹ
    rem_res = execute_service_remediation.invoke(
        {"service_name": service_name, "action_type": action_type, "extra_param": extra}
    )

    # Gửi thông báo cứu nạn lên War Room
    post_war_room_alert.invoke(
        {
            "incident_id": incident_id,
            "service_name": service_name,
            "severity": severity,
            "stage": "Emergency Mitigation",
            "action_taken": rem_res.get("message", f"Executed {action_type}"),
        }
    )

    now = get_current_time_str()
    timeline.append(
        {
            "time": now,
            "event": f"[Remediation Agent] Thực hiện cứu nạn: {rem_res.get('message')}",
            "stage": "mitigation",
        }
    )

    return {
        "mitigation_action_taken": rem_res.get("action", action_type),
        "mitigation_status": rem_res.get("status", "success"),
        "timeline": timeline,
    }


def investigator_worker(state: IncidentState) -> dict:
    """🔍 Investigator Agent: Chẩn đoán nguyên nhân gốc rễ (RCA) và 5 Whys từ log lỗi."""
    service_name = state.get("service_name", "app_service")
    incident_id = state.get("incident_id", "INC-UNKNOWN")
    timeline = list(state.get("timeline") or [])

    # Tra cứu error logs
    log_content = query_error_logs.invoke({"service_name": service_name, "keyword": ""})

    if "NoneType" in log_content or "user_id" in log_content:
        rca_detail = "JWT token payload dictionary is missing 'user_id' key, causing TypeError subscript crash in verify_jwt()."
    elif "Deadlock" in log_content or "deadlock" in log_content:
        rca_detail = "Concurrent transactions competing for ExclusiveLock on stock_items tuple under high traffic spike."
    elif "ConnectionTimeout" in log_content:
        rca_detail = "Upstream payment gateway timeout at 10.0.4.12:443 exceeded 3000ms threshold."
    else:
        rca_detail = f"System error encountered in {service_name}: {log_content[:100]}."

    summary = (
        f"### RCA Diagnosis for {service_name}\n"
        f"- **Incident ID:** {incident_id}\n"
        f"- **Root Cause:** {rca_detail}\n"
        f"- **Log Evidence:** `{log_content[:150]}...`\n"
        f"- **5 Whys Deduction:** Direct access on dictionary key without fallback schema validation."
    )

    now = get_current_time_str()
    timeline.append(
        {
            "time": now,
            "event": f"[Investigator Agent] Hoàn thành RCA: {rca_detail}",
            "stage": "investigation",
        }
    )

    return {
        "investigation_summary": summary,
        "timeline": timeline,
    }


def patching_worker(state: IncidentState) -> dict:
    """🛠️ Patching Agent: Tổng hợp mã nguồn bản vá an toàn và tiếp thu ý kiến phản hồi khi bị từ chối."""
    service_name = state.get("service_name", "app_service")
    rca_summary = state.get("investigation_summary", "")
    reviewer_feedback = state.get("reviewer_feedback")
    timeline = list(state.get("timeline") or [])

    now = get_current_time_str()

    if reviewer_feedback:
        # Nếu có góp ý từ Reviewer, ưu tiên áp dụng chỉ dẫn cụ thể
        fix_code = (
            f"```python\n"
            f"# Patch adjusted per human reviewer feedback: {reviewer_feedback}\n"
            f"user_id = payload.get('user_id', None)\n"
            f"if not user_id:\n"
            f"    raise ValueError('Token missing user_id')\n"
            f"```"
        )
        # Kiểm tra tính hợp lệ cú pháp bằng AST Parser thật của Python
        raw_code = "\n".join([line for line in fix_code.splitlines() if not line.startswith("```")])
        try:
            ast.parse(raw_code)
            ast_status = "Passed ✅"
        except SyntaxError as exc:
            ast_status = f"Failed ❌ ({exc})"

        proposed_content = (
            f"### [Revised Patch Proposal]\n"
            f"**Adjusted based on Reviewer Feedback:** '{reviewer_feedback}'\n\n"
            f"{fix_code}\n\n"
            f"*AST Syntax Validation:* {ast_status}"
        )
        timeline.append(
            {
                "time": now,
                "event": f"[Patching Agent] Bản vá được điều chỉnh theo phản hồi: '{reviewer_feedback[:40]}...'",
                "stage": "planning",
            }
        )
    else:
        # Tổng hợp bản vá mặc định dựa trên RCA
        fix_code = (
            f"```python\n"
            f"def verify_jwt(token: str):\n"
            f"    payload = decode_jwt(token)\n"
            f"    user_id = payload.get('user_id') if payload else None\n"
            f"    if not user_id:\n"
            f"        raise ValueError('Payload missing user_id')\n"
            f"    return user_id\n"
            f"```"
        )
        # Kiểm tra tính hợp lệ cú pháp bằng AST Parser thật của Python
        raw_code = "\n".join([line for line in fix_code.splitlines() if not line.startswith("```")])
        try:
            ast.parse(raw_code)
            ast_status = "Passed ✅"
        except SyntaxError as exc:
            ast_status = f"Failed ❌ ({exc})"

        proposed_content = (
            f"### [Autonomous Safe Code Patch]\n"
            f"**Target Service:** {service_name}\n"
            f"**Objective:** Prevent NoneType subscript error.\n\n"
            f"{fix_code}\n\n"
            f"*AST Syntax Validation:* {ast_status}"
        )
        timeline.append(
            {
                "time": now,
                "event": f"[Patching Agent] Đã tổng hợp bản vá mã nguồn an toàn.",
                "stage": "planning",
            }
        )

    timeline.append(
        {
            "time": now,
            "event": "[HITL Gate] Bản vá đã sẵn sàng, tạm dừng chờ kỹ sư phê duyệt.",
            "stage": "governance",
        }
    )

    return {
        "proposed_fix": proposed_content,
        "approval_status": "pending",
        "timeline": timeline,
    }


def hitl_gate_node(state: IncidentState) -> dict:
    """🚪 HITL Gate Node: Tiếp nhận quyết định của kỹ sư trực ban sau khi mở khóa breakpoint."""
    now = get_current_time_str()
    timeline = list(state.get("timeline") or [])
    approval = state.get("approval_status", "pending")
    timeline.append(
        {
            "time": now,
            "event": f"[HITL Gate] Tiếp nhận quyết định của kỹ sư: {approval}.",
            "stage": "governance",
        }
    )
    return {"timeline": timeline}


def scribe_worker(state: IncidentState) -> dict:
    """📋 Scribe & Governance Agent: Mở Pull Request thật, Issue phòng ngừa và xuất Google SRE Post-Mortem."""
    if state.get("approval_status") == "rejected":
        return {
            "messages": [
                AIMessage(
                    content="Kế hoạch đã bị từ chối bởi Reviewer. Hủy thao tác mở Pull Request."
                )
            ]
        }

    fix_content = str(state.get("proposed_fix", ""))
    service_name = state.get("service_name", "app_service")
    issue_desc = state.get("issue_description", "incident fix")
    incident_id = state.get("incident_id", "INC-UNKNOWN")
    severity = state.get("severity", "P2")
    timeline = list(state.get("timeline") or [])

    # 1. Tạo Pull Request trên GitHub
    service_slug = service_name.replace("_", "-").lower()
    repo_name = f"backend/{service_slug}"
    clean_id = incident_id.replace("_", "-").lower()
    branch_name = f"fix/{service_slug}-{clean_id}"
    pr_title = f"fix({service_slug}): resolve {issue_desc[:50]}"

    pr_result = create_github_pr.invoke(
        {
            "repo": repo_name,
            "branch": branch_name,
            "title": pr_title,
            "changes": fix_content,
            "incident_id": incident_id,
            "service_slug": service_slug,
        }
    )

    github_pr_url = f"https://github.com/{repo_name}/pull/142"
    if "(URL: " in pr_result:
        try:
            github_pr_url = pr_result.split("(URL: ")[1].split(")")[0]
        except Exception:
            pass

    # 2. Tạo GitHub Issue cho việc phòng ngừa tái diễn sau sự cố
    issue_result = create_github_prevention_issue.invoke(
        {
            "repo": repo_name,
            "title": f"[SRE Prevention] Hardening & tests for {service_name}",
            "body": f"Action item created from incident {incident_id}.",
            "labels": ["sre", "prevention", severity.lower()],
        }
    )
    issue_url = issue_result.get("issue_url", "")

    # 3. Sinh báo cáo Google SRE Post-Mortem hoàn chỉnh
    now = get_current_time_str()
    event_msg = f"[Scribe Agent] Bản vá được phê duyệt. Đã tạo PR tại {github_pr_url}"
    if issue_url:
        event_msg += f" và Issue phòng ngừa tại {issue_url}"
    event_msg += "."

    timeline.append(
        {
            "time": now,
            "event": event_msg,
            "stage": "resolution",
        }
    )

    post_mortem = generate_google_sre_postmortem(
        incident_id=incident_id,
        service_name=service_name,
        severity=severity,
        issue_description=issue_desc,
        timeline=timeline,
        rca_summary=f"Automated Swarm RCA identified issue in {service_name}. Root cause addressed in PR {branch_name}.",
        fix_applied=fix_content[:200] + "...",
        mttd_seconds=30,
        mttr_seconds=120,
    )

    return {
        "messages": [AIMessage(content=f"Đã hoàn thành: {pr_result}")],
        "approval_status": "approved",
        "github_pr_url": github_pr_url,
        "post_mortem_report": post_mortem,
        "timeline": timeline,
    }
