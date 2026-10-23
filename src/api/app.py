import logging
import os
import sys
import uuid

# Dam bao import duoc module tu thu muc goc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from langchain_core.messages import HumanMessage

from src.agent.graph import incident_app
from src.agent.nodes import extract_text_content
from src.api.schemas import (
    IncidentApprovalRequest,
    IncidentApprovalResponse,
    IncidentStatusResponse,
    IncidentTriggerRequest,
    IncidentTriggerResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("incident-api")

app = FastAPI(
    title="Incident Response AI Agent API",
    description="REST API cho he thong tu dong dieu tra su co voi FastAPI BackgroundTasks va LangGraph Human-in-the-Loop",
    version="1.2.1",
)


def run_agent_workflow_task(thread_id: str, initial_input: dict):
    """Tac vu chay nen cho Agent: dieu tra su co cho toi khi gap breakpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    logger.info(f"Bat dau tac vu nen dieu tra cho thread: {thread_id}")
    try:
        for _ in incident_app.stream(initial_input, config=config):
            pass
        logger.info(f"Tac vu nen hoan tat hoac da tam dung tai breakpoint cho thread: {thread_id}")
    except Exception as exc:
        logger.error(f"Loi trong tac vu nen cho thread {thread_id}: {str(exc)}", exc_info=True)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Giao dien truc quan 3 buoc giup kiem thu toan bo luong hoat dong cua Agent."""
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Incident Response AI Agent Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen py-10 px-4">
        <div class="max-w-4xl mx-auto bg-slate-800 rounded-xl shadow-2xl border border-slate-700 p-8">
            <h1 class="text-2xl font-bold text-center text-blue-400 mb-2">Autonomous Incident Response Agent</h1>
            <p class="text-center text-slate-400 text-sm mb-8">Trực quan hóa quy trình AI điều tra sự cố & Phê duyệt Human-in-the-Loop</p>

            <!-- Thanh tien trinh 3 buoc -->
            <div class="flex items-center justify-between mb-8 relative">
                <div class="w-full absolute top-1/2 h-1 bg-slate-700 -z-0"></div>
                
                <!-- Buoc 1 -->
                <div class="flex flex-col items-center relative z-10">
                    <div id="step-1-badge" class="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg transition-all">1</div>
                    <span id="step-1-label" class="text-xs font-semibold text-blue-400 mt-2">Báo cáo sự cố</span>
                </div>

                <!-- Buoc 2 -->
                <div class="flex flex-col items-center relative z-10">
                    <div id="step-2-badge" class="w-10 h-10 rounded-full bg-slate-700 text-slate-400 flex items-center justify-center font-bold shadow-lg transition-all">2</div>
                    <span id="step-2-label" class="text-xs font-semibold text-slate-400 mt-2">Duyệt bản vá</span>
                </div>

                <!-- Buoc 3 -->
                <div class="flex flex-col items-center relative z-10">
                    <div id="step-3-badge" class="w-10 h-10 rounded-full bg-slate-700 text-slate-400 flex items-center justify-center font-bold shadow-lg transition-all">3</div>
                    <span id="step-3-label" class="text-xs font-semibold text-slate-400 mt-2">Hoàn tất & PR</span>
                </div>
            </div>

            <!-- Khung Buoc 1 -->
            <div id="panel-step-1" class="space-y-4">
                <div class="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <label class="block text-sm font-medium mb-1">Tên Service:</label>
                    <input type="text" id="service-name" value="payment_service" class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                    
                    <label class="block text-sm font-medium mt-3 mb-1">Mô tả sự cố:</label>
                    <textarea id="issue-desc" rows="2" class="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500">Khách thanh toán bị treo và báo lỗi timeout sau 3 giây</textarea>

                    <button id="btn-trigger" onclick="triggerIncident()" class="mt-4 w-full bg-blue-600 hover:bg-blue-500 font-semibold py-2.5 rounded text-sm transition-all shadow-md">
                        Bắt đầu điều tra sự cố (Bước 1)
                    </button>
                </div>
            </div>

            <!-- Trạng thái Loading / Polling -->
            <div id="loading-spinner" class="hidden my-8 text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent mb-2"></div>
                <p id="loading-text" class="text-sm text-blue-300 font-medium">Agent đang truy vấn log và phân tích lỗi ngầm...</p>
            </div>

            <!-- Khung Buoc 2 -->
            <div id="panel-step-2" class="hidden space-y-4">
                <div class="bg-slate-700/50 p-4 rounded-lg border border-yellow-600/50">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-semibold text-yellow-400">Breakpoint: Agent đang chờ con người phê duyệt</span>
                        <span id="display-thread-id" class="text-xs text-slate-400 font-mono"></span>
                    </div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">Bản phân tích lỗi & Code vá do Gemini đề xuất:</label>
                    <pre id="proposed-fix-content" class="bg-slate-900 p-4 rounded text-xs text-slate-200 overflow-x-auto max-h-80 border border-slate-700 whitespace-pre-wrap"></pre>

                    <div class="flex gap-4 mt-4">
                        <button onclick="submitApproval(true)" class="flex-1 bg-emerald-600 hover:bg-emerald-500 font-semibold py-2.5 rounded text-sm transition-all shadow-md">
                            Duyệt bản vá & Tạo PR (Approve)
                        </button>
                        <button onclick="submitApproval(false)" class="flex-1 bg-rose-600 hover:bg-rose-500 font-semibold py-2.5 rounded text-sm transition-all shadow-md">
                            Từ chối bản vá (Reject)
                        </button>
                    </div>
                </div>
            </div>

            <!-- Khung Buoc 3 -->
            <div id="panel-step-3" class="hidden space-y-4">
                <div class="bg-slate-700/50 p-6 rounded-lg border border-emerald-600/50 text-center">
                    <div class="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center text-xl mb-3">✓</div>
                    <h3 class="text-lg font-bold text-emerald-400 mb-2">Quy trình đã hoàn tất!</h3>
                    <p id="final-output-content" class="text-sm text-slate-300 bg-slate-900 p-4 rounded border border-slate-700 text-left"></p>
                    <button onclick="resetFlow()" class="mt-6 bg-slate-600 hover:bg-slate-500 text-white font-semibold py-2 px-6 rounded text-sm transition-all">
                        Thử nghiệm ca mới
                    </button>
                </div>
            </div>
        </div>

        <script>
            let currentThreadId = "";
            let pollTimer = null;

            async function triggerIncident() {
                const serviceName = document.getElementById("service-name").value;
                const issueDesc = document.getElementById("issue-desc").value;
                currentThreadId = "WEB-TEST-" + Math.random().toString(36).substring(2, 8).toUpperCase();

                document.getElementById("btn-trigger").disabled = true;
                document.getElementById("loading-spinner").classList.remove("hidden");
                document.getElementById("loading-text").innerText = "Đang gửi sự cố tới Agent...";

                try {
                    const res = await fetch("/incidents/trigger", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            service_name: serviceName,
                            issue_description: issueDesc,
                            thread_id: currentThreadId
                        })
                    });

                    if (!res.ok) throw new Error("Lỗi khi trigger incident");

                    document.getElementById("loading-text").innerText = "Agent đang điều tra log và tạo bản vá (khoảng 5-10 giây)...";
                    
                    // Bat dau polling kiem tra tien do
                    pollTimer = setInterval(checkStatus, 2000);
                } catch (err) {
                    alert("Có lỗi: " + err.message);
                    document.getElementById("btn-trigger").disabled = false;
                    document.getElementById("loading-spinner").classList.add("hidden");
                }
            }

            async function checkStatus() {
                try {
                    const res = await fetch(`/incidents/${currentThreadId}/status`);
                    if (!res.ok) return;
                    const data = await res.json();

                    // Chi chuyen sang buoc 2 khi Agent thuc su den breakpoint cua execute_fix va da co noi dung ban va
                    if (data.status === "paused_at_breakpoint" && data.proposed_fix) {
                        clearInterval(pollTimer);
                        document.getElementById("loading-spinner").classList.add("hidden");
                        
                        // Cap nhat badge buoc
                        document.getElementById("step-1-badge").className = "w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-white shadow-lg";
                        document.getElementById("step-1-badge").innerHTML = "✓";
                        document.getElementById("step-2-badge").className = "w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg";
                        document.getElementById("step-2-label").className = "text-xs font-semibold text-blue-400 mt-2";

                        // Hien thi panel buoc 2
                        document.getElementById("panel-step-1").classList.add("hidden");
                        document.getElementById("panel-step-2").classList.remove("hidden");
                        document.getElementById("display-thread-id").innerText = "Thread: " + currentThreadId;
                        document.getElementById("proposed-fix-content").innerText = data.proposed_fix;
                    }
                } catch (err) {
                    console.error("Loi khi polling status:", err);
                }
            }

            async function submitApproval(isApproved) {
                document.getElementById("panel-step-2").classList.add("hidden");
                document.getElementById("loading-spinner").classList.remove("hidden");
                document.getElementById("loading-text").innerText = isApproved ? "Đang tiếp tục thực thi tạo Pull Request..." : "Đang hủy thao tác...";

                try {
                    const res = await fetch(`/incidents/${currentThreadId}/approve`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ approved: isApproved })
                    });

                    if (!res.ok) throw new Error("Lỗi khi gửi phê duyệt");
                    const data = await res.json();

                    document.getElementById("loading-spinner").classList.add("hidden");

                    // Cap nhat badge buoc 3
                    document.getElementById("step-2-badge").className = "w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-white shadow-lg";
                    document.getElementById("step-2-badge").innerHTML = "✓";
                    document.getElementById("step-3-badge").className = "w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-white shadow-lg";
                    document.getElementById("step-3-badge").innerHTML = "✓";
                    document.getElementById("step-3-label").className = "text-xs font-semibold text-emerald-400 mt-2";

                    // Hien thi panel ket qua
                    document.getElementById("panel-step-3").classList.remove("hidden");
                    document.getElementById("final-output-content").innerText = data.final_output;
                } catch (err) {
                    alert("Có lỗi: " + err.message);
                    document.getElementById("panel-step-2").classList.remove("hidden");
                    document.getElementById("loading-spinner").classList.add("hidden");
                }
            }

            function resetFlow() {
                location.reload();
            }
        </script>
    </body>
    </html>
    """


@app.get("/health", tags=["System"])
def health_check():
    """Kiem tra trang thai hoat dong cua dich vu."""
    return {"status": "ok", "service": "incident-response-agent"}


@app.post(
    "/incidents/trigger",
    response_model=IncidentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Incidents"],
)
def trigger_incident(payload: IncidentTriggerRequest, background_tasks: BackgroundTasks):
    """Tiep nhan su co va day vao tac vu chay nen (BackgroundTasks), phan hoi ngay lap tuc."""
    thread_id = payload.thread_id or f"INCIDENT-{uuid.uuid4().hex[:8].upper()}"

    initial_input = {
        "messages": [
            HumanMessage(
                content=f"Service '{payload.service_name}' gap su co: {payload.issue_description}. Hay tra cuu log va phan tich."
            )
        ],
        "service_name": payload.service_name,
        "issue_description": payload.issue_description,
        "proposed_fix": "",
        "approval_status": "pending",
    }

    # Day quy trinh vao chay nen
    background_tasks.add_task(run_agent_workflow_task, thread_id, initial_input)

    return IncidentTriggerResponse(
        thread_id=thread_id,
        status="processing",
        next_node=None,
        proposed_fix=None,
        message="Agent da tiep nhan su co va dang xu ly trong background. Kiem tra trang thai qua endpoint GET /incidents/{thread_id}/status.",
    )


@app.get(
    "/incidents/{thread_id}/status",
    response_model=IncidentStatusResponse,
    tags=["Incidents"],
)
def get_incident_status(thread_id: str):
    """Kiem tra tien do, lay ban va de xuat khi Agent da cham breakpoint."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

    # Truong hop Agent chua khoi tao hoac chua co du lieu
    if not snapshot or not snapshot.values:
        return IncidentStatusResponse(
            thread_id=thread_id,
            status="processing",
            approval_status="pending",
            next_node=None,
            proposed_fix=None,
            is_paused=False,
        )

    next_nodes = list(snapshot.next) if snapshot.next else []
    proposed_fix = snapshot.values.get("proposed_fix")
    
    # Diem ngat chi thuc su bat khi Agent da chay xong plan_fix va dang dung truoc execute_fix
    is_paused = ("execute_fix" in next_nodes) and bool(proposed_fix)

    if is_paused:
        current_status = "paused_at_breakpoint"
    elif snapshot.values.get("approval_status") in ["approved", "rejected"]:
        current_status = "completed"
    else:
        current_status = "processing"

    return IncidentStatusResponse(
        thread_id=thread_id,
        status=current_status,
        approval_status=snapshot.values.get("approval_status"),
        next_node=next_nodes[0] if next_nodes else None,
        proposed_fix=proposed_fix,
        is_paused=is_paused,
    )


@app.post(
    "/incidents/{thread_id}/approve",
    response_model=IncidentApprovalResponse,
    tags=["Incidents"],
)
def approve_incident_fix(thread_id: str, payload: IncidentApprovalRequest):
    """Gui quyet dinh phe duyet de Agent tiep tuc thuc thi tao PR hoac huy bo."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = incident_app.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Khong tim thay phien lam viec voi thread_id '{thread_id}'.",
        )

    if not snapshot.next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phien lam viec '{thread_id}' khong o trang thai cho duyet.",
        )

    decision = "approved" if payload.approved else "rejected"

    incident_app.update_state(
        config,
        {"approval_status": decision},
        as_node="plan_fix",
    )

    try:
        # Resume do thi de hoan tat node execute_fix
        for _ in incident_app.stream(None, config=config):
            pass

        final_snapshot = incident_app.get_state(config)
        messages = final_snapshot.values.get("messages", [])
        final_output = extract_text_content(messages[-1].content) if messages else ""

        return IncidentApprovalResponse(
            thread_id=thread_id,
            status=decision,
            final_output=final_output,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loi khi resume Agent: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)