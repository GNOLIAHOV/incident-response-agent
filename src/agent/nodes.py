import os
from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.state import IncidentState
from src.tools.incident_tools import create_github_pr, query_error_logs

tools = [query_error_logs, create_github_pr]
tool_map = {t.name: t for t in tools}

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
)
llm_with_tools = llm.bind_tools(tools)


def extract_text_content(content) -> str:
    """Chuyen doi content tu list/dict cua Gemini thanh chuoi van ban sach."""
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
    """Node 1: Phan tich bao cao va goi tool tra cuu log neu can."""
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

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: IncidentState) -> dict:
    """Node 2: Thuc thi cac cong cu ma LLM yeu cau."""
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
    """Node 3: Trich xuat de xuat ban va va dua vao trang thai cho phe duyet."""
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
    """Node 4: Thuc thi tao PR sau khi con nguoi phe duyet."""
    if state.get("approval_status") == "rejected":
        return {
            "messages": [
                AIMessage(
                    content="Ke hoach da bi tu choi boi Reviewer. Huy thao tac mo Pull Request."
                )
            ]
        }

    fix_content = str(state.get("proposed_fix", ""))

    pr_result = create_github_pr.invoke(
        {
            "repo": "backend/auth-service",
            "branch": "fix/jwt-payload-null-check",
            "title": "fix(auth): handle missing user_id in JWT verification",
            "changes": fix_content,
        }
    )

    return {
        "messages": [AIMessage(content=f"Da hoan thanh: {pr_result}")],
        "approval_status": "approved",
    }


def route_investigation(state: IncidentState) -> Literal["tools", "plan_fix"]:
    """Ham dieu kien phan nhanh giua tools va plan_fix."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "plan_fix"