"""Trigger a fresh live incident end-to-end to demo Telegram HITL approval.
Runs the multi-agent swarm up to hitl_gate, then pauses waiting for human approval.
"""

import sys
from pathlib import Path
from langchain_core.messages import HumanMessage

# Ensure Windows console uses UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agent.graph import incident_app

def trigger_demo_incident(incident_id: str = "INC-LIVE-002"):
    print("=" * 65)
    print(f"🚨 ĐANG KÍCH HOẠT SỰ CỐ LIVE MỚI: {incident_id}")
    print("Dịch vụ: auth_service | Mức độ: P1 Critical")
    print("Triệu chứng: High rate of HTTP 500 TypeError in verify_jwt()")
    print("=" * 65)

    config = {"configurable": {"thread_id": incident_id}}
    initial_input = {
        "messages": [
            HumanMessage(
                content="[ALERT] Dịch vụ 'auth_service' gặp sự cố nghiêm trọng P1: Crash 500 trong hàm verify_jwt. Cứu nạn và tạo bản vá khẩn cấp."
            )
        ],
        "incident_id": incident_id,
        "service_name": "auth_service",
        "severity": "P1",
        "issue_description": "High rate of HTTP 500 TypeError in verify_jwt()",
        "alert_source": "prometheus_webhook",
        "proposed_fix": "",
        "approval_status": "pending",
        "timeline": [],
    }

    print("\n▶️ Multi-Agent Swarm bắt đầu chu trình điều phối...")
    for step in incident_app.stream(initial_input, config=config):
        node_name = list(step.keys())[0] if step else "unknown"
        print(f"  ✓ Specialist hoàn tất: {node_name}")

    snapshot = incident_app.get_state(config)
    next_nodes = list(snapshot.next) if snapshot.next else []
    print("\n⏸️ GRAPH ĐÃ DỪNG TẠI BREAKPOINT HITL GATE:")
    print(f"  • Trạng thái hiện tại: {snapshot.values.get('approval_status')}")
    print(f"  • Node kế tiếp đang chờ: {next_nodes}")
    print(f"  • Bản vá đã gửi lên Telegram!")
    print("=" * 65)

if __name__ == "__main__":
    trigger_demo_incident()
