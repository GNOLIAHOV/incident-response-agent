"""Entry point chính để chạy Agent quy trình phản ứng sự cố qua giao diện dòng lệnh (CLI)."""

import sys
from langchain_core.messages import HumanMessage

from src.core.config import settings
from src.agent.graph import incident_app


def run_incident_workflow():
    if not settings.GOOGLE_API_KEY:
        print("Lỗi: Chưa tìm thấy GOOGLE_API_KEY trong file .env!")
        print("Hãy mở file .env và thêm dòng: GOOGLE_API_KEY=\"AIzaSy...\"")
        sys.exit(1)

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
    print("GIAI ĐOẠN 1: AGENT BẮT ĐẦU ĐIỀU TRA VÀ ĐỀ XUẤT BẢN VÁ")
    print("=" * 60)

    for event in incident_app.stream(initial_input, config=config):
        for node_name, state_update in event.items():
            print(f"-> Hoàn thành Node: [{node_name}]")

    snapshot = incident_app.get_state(config)

    print("\n" + "=" * 60)
    print("HỆ THỐNG TẠM DỪNG: HUMAN-IN-THE-LOOP (HITL) BREAKPOINT")
    print("=" * 60)
    print(f"Node tiếp theo bị chặn lại: {snapshot.next}")
    print("\nBản vá do Agent đề xuất:\n")
    print(snapshot.values.get("proposed_fix", "(Chưa có nội dung)"))
    print("-" * 60)

    user_choice = input("\nBạn có đồng ý phê duyệt bản vá này để tạo PR không? (y/n): ").strip().lower()

    if user_choice == "y":
        approval_decision = "approved"
        print("\nBạn đã duyệt bản vá. Đang gửi tín hiệu tiếp tục chạy Agent...")
    else:
        approval_decision = "rejected"
        print("\nBạn đã từ chối bản vá. Đang hủy bỏ thao tác...")

    incident_app.update_state(
        config,
        {"approval_status": approval_decision},
        as_node="hitl_gate",
    )

    print("\n" + "=" * 60)
    print("GIAI ĐOẠN 2: TIẾP TỤC GRAPH VỚI QUYẾT ĐỊNH CỦA CON NGƯỜI")
    print("=" * 60)

    for event in incident_app.stream(None, config=config):
        for node_name, state_update in event.items():
            print(f"-> Hoàn thành Node: [{node_name}]")

    final_snapshot = incident_app.get_state(config)
    messages = final_snapshot.values.get("messages", [])
    last_message = messages[-1].content if messages else "Chu trình Swarm SRE đã xử lý thành công."

    print("\n" + "=" * 60)
    print("KẾT QUẢ CUỐI CÙNG:")
    print("=" * 60)
    print(last_message)

    post_mortem = final_snapshot.values.get("post_mortem_report")
    if post_mortem:
        print("\n" + "=" * 60)
        print("BÁO CÁO GOOGLE SRE POST-MORTEM TỰ ĐỘNG:")
        print("=" * 60)
        print(post_mortem)


if __name__ == "__main__":
    run_incident_workflow()
