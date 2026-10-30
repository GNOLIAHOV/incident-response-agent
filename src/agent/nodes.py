from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import settings
from src.agent.state import IncidentState
from src.tools.incident_tools import create_github_pr, query_error_logs

tools = [query_error_logs, create_github_pr]
tool_map = {t.name: t for t in tools}

_llm_instance = None


def get_llm():
    """Khởi tạo hoặc lấy instance LLM một cách lười (Lazy Initialization).

    Tránh việc crash ứng dụng khi import module lúc chưa cấu hình GOOGLE_API_KEY.
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.DEFAULT_TEMPERATURE,
        ).bind_tools(tools)
    return _llm_instance


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


def investigate_node(state: IncidentState) -> dict:
    """Node 1: Phân tích báo cáo và gọi tool tra cứu log nếu cần."""
    system_prompt = SystemMessage(
        content=(
            "Ban la mot SRE/AI Incident Response Engineer. "
            "Nhiem vu cua ban la phan tich bao cao su co, goi cong cu query_error_logs de tim stack trace. "
            "Sau khi co log, hay giai thich nguyen nhan goc re va de xuat phuong an sua ma nguon cu the."
        )
    )

    history = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in history):
        messages = [system_prompt] + history
    else:
        messages = history

    llm_runner = get_llm()
    response = llm_runner.invoke(messages)
    return {"messages": [response]}


def tool_node(state: IncidentState) -> dict:
    """Node 2: Thực thi các công cụ mà LLM yêu cầu."""
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
    """Node 3: Trích xuất đề xuất bản vá và đưa vào trạng thái chờ phê duyệt."""
    ai_messages = [m for m in state["messages"] if isinstance(m, AIMessage)]
    if ai_messages:
        proposed_content = extract_text_content(ai_messages[-1].content)
    else:
        proposed_content = ""

    return {
        "proposed_fix": proposed_content,
        "approval_status": "pending",
    }


def execute_fix_node(state: IncidentState) -> dict:
    """Node 4: Thực thi tạo PR sau khi con người phê duyệt."""
    if state.get("approval_status") == "rejected":
        return {
            "messages": [
                AIMessage(
                    content="Ke hoach da bi tu choi boi Reviewer. Huy thao tac mo Pull Request."
                )
            ]
        }

    fix_content = str(state.get("proposed_fix", ""))
    service_name = state.get("service_name", "app_service")
    issue_desc = state.get("issue_description", "incident fix")

    # Tạo tên repository, branch và PR title linh hoạt theo service_name thực tế
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

    return {
        "messages": [AIMessage(content=f"Da hoan thanh: {pr_result}")],
        "approval_status": "approved",
    }


def route_investigation(state: IncidentState) -> Literal["tools", "plan_fix"]:
    """Hàm điều kiện phân nhánh giữa tools và plan_fix."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "plan_fix"
