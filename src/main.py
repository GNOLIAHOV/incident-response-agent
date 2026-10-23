import os
import sys
from dotenv import load_dotenv

# Bổ sung thư mục gốc của dự án vào đường dẫn tìm kiếm của Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("Loi: Chua tim thay GOOGLE_API_KEY trong file .env!")
    print("Hay mo file .env va them dong: GOOGLE_API_KEY=\"AIzaSy...\"")
    sys.exit(1)

from langchain_core.messages import HumanMessage
from src.agent.graph import incident_app


def run_incident_workflow():
    config = {"configurable": {"thread_id": "INCIDENT-2026-001"}}

    initial_input = {
        "messages": [
            HumanMessage(
                content="Service 'auth_service' dang lien tuc vang loi 500 khi xac thuc token nguoi dung. Hay tra cuu log va tim nguyen nhan."
            )
        ],
        "service_name": "auth_service",
        "issue_description": "Loi 500 xac thuc token auth_service",
        "proposed_fix": "",
        "approval_status": "pending",
    }

    print("\n" + "=" * 60)
    print("GIAI DOAN 1: AGENT BAT DAU DIEU TRA VA DE XUAT BAN VA")
    print("=" * 60)

    for event in incident_app.stream(initial_input, config=config):
        for node_name, state_update in event.items():
            print(f"-> Hoan thanh Node: [{node_name}]")

    snapshot = incident_app.get_state(config)

    print("\n" + "=" * 60)
    print("HE THONG TAM DUNG: HUMAN-IN-THE-LOOP (HITL) BREAKPOINT")
    print("=" * 60)
    print(f"Node tiep theo bi chan lai: {snapshot.next}")
    print("\nBan va do Agent de xuat:\n")
    print(snapshot.values.get("proposed_fix", "(Chua co noi dung)"))
    print("-" * 60)

    user_choice = input("\nBan co dong y phe duyet ban va nay de tao PR khong? (y/n): ").strip().lower()

    if user_choice == "y":
        approval_decision = "approved"
        print("\nBan da duyet ban va. Dang gui tin hieu tiep tuc chay Agent...")
    else:
        approval_decision = "rejected"
        print("\nBan da tu choi ban va. Dang huy bo thao tac...")

    incident_app.update_state(
        config,
        {"approval_status": approval_decision},
        as_node="plan_fix",
    )

    print("\n" + "=" * 60)
    print("GIAI DOAN 2: TIEP TUC GRAPH VOI QUYET DINH CUA CON NGUOI")
    print("=" * 60)

    for event in incident_app.stream(None, config=config):
        for node_name, state_update in event.items():
            print(f"-> Hoan thanh Node: [{node_name}]")

    final_snapshot = incident_app.get_state(config)
    last_message = final_snapshot.values["messages"][-1]

    print("\n" + "=" * 60)
    print("KET QUA CUOI CUNG:")
    print("=" * 60)
    print(last_message.content)


if __name__ == "__main__":
    run_incident_workflow()