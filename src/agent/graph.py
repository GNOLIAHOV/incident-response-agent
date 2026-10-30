from langgraph.graph import END, START, StateGraph

from src.agent.checkpointer import PersistentSqliteSaver
from src.agent.nodes import triage_node
from src.agent.state import IncidentState
from src.agent.swarm.supervisor import supervisor_node
from src.agent.swarm.workers import (
    hitl_gate_node,
    investigator_worker,
    patching_worker,
    remediation_worker,
    scribe_worker,
)


def route_supervisor(state: IncidentState) -> str:
    """Hàm điều kiện phân nhánh từ Incident Commander Supervisor."""
    next_worker = state.get("next_worker", "FINISH")
    if next_worker in ("escalate", "FINISH"):
        return END
    return next_worker


def create_incident_graph(checkpointer=None):
    """Khởi tạo và biên dịch đồ thị xử lý sự cố Multi-Agent SRE Swarm kèm cổng kiểm duyệt HITL."""
    workflow = StateGraph(IncidentState)

    # 1. Đăng ký các Nodes: Triage, Supervisor và 4 Specialist Workers + HITL Gate
    workflow.add_node("triage", triage_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("remediation", remediation_worker)
    workflow.add_node("investigator", investigator_worker)
    workflow.add_node("patching", patching_worker)
    workflow.add_node("hitl_gate", hitl_gate_node)
    workflow.add_node("scribe", scribe_worker)

    # 2. Thiết lập luồng thực thi (Edges)
    workflow.add_edge(START, "triage")
    workflow.add_edge("triage", "supervisor")

    # Phân nhánh từ Supervisor tới từng Specialist Worker
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "remediation": "remediation",
            "investigator": "investigator",
            "patching": "patching",
            "hitl": "hitl_gate",
            "scribe": "scribe",
            END: END,
        },
    )

    # Các worker báo cáo ngược về Supervisor sau khi hoàn tất nhiệm vụ
    workflow.add_edge("remediation", "supervisor")
    workflow.add_edge("investigator", "supervisor")
    workflow.add_edge("patching", "hitl_gate")
    workflow.add_edge("hitl_gate", "supervisor")
    workflow.add_edge("scribe", END)

    # 3. Checkpointer để lưu snapshot state (mặc định lưu bền vững vào SQLite)
    if checkpointer is None:
        checkpointer = PersistentSqliteSaver()

    # 4. Biên dịch đồ thị kèm Breakpoint ngắt TRƯỚC KHI hitl_gate chạy
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_gate"],
    )

    return app


# Đối tượng graph dùng cho API và background task
incident_app = create_incident_graph()
