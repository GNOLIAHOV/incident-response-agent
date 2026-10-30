import os
import shutil
import tempfile
from langchain_core.messages import HumanMessage
from langgraph.graph import START, StateGraph

from src.agent.checkpointer import PersistentSqliteSaver
from src.agent.state import IncidentState


def test_incident_state_schema_fields():
    """Kiểm tra IncidentState hỗ trợ đầy đủ các trường SRE mở rộng."""
    state: IncidentState = {
        "messages": [HumanMessage(content="alert")],
        "incident_id": "INC-001",
        "service_name": "payment_service",
        "severity": "P1",
        "issue_description": "Database connection timeout",
        "alert_source": "prometheus",
        "mitigation_action_taken": "restart_container",
        "mitigation_status": "success",
        "timeline": [{"time": "2026-10-30T10:00:00Z", "event": "Alert received", "stage": "ingest"}],
        "investigation_summary": "DB pool exhausted",
        "proposed_fix": "Increase max connections",
        "reviewer_feedback": "Check connection leak too",
        "approval_status": "pending",
        "github_pr_url": "https://github.com/repo/pull/1",
        "post_mortem_report": "# Post-Mortem Report",
    }
    assert state["severity"] == "P1"
    assert state["mitigation_status"] == "success"
    assert len(state["timeline"]) == 1
    assert state["reviewer_feedback"] == "Check connection leak too"


def test_persistent_sqlite_saver_lifecycle():
    """Kiểm tra PersistentSqliteSaver ghi nhận checkpoint và phục hồi chính xác từ file SQLite."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_checkpoints.db")

    try:
        # 1. Khởi tạo checkpointer và StateGraph đơn giản
        saver1 = PersistentSqliteSaver(db_path=db_path)
        builder = StateGraph(IncidentState)

        def step_node(state: IncidentState):
            return {
                "mitigation_action_taken": "restart_container",
                "timeline": [{"time": "t1", "event": "node_run", "stage": "test"}],
            }

        builder.add_node("step", step_node)
        builder.add_edge(START, "step")
        app1 = builder.compile(checkpointer=saver1)

        config = {"configurable": {"thread_id": "THREAD-SRE-TEST"}}
        initial_input = {
            "messages": [HumanMessage(content="initial")],
            "service_name": "auth_service",
            "severity": "P2",
            "issue_description": "Token error",
            "approval_status": "pending",
        }

        # Chạy graph
        app1.invoke(initial_input, config=config)

        # 2. Tạo instance checkpointer mới trỏ cùng file DB (mô phỏng server restart)
        saver2 = PersistentSqliteSaver(db_path=db_path)
        app2 = builder.compile(checkpointer=saver2)

        snapshot = app2.get_state(config)
        assert snapshot is not None
        assert snapshot.values.get("service_name") == "auth_service"
        assert snapshot.values.get("mitigation_action_taken") == "restart_container"
        assert snapshot.values.get("severity") == "P2"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
