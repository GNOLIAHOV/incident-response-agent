# Autonomous Incident Response AI Agent

An autonomous software incident response agent designed for automated root cause analysis (RCA), code fix synthesis, and safe deployment via a Human-in-the-Loop (HITL) approval gate before opening GitHub Pull Requests.

## Key Highlights and Core Capabilities

* Autonomous Investigation: The agent automatically queries system logs to extract stack traces, error codes, and source file locations instead of relying on manual engineer input.

* Root Cause Analysis & Fix Planning: Integrates Google Gemini (gemini-3.5-flash-lite) to diagnose application logic bugs, network infrastructure timeouts, and advanced concurrency deadlocks.

* Human-in-the-Loop Safety Gate: Implements LangGraph dynamic breakpoints via interrupt_before=["execute_fix"] to ensure no source code changes or pull requests are executed without engineer approval.

* Asynchronous Background Processing: Combines FastAPI with BackgroundTasks to immediately acknowledge incident alerts (HTTP 202 Accepted) and run the LangGraph workflow in the background, avoiding HTTP connection timeouts during LLM reasoning.

* Interactive 3-Step Web Dashboard: Provides an automated polling web interface that guides the operator through incident intake, patch review, and pull request generation.

* Comprehensive Automated Testing: Achieves a 100% pass rate across 15 automated unit and integration tests using Pytest and HTTPX.

## System Architecture

```
[Monitoring / Alerting / User]
            │  (POST /incidents/trigger)
            ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Application (BackgroundTasks)                  │
└───────────────────────┬────────────────────────────────┘
                        │ Dispatches background worker
                        ▼
┌────────────────────────────────────────────────────────┐
│ LangGraph StateGraph Workflow                          │
│                                                        │
│  [investigate] <─── (Fetch additional logs) ───────┐   │
│         │                                          │   │
│         ▼                                          │   │
│   [tools (query_error_logs)] ──────────────────────┘   │
│         │                                              │
│         ▼                                              │
│    [plan_fix] (Root cause analysis & fix proposal)     │
│         │                                              │
│    BREAKPOINT (Halts before execute_fix)               │
└─────────┬──────────────────────────────────────────────┘
          │
          ▼ Client Polling (GET /incidents/{id}/status)
┌────────────────────────────────────────────────────────┐
│ Web Dashboard / REST API (Human-in-the-Loop)           │
│  ├── [ Approve ] ──> (POST /approve)                   │
│  └── [ Reject  ] ──> (POST /approve)                   │
└─────────┬──────────────────────────────────────────────┘
          │
          ▼ Resumes graph execution
┌────────────────────────────────────────────────────────┐
│    [execute_fix] (Create GitHub Pull Request)          │
│         │                                              │
│         ▼                                              │
│       [END]                                            │
└────────────────────────────────────────────────────────┘
```

## Tech Stack

* Programming Language: Python 3.10+
* Orchestration Framework: LangGraph (StateGraph, MemorySaver)
* LLM Engine: Google Gemini (gemini-3.5-flash-lite) via langchain-google-genai
* Web & API Backend: FastAPI, Uvicorn, Pydantic v2
* Automated Testing: Pytest, HTTPX

## Project Structure

```
incident-response-agent/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # StateGraph definition and MemorySaver
│   │   ├── nodes.py          # Core nodes (investigate, plan_fix, execute_fix)
│   │   └── state.py          # IncidentState TypedDict schema
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py            # FastAPI endpoints, background task runner & dashboard
│   │   └── schemas.py        # Pydantic request and response models
│   └── tools/
│       ├── __init__.py
│       └── incident_tools.py # LangChain tools (query_error_logs, create_github_pr)
├── tests/
│   ├── __init__.py
│   └── test_agent.py         # 15 unit and integration tests
├── .gitignore
├── README.md
└── requirements.txt
```

## Installation and Setup

### 1. Clone Repository and Set Up Virtual Environment

```powershell
git clone https://github.com/<your-github-username>/incident-response-agent.git
cd incident-response-agent

python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY="AIzaSy..."
```

### 4. Run the Application

```powershell
python -m uvicorn src.api.app:app --reload --port 8000
```

Access the application via browser:
* Interactive Web Dashboard: `http://127.0.0.1:8000/`
* API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

## Automated Testing

Run the entire test suite with Pytest:

```powershell
pytest tests/ -v
```

## Test Scenarios

1. Source Code Logic Failure (auth_service):
   * Description: Continuous HTTP 500 errors during token authentication.
   * Result: Agent detects TypeError at /app/auth/tokens.py line 42 and synthesizes a safe payload dictionary access patch.

2. Network Infrastructure Failure (payment_service):
   * Description: Client checkout requests hanging and returning timeout errors after 3000ms.
   * Result: Agent identifies connection timeouts to the payment gateway IP and proposes a circuit breaker and retry backoff strategy.

3. High-Concurrency Deadlock (inventory_service):
   * Description: Flash sale traffic spike (12,000 req/s) causing database transaction deadlocks.
   * Result: Agent diagnoses lock contention between ExclusiveLock and ShareLock on the stock_items table, proposing ordered row updates and transaction isolation tuning.