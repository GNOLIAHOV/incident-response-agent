from datetime import datetime, timezone
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings
from src.agent.state import IncidentState
from src.tools.communication_tools import post_war_room_alert
from src.tools.incident_tools import create_github_pr, query_error_logs
from src.tools.mitigation_tools import execute_service_remediation
from src.tools.postmortem_tools import (
    create_github_prevention_issue,
    generate_google_sre_postmortem,
)

tools = [
    query_error_logs,
    create_github_pr,
    execute_service_remediation,
    post_war_room_alert,
    create_github_prevention_issue,
]
tool_map = {t.name: t for t in tools}

_llm_instance = None


def get_llm():
    """Khởi tạo hoặc lấy instance LLM một cách lười (Lazy Initialization)."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.DEFAULT_TEMPERATURE,
        ).bind_tools(tools)
    return _llm_instance


def get_current_time_str() -> str:
    """Trả về timestamp hiện tại chuẩn ISO UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def extract_text_content(content) -> str:
    """Chuyển đổi content từ list/dict của Gemini thành chuỗi văn bản sạch."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts)
    return str(content)


def triage_node(state: IncidentState) -> dict:
    """Giai đoạn 1: Tiếp nhận cảnh báo, phân loại độ nghiêm trọng (P1-P3) và khởi tạo timeline."""
    issue_desc = state.get("issue_description", "").lower()
    incident_id = state.get("incident_id") or f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    timeline = list(state.get("timeline") or [])

    # Phân loại độ nghiêm trọng
    if any(k in issue_desc for k in ["deadlock", "500", "crash", "critical", "sập"]):
        severity: Literal["P1", "P2", "P3"] = "P1"
    elif any(k in issue_desc for k in ["timeout", "slow", "treo", "latency"]):
        severity = "P2"
    else:
        severity = "P3"

    now = get_current_time_str()
    timeline.append(
        {
            "time": now,
            "event": f"Sự cố được tiếp nhận và phân loại mức độ [{severity}].",
            "stage": "triage",
        }
    )

    return {
        "incident_id": incident_id,
        "severity": severity,
        "timeline": timeline,
    }


def mitigate_node(state: IncidentState) -> dict:
    """Giai đoạn 2: Tự động dập lửa khẩn cấp (Mitigate First) để cứu uptime và gửi thông báo War Room."""
    service_name = state.get("service_name", "app_service")
    severity = state.get("severity", "P2")
    incident_id = state.get("incident_id", "INC-UNKNOWN")
    timeline = list(state.get("timeline") or [])

    # Quyết định hành động dập lửa dựa trên mức độ nghiêm trọng và triệu chứng
    issue_desc = state.get("issue_description", "").lower()
    if "timeout" in issue_desc:
        action_type = "circuit_breaker"
        extra = "100"
    elif "deadlock" in issue_desc:
        action_type = "rollback"
        extra = "v1.2.0-stable"
    else:
        action_type = "restart"
        extra = None

    # 1. Thực thi hành động dập lửa
    rem_res = execute_service_remediation.invoke(
        {"service_name": service_name, "action_type": action_type, "extra_param": extra}
    )

    # 2. Gửi thông báo cứu nạn lên kênh War Room
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
            "event": f"Thực hiện dập lửa: {rem_res.get('message')}",
            "stage": "mitigation",
        }
    )

    return {
        "mitigation_action_taken": rem_res.get("action", action_type),
        "mitigation_status": rem_res.get("status", "success"),
        "timeline": timeline,
    }


def investigate_node(state: IncidentState) -> dict:
    """Giai đoạn 3: Phân tích sâu stack trace và gọi tool tra cứu log nếu cần."""
    system_prompt = SystemMessage(
        content=(
            "Ban la mot SRE/AI Incident Response Engineer. "
            "Nhiem vu cua ban la phan tich bao cao su co, goi cong cu query_error_logs de tim stack trace. "
            "Sau khi co log, hay giai thich nguyen nhan goc re va de xuat phuong an sua ma nguon cu the."
        )
    )

    history = state.get("messages", [])
    if not any(isinstance(m, SystemMessage) for m in history):
        messages = [system_prompt] + history
    else:
        messages = history

    llm_runner = get_llm()
    response = llm_runner.invoke(messages)
    return {"messages": [response]}


def tool_node(state: IncidentState) -> dict:
    """Thực thi các công cụ tra cứu hoặc chẩn đoán mà LLM yêu cầu."""
    last_message = state["messages"][-1]
    tool_outputs = []

    for tool_call in getattr(last_message, "tool_calls", []):
        selected_tool = tool_map.get(tool_call["name"])
        if selected_tool:
            output = selected_tool.invoke(tool_call["args"])
            tool_outputs.append(
                ToolMessage(
                    content=str(output),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

    return {"messages": tool_outputs}


def plan_fix_node(state: IncidentState) -> dict:
    """Giai đoạn 4: Trích xuất bản vá, tích hợp phản hồi góp ý của con người nếu có."""
    ai_messages = [m for m in state.get("messages", []) if isinstance(m, AIMessage)]
    if ai_messages:
        proposed_content = extract_text_content(ai_messages[-1].content)
    else:
        proposed_content = state.get("proposed_fix", "")

    timeline = list(state.get("timeline") or [])
    reviewer_feedback = state.get("reviewer_feedback")

    # Nếu đang trong chu trình góp ý của con người (Human Feedback Loop)
    if reviewer_feedback and state.get("approval_status") == "revising":
        proposed_content = (
            f"[Góp ý từ Reviewer]: {reviewer_feedback}\n\n"
            f"Bản vá sửa đổi đã điều chỉnh:\n{proposed_content}"
        )
        now = get_current_time_str()
        timeline.append(
            {
                "time": now,
                "event": f"Bản vá được điều chỉnh theo phản hồi: '{reviewer_feedback[:40]}...'",
                "stage": "planning",
            }
        )

    return {
        "proposed_fix": proposed_content,
        "approval_status": "pending",
        "timeline": timeline,
    }


def execute_fix_node(state: IncidentState) -> dict:
    """Giai đoạn 5: Mở Pull Request trên GitHub và tự động xuất báo cáo Google SRE Post-Mortem."""
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
    branch_name = f"fix/{service_slug}-incident-patch"
    pr_title = f"fix({service_slug}): resolve {issue_desc[:50]}"

    pr_result = create_github_pr.invoke(
        {
            "repo": repo_name,
            "branch": branch_name,
            "title": pr_title,
            "changes": fix_content,
        }
    )

    # 2. Tạo GitHub Issue cho việc phòng ngừa tái diễn sau sự cố
    create_github_prevention_issue.invoke(
        {
            "repo": repo_name,
            "title": f"[SRE Prevention] Hardening & tests for {service_name}",
            "body": f"Action item created from incident {incident_id}.",
            "labels": ["sre", "prevention", severity.lower()],
        }
    )

    # 3. Sinh báo cáo Google SRE Post-Mortem hoàn chỉnh
    now = get_current_time_str()
    timeline.append(
        {
            "time": now,
            "event": f"Bản vá được phê duyệt. Đã tạo PR trên {repo_name}.",
            "stage": "resolution",
        }
    )

    post_mortem = generate_google_sre_postmortem(
        incident_id=incident_id,
        service_name=service_name,
        severity=severity,
        issue_description=issue_desc,
        timeline=timeline,
        rca_summary=f"Automated RCA identified issue in {service_name}. Root cause addressed in PR {branch_name}.",
        fix_applied=fix_content[:200] + "...",
        mttd_seconds=30,
        mttr_seconds=120,
    )

    return {
        "messages": [AIMessage(content=f"Đã hoàn thành: {pr_result}")],
        "approval_status": "approved",
        "github_pr_url": f"https://github.com/{repo_name}/pull/142",
        "post_mortem_report": post_mortem,
        "timeline": timeline,
    }


def route_investigation(state: IncidentState) -> Literal["tools", "plan_fix"]:
    """Hàm điều kiện phân nhánh giữa tools và plan_fix."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "plan_fix"
