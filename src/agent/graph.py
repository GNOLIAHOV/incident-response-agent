from langgraph.graph import END, START, StateGraph

from src.agent.checkpointer import PersistentSqliteSaver
from src.agent.nodes import (
    execute_fix_node,
    investigate_node,
    mitigate_node,
    plan_fix_node,
    route_investigation,
    tool_node,
    triage_node,
)
from src.agent.state import IncidentState


def create_incident_graph(checkpointer=None):
    """Khởi tạo và biên dịch đồ thị xử lý sự cố 5 giai đoạn kèm cơ chế Human-in-the-Loop."""

    # 1. Khởi tạo StateGraph với Schema IncidentState
    workflow = StateGraph(IncidentState)

    # 2. Đăng ký các Nodes vào đồ thị theo chu trình SRE 5 giai đoạn
    workflow.add_node("triage", triage_node)
    workflow.add_node("mitigate", mitigate_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("plan_fix", plan_fix_node)
    workflow.add_node("execute_fix", execute_fix_node)

    # 3. Thiết lập luồng thực thi (Edges)
    # Giai đoạn 1: Tiếp nhận và phân loại độ nghiêm trọng
    workflow.add_edge(START, "triage")

    # Giai đoạn 2: Tự động dập lửa khẩn cấp (Mitigate First)
    workflow.add_edge("triage", "mitigate")

    # Giai đoạn 3: Phân tích nguyên nhân gốc rễ (Deep RCA)
    workflow.add_edge("mitigate", "investigate")

    # Phân nhánh điều kiện: Gọi tools tra cứu log hay đã có đủ log để chuyển sang plan_fix
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

    # Giai đoạn 4: Sau khi lập plan_fix -> chuyển sang execute_fix (Sẽ chạm Breakpoint)
    workflow.add_edge("plan_fix", "execute_fix")

    # Giai đoạn 5: Sau khi thực thi bản vá và xuất Post-Mortem -> Kết thúc
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
