# Autonomous SRE Incident Response Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-black?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage_Build-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![Pytest](https://img.shields.io/badge/Pytest-36%2F36_Passed-0A9EDC?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=flat-square&logo=sqlite)](https://www.sqlite.org/)

An enterprise-grade autonomous Site Reliability Engineering (SRE) AI platform designed under the golden principle:
> **"Mitigate First, Fix Later"** — Automatically ingests alerts, executes immediate emergency remediation to restore service uptime, dispatches War Room notifications, synthesizes verified code patches via Human-in-the-Loop review with an interactive feedback loop, creates real GitHub Pull Requests and Issues, and auto-generates Google SRE-standard Post-Mortem reports.

---

## 1. Key Highlights & Core Capabilities

* **Automated Alert Ingestion & Triage:** Supports Prometheus Alertmanager / Grafana Webhooks (`POST /alerts/webhook`) with automatic severity classification (`P1-Critical`, `P2-High`, `P3-Medium`).
* **Automated Emergency Remediation (Mitigate First):** Automatically executes simulated infrastructure runbooks (`restart_container`, `rollback_deployment`, `apply_traffic_shedding`) in seconds before deep code diagnosis.
* **War Room Live Notification Dispatch:** Formats and dispatches incident status cards to team collaboration channels (Slack/Discord/Teams).
* **Persistent SQLite Checkpointing (`PersistentSqliteSaver`):** Checkpoints active graph state and breakpoints into a local SQLite database (`data/incidents.db`) with WAL mode, surviving process reloads and multi-worker execution.
* **Human-in-the-Loop Gate with Rejection Feedback Loop:** Reviewers can approve or reject with specific feedback (e.g., *"Use dict.get instead of try-except"*). The agent ingests feedback and automatically refines the patch.
* **Real GitHub Pull Request & Issue Integration:** Creates real feature branches, commits incident patch artifacts (`incidents/patches/INC-xxx-{service}.md`), and opens Pull Requests and prevention Issues via GitHub REST API v3 (with graceful simulation fallback when offline/unconfigured).
* **Google SRE Post-Mortem Generation:** Upon approval, the agent automatically compiles an official Post-Mortem report (Timeline, MTTD, MTTR, 5 Whys, Action Items) and opens tracking issues on GitHub.
* **Containerized Production Deployment:** Production-ready multi-stage `Dockerfile` (non-root `appuser`) with `docker-compose.yml` and persistent volume mounts for SQLite data.
* **Interactive 4-Step Visual Dashboard:** Web interface featuring a War Room Live Timeline, feedback modal, and Post-Mortem Markdown viewer.
* **100% Automated Test Suite:** 36 comprehensive unit and API integration tests running in ~1.8 seconds.

---

## 2. System Architecture (5-Stage SRE Lifecycle)

