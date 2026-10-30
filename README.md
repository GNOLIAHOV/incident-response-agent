# Autonomous Incident Response AI Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-black?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev/)
[![Pytest](https://img.shields.io/badge/Pytest-15%2F15_Passed-0A9EDC?style=flat-square&logo=pytest)](https://docs.pytest.org/)

An autonomous software reliability engineering (SRE) AI agent designed for **automated root cause analysis (RCA)**, **code patch synthesis**, and **safe deployment via a Human-in-the-Loop (HITL) approval gate** before opening GitHub Pull Requests.

---

## 1. Key Highlights & Core Capabilities

* **Autonomous Log Investigation:** Automatically queries system logs (`query_error_logs`) to extract stack traces, error messages, and offending source lines without requiring manual engineer diagnosis.
* **Dynamic Multi-Service Resolution:** Intelligently adapts to any reporting microservice (e.g., `auth_service`, `payment_service`, `inventory_service`), dynamically generating service-specific repositories, patch branches, and pull request titles.
* **Root Cause Analysis with Gemini:** Integrates Google Gemini (`gemini-2.5-flash` or configurable) with lazy initialization and structured system prompts to diagnose application logic bugs, network timeouts, and concurrency deadlocks.
* **Human-in-the-Loop (HITL) Safety Gate:** Enforces LangGraph dynamic breakpoints via `interrupt_before=["execute_fix"]`. The AI synthesizes the fix but **cannot modify source code or open PRs** until an authorized human engineer explicitly approves.
* **Asynchronous Background Processing:** Uses FastAPI `BackgroundTasks` to immediately acknowledge incident webhooks (`HTTP 202 Accepted`), offloading the multi-step LangGraph workflow to background execution to avoid HTTP client timeouts.
* **Interactive 3-Step Visual Dashboard:** Includes a clean web dashboard (separated in `src/api/static/dashboard.html`) with real-time status polling for incident reporting, patch inspection, and one-click approve/reject actions.
* **Dual Execution Modes:** Fully supports both **Interactive CLI workflow** (`python main.py`) and **REST API / Web Dashboard** (`uvicorn src.api.app:app`).
* **100% Automated Test Suite:** 15 comprehensive unit and API integration tests running in ~1.1 seconds.

---

## 2. System Architecture

```text
[ Monitoring / Alerting Webhook / Engineer ]
                     │
                     ▼ (POST /incidents/trigger)
┌────────────────────────────────────────────────────────┐
│ FastAPI Application (BackgroundTasks)                  │
│  └── Dispatches background worker with thread_id       │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ LangGraph StateGraph Execution                         │
│                                                        │
│   [investigate] <─── (Fetch additional logs) ──────┐   │
│          │                                         │   │
│          ▼                                         │   │
│    [tools (query_error_logs)] ─────────────────────┘   │
│          │                                             │
│          ▼                                             │
│     [plan_fix] (RCA & code patch proposal)             │
│          │                                             │
│     BREAKPOINT (State halted before execute_fix)       │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼ Client Polling (GET /incidents/{id}/status)
┌────────────────────────────────────────────────────────┐
│ Human-in-the-Loop Operator Gate                        │
│ (Web Dashboard / Swagger UI / CLI)                     │
│   ├── [ Approve ] ──> (POST /approve)                  │
│   └── [ Reject  ] ──> (POST /approve)                  │
└──────────┬─────────────────────────────────────────────┘
           │
           ▼ Resumes graph with human approval state
┌────────────────────────────────────────────────────────┐
│     [execute_fix] (Create Pull Request on GitHub)      │
│          │                                             │
│          ▼                                             │
│        [END]                                           │
└────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

- **Language:** Python 3.10+
- **Agent Orchestration:** LangGraph 0.2+, LangChain Core 0.3+
- **LLM Engine:** Google Gemini (`gemini-2.5-flash`) via `langchain-google-genai`
- **Web & API Backend:** FastAPI 0.110+, Uvicorn, Pydantic v2
- **Testing:** Pytest 8.x, HTTPX
- **Environment Management:** `python-dotenv`

---

## 4. Project Directory Structure

```text
incident-response-agent/
├── scripts/                      # Helper & diagnostic utilities
│   └── check_models.py           # Diagnostic script to list active Gemini API models
├── src/
│   ├── core/                     # Centralized configuration management
│   │   ├── __init__.py
│   │   └── config.py             # Settings class (API keys, model configuration, paths)
│   ├── agent/                    # LangGraph core workflow
│   │   ├── __init__.py
│   │   ├── graph.py              # StateGraph compilation with HITL interrupt breakpoint
│   │   ├── nodes.py              # Nodes: investigate, tool_node, plan_fix, execute_fix
│   │   └── state.py              # IncidentState TypedDict schema
│   ├── api/                      # REST API & Web Dashboard layer
│   │   ├── static/
│   │   │   └── dashboard.html    # Standalone interactive TailwindCSS web dashboard
│   │   ├── __init__.py
│   │   ├── app.py                # FastAPI endpoints & background task dispatchers
│   │   └── schemas.py            # Pydantic request / response validation schemas
│   ├── tools/                    # Tool definitions for LLM tool calling
│   │   ├── __init__.py
│   │   └── incident_tools.py     # query_error_logs, create_github_pr
│   ├── __init__.py
│   └── main.py                   # Module entrypoint delegate
├── tests/                        # Comprehensive test suite
│   └── test_agent.py             # 15 automated unit & integration tests
├── .env                          # Local environment variables
├── .gitignore
├── main.py                       # Root CLI entry point (Run interactive terminal flow)
├── README.md
└── requirements.txt              # Production and testing dependencies
```

---

## 5. Environment Configuration

Create a `.env` file in the project root:

```env
# Google Gemini Developer API Key (Required)
GOOGLE_API_KEY="AIzaSyYourGeminiApiKeyHere"

# Gemini Model Selection (Optional, defaults to gemini-2.5-flash)
GEMINI_MODEL="gemini-2.5-flash"

# Model Temperature (Optional, defaults to 0.2)
DEFAULT_TEMPERATURE=0.2
```

---

## 6. Installation & Setup

### 1. Clone Repository & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/<your-username>/incident-response-agent.git
cd incident-response-agent

# Create and activate virtual environment
# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 7. Running the Application

### Mode 1: Interactive CLI Workflow
Run the end-to-end incident investigation directly in your terminal with interactive human approval:

```bash
python main.py
```

**Terminal Workflow Experience:**
1. The agent ingests the error alert and queries logs via `query_error_logs`.
2. The agent diagnoses the root cause and synthesizes a proposed code patch.
3. The graph hits the breakpoint and pauses:
   ```text
   HE THONG TAM DUNG: HUMAN-IN-THE-LOOP (HITL) BREAKPOINT
   Node tiep theo bi chan lai: ('execute_fix',)
   Ban va do Agent de xuat: [...]
   Ban co dong y phe duyet ban va nay de tao PR khong? (y/n):
   ```
4. Typing `y` resumes graph execution to open the GitHub PR; typing `n` halts and cancels the operation.

---

### Mode 2: Web Dashboard & REST API
Start the FastAPI server:

```bash
uvicorn src.api.app:app --reload --port 8000
```

Access the interfaces via your browser:
* **Interactive Web Dashboard:** [http://localhost:8000/](http://localhost:8000/)
* **Interactive Swagger UI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 8. Automated Testing

Run the test suite with Pytest:

```bash
pytest tests/ -v
```

All 15 unit and integration tests run in ~1.1 seconds with zero external network dependencies:
- Tools execution (`query_error_logs`, `create_github_pr`)
- Message formatting and Gemini list/dict parsing
- Conditional graph routing (`tools` vs. `plan_fix`)
- Plan and fix nodes execution under both approved and rejected states
- FastAPI API endpoints (health, background task trigger, state inspection, approval gate)

---

## 9. Diagnostic Scripts

To inspect which Gemini models are available for your API key:

```bash
python scripts/check_models.py
```

---

## 10. API Reference

### 1. Trigger Incident Investigation
* **Endpoint:** `POST /incidents/trigger`
* **Status:** `202 Accepted`
* **Request Body:**
  ```json
  {
    "service_name": "payment_service",
    "issue_description": "Connection timeout after 3000ms",
    "thread_id": "INCIDENT-PAYMENT-001"
  }
  ```
* **Response:**
  ```json
  {
    "thread_id": "INCIDENT-PAYMENT-001",
    "status": "processing",
    "next_node": null,
    "proposed_fix": null,
    "message": "Agent đã tiếp nhận sự cố và đang xử lý trong background..."
  }
  ```

---

### 2. Poll Incident Status & Inspect Fix Proposal
* **Endpoint:** `GET /incidents/{thread_id}/status`
* **Response (When Paused at HITL Breakpoint):**
  ```json
  {
    "thread_id": "INCIDENT-PAYMENT-001",
    "status": "paused_at_breakpoint",
    "approval_status": "pending",
    "next_node": "execute_fix",
    "proposed_fix": "Root cause: Timeout communicating with payment gateway at 10.0.4.12:443. Proposed fix: Introduce Circuit Breaker pattern with backoff retry...",
    "is_paused": true
  }
  ```

---

### 3. Submit Human Approval Decision
* **Endpoint:** `POST /incidents/{thread_id}/approve`
* **Request Body:**
  ```json
  {
    "approved": true
  }
  ```
* **Response:**
  ```json
  {
    "thread_id": "INCIDENT-PAYMENT-001",
    "status": "approved",
    "final_output": "Da hoan thanh: Success: Pull Request #142 'fix(payment-service): resolve Connection timeout' created on backend/payment-service:fix/payment-service-incident-patch."
  }
  ```

---

## 11. Supported Incident Scenarios (Mock Logs)

1. **Application Logic Error (`auth_service`):**
   * *Log Signature:* `TypeError: 'NoneType' object is not subscriptable in verify_jwt() at /app/auth/tokens.py line 42`.
   * *Agent Outcome:* Identifies missing `user_id` in token payload and synthesizes safe dictionary key access.
2. **Infrastructure Network Timeout (`payment_service`):**
   * *Log Signature:* `ConnectionTimeout: Failed to connect to payment gateway at 10.0.4.12:443 after 3000ms`.
   * *Agent Outcome:* Diagnoses external gateway unresponsiveness and synthesizes a Circuit Breaker with exponential retry backoff.
3. **High-Concurrency Database Deadlock (`inventory_service`):**
   * *Log Signature:* `psycopg2.errors.DeadlockDetected on relation 'stock_items' under 12,000 req/s flash sale spike`.
   * *Agent Outcome:* Identifies conflicting locks between transactions and proposes atomic Redis lua deductions and ordered row locking.

---

## 12. License

This project is licensed under the [MIT License](LICENSE).
