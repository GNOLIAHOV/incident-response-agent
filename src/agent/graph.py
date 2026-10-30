from langgraph.graph import END, START, StateGraph

from src.agent.checkpointer import PersistentSqliteSaver
from src.agent.nodes import (
    execute_fix_node,
    investigate_node,
    plan_fix_node,
    route_investigation,
    tool_node,
)
from src.agent.state import IncidentState


def create_incident_graph(checkpointer=None):
    """Khởi tạo và biên dịch đồ thị xử lý sự cố kèm cơ chế Human-in-the-Loop."""

    # 1. Khởi tạo StateGraph với Schema IncidentState
    workflow = StateGraph(IncidentState)

    # 2. Đăng ký các Nodes vào đồ thị
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("plan_fix", plan_fix_node)
    workflow.add_node("execute_fix", execute_fix_node)

    # 3. Thiết lập các liên kết (Edges) và phân nhánh điều kiện
    workflow.add_edge(START, "investigate")

    # Phân nhánh: Tiếp tục gọi tool hay đã có đủ log để chuyển sang plan_fix
    workflow.add_conditional_edges(
        "investigate",
        route_investigation,
        {
            "tools": "tools",
            "plan_fix": "plan_fix",
        },
    )

    # Sau khi thực thi tool xong -> quay lại node investigate để LLM đọc kết quả
    workflow.add_edge("tools", "investigate")

    # Sau khi lập plan_fix -> chuyển sang execute_fix
    workflow.add_edge("plan_fix", "execute_fix")

    # Kết thúc sau khi thực thi bản vá
    workflow.add_edge("execute_fix", END)

    # 4. Checkpointer để lưu snapshot state (mặc định lưu bền vững vào SQLite)
    if checkpointer is None:
        checkpointer = PersistentSqliteSaver()

    # 5. Biên dịch đồ thị kèm Breakpoint ngắt TRƯỚC KHI node execute_fix chạy
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["execute_fix"],
    )

    return app


# Đối tượng graph dùng cho module chạy trực tiếp
incident_app = create_incident_graph()