```text
                     [ Prometheus / Grafana / Sentry Alert ]
                                       │
                                       ▼ (POST /alerts/webhook)
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 1: INGESTION & TRIAGE (FastAPI -> Background Task)                     │
│  ├── Parse alert payload (service, error_type, metrics, stack trace)          │
│  └── Classify Severity: P1-Critical / P2-High / P3-Medium                     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 2: EMERGENCY MITIGATION & WAR ROOM (Node: mitigate_node)                │
│  ├── Execute immediate runbook: Restart container / Rollback / Shed traffic   │
│  ├── Dispatch War Room Alert (Slack/Discord Webhook + Web Dashboard)          │
│  └── Record Mitigation Timestamp (for MTTD / MTTR calculation)                │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 3: DEEP ROOT CAUSE ANALYSIS (Node: investigate_node)                    │
│  ├── Query error logs & stack traces                                          │
│  ├── Analyze code and synthesize minimal safe patch                           │
│  └── Validate code syntax with Python AST                                     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 4: HUMAN-IN-THE-LOOP GATE (LangGraph Breakpoint)                        │
│  ├── System Pauses at 'execute_fix'                                           │
│  ├── Operator Reviews Proposed Patch on Web Dashboard / API                   │
│  │                                                                            │
│  ├── [ REJECT WITH FEEDBACK ] ──────────────────────────────────────────┐     │
│  │    Operator: "Use dict.get instead"                                  │     │
│  │    Agent loops back to Stage 3, adapts code, and pauses again        │     │
│  │                                                                      ▼     │
│  └── [ APPROVE PATCH ] ──> Resumes Graph ───────────────────────────────┘     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 5: RESOLUTION & POST-MORTEM (Node: execute_fix_node)                    │
│  ├── Create GitHub Branch, Commit Patch & Open Real Pull Request              │
│  ├── Generate Google SRE-style Post-Mortem Report (Timeline, 5 Whys, MTTR)    │
│  ├── Create GitHub Prevention Issue for engineering backlog                   │
│  └── Update War Room with Resolution Summary                                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Project Directory Structure

```text
incident-response-agent/
├── Dockerfile                    # Multi-stage production container build (non-root appuser)
├── docker-compose.yml            # Container orchestration with volume persistence
├── .dockerignore                 # Excluded directories and artifacts
├── docs/                         # Specifications & Implementation Plans
│   └── superpowers/
│       ├── specs/
│       │   ├── 2026-10-30-autonomous-sre-engine-design.md
│       │   └── 2026-10-30-dockerization-and-github-pr-integration-design.md
│       └── plans/
│           ├── 2026-10-30-autonomous-sre-engine.md
│           └── 2026-10-30-dockerization-and-github-pr-integration.md
├── scripts/                      # Diagnostic and helper scripts
│   └── check_models.py           # Check available Gemini models for API key
├── src/
│   ├── core/                     # Central configuration management
│   │   ├── __init__.py
│   │   └── config.py             # Settings (API keys, GitHub tokens, paths)
│   ├── agent/                    # LangGraph core workflow
│   │   ├── __init__.py
│   │   ├── checkpointer.py       # PersistentSqliteSaver (SQLite-backed state persistence)
│   │   ├── graph.py              # 5-stage StateGraph compilation & HITL breakpoint
│   │   ├── nodes.py              # triage, mitigate, investigate, plan_fix, execute_fix
│   │   └── state.py              # Extended IncidentState schema
│   ├── api/                      # REST API & Web Dashboard layer
│   │   ├── static/
│   │   │   └── dashboard.html    # Interactive 4-step TailwindCSS web dashboard
│   │   ├── __init__.py
│   │   ├── app.py                # FastAPI endpoints & background task dispatchers
│   │   └── schemas.py            # Pydantic request / response validation schemas
│   ├── tools/                    # Tool definitions for SRE capabilities
│   │   ├── __init__.py
│   │   ├── github_client.py      # Native GitHub REST API client with simulation fallback
│   │   ├── incident_tools.py     # query_error_logs, create_github_pr
│   │   ├── mitigation_tools.py   # restart_container, rollback_deployment, apply_traffic_shedding
│   │   ├── communication_tools.py # post_war_room_alert, generate_war_room_card
│   │   └── postmortem_tools.py   # generate_google_sre_postmortem, create_github_prevention_issue
│   ├── __init__.py
│   └── main.py                   # Module entrypoint delegate
├── tests/                        # 36 unit and integration tests
│   ├── test_agent.py
│   ├── test_communication_tools.py
│   ├── test_github_client.py
│   ├── test_mitigation_tools.py
│   ├── test_postmortem_tools.py
│   ├── test_sre_api.py
│   ├── test_sre_workflow.py
│   └── test_state_and_persistence.py
├── .env                          # Local environment variables (API keys & Tokens)
├── .gitignore
├── main.py                       # Root CLI entry point
├── pytest.ini                    # Pytest configuration
├── README.md
└── requirements.txt
```

---

## 4. Configuration & Environment Variables

Copy or edit your `.env` file with the required keys:

```dotenv
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DEFAULT_TEMPERATURE=0.2

# GitHub Integration (Optional - falls back to simulation mode if empty)
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_OWNER=GNOLIAHOV
GITHUB_DEFAULT_REPO=incident-response-agent
```

> **Note on GitHub Token:** If `GITHUB_TOKEN` is provided with `repo` scope, the agent will open real Pull Requests and create real Issues on GitHub. If left empty, the agent transparently uses simulated fallback URLs (`https://github.com/{owner}/{repo}/pull/142`), allowing full local testing without live credentials.

---

## 5. Running the Application

### Option A: Running with Docker Compose (Recommended for Production)

1. Build and start the service in background:
```bash
docker compose up -d --build
```

2. Check container logs:
```bash
docker compose logs -f
```

3. Access Dashboard:
* **Interactive Dashboard:** [http://localhost:8000/](http://localhost:8000/)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

4. Stop the service:
```bash
docker compose down
```

### Option B: Local Python Environment

1. Activate your virtual environment and install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI Server & Dashboard:
```bash
uvicorn src.api.app:app --reload --port 8000
```

3. Interactive Terminal CLI Mode:
```bash
python main.py
```

---

## 6. Automated Testing

Run all 36 unit and integration tests:
```bash
pytest -v
```

Expected output:
```text
============================= 36 passed in 1.80s ==============================
```

---

## 7. License

This project is licensed under the [MIT License](LICENSE).
