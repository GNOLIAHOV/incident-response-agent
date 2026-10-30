# Autonomous SRE Incident Response Platform (Multi-Agent Swarm)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-black?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage_Build-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![Pytest](https://img.shields.io/badge/Pytest-58%2F58_Passed-0A9EDC?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=flat-square&logo=sqlite)](https://www.sqlite.org/)

An enterprise-grade **Autonomous Site Reliability Engineering (SRE) Multi-Agent Swarm** designed under the golden principle:
> **"Mitigate First, Fix Later"** — An **Incident Commander (Supervisor)** orchestrates specialized autonomous agents (**Remediation**, **Investigator**, **Patching**, and **Scribe**) to immediately stabilize service availability, perform deep RCA, synthesize verified code patches with Human-in-the-Loop review, create real GitHub Pull Requests, and compile official Google SRE Post-Mortem reports.

---

## 1. Key Highlights & Swarm Capabilities

* **Incident Commander (Supervisor Orchestration):** Central supervisory agent dynamically evaluating incident state, delegating tasks to domain specialists, and enforcing a 5-iteration circuit breaker with on-call manual escalation.
* **4 Specialized Autonomous Workers:**
  - 🚒 **Remediation Specialist:** Instant emergency runbook execution (`restart_container`, `rollback_deployment`, `apply_traffic_shedding`) and War Room live alerts.
  - 🔍 **Investigator Specialist:** Autonomous ReAct diagnostic loop querying logs and formulating 5 Whys root cause deduction.
  - 🛠️ **Patching Specialist:** Safe Python AST code synthesis incorporating reviewer feedback upon rejection.
  - 📋 **Scribe & Governance Specialist:** Official Google SRE Post-Mortem generation, GitHub Pull Request creation, and prevention issue filing upon verified human approval.
* **Independent HITL Gate (`hitl_gate`):** An isolated breakpoint node ensuring code modifications and PR creation are strictly gated behind human sign-off.
* **Persistent SQLite Checkpointing (`PersistentSqliteSaver`):** Checkpoints active graph state and breakpoints into a local SQLite database (`data/incidents.db`) with WAL mode, surviving process reloads and container restarts.
* **Real GitHub Pull Request & Issue Integration:** Opens real feature branches (`fix/{service}-{incident_id}`), commits incident patch artifacts (`incidents/patches/INC-xxx-{service}.md`), and creates PRs/Issues via GitHub REST API v3 (with graceful simulation fallback).
* **Containerized Production Deployment:** Production-ready multi-stage `Dockerfile` (non-root `appuser`) with `docker-compose.yml` and persistent volume mounts.
* **Interactive 4-Step Visual Dashboard:** Web interface featuring a War Room Live Timeline, feedback modal, and Post-Mortem Markdown viewer.
* **📱 Interactive Telegram Bot for Remote HITL Approval:** Pushes real-time alerts to on-call mobile phones with interactive Inline Buttons (`[✅ Approve & Open PR]` / `[❌ Reject]`). Engineers can review and trigger fixes anywhere without opening their laptop.
* **100% Automated Test Suite:** 58 comprehensive unit and integration tests running in ~1.6 seconds.

---

## 2. Multi-Agent Swarm Architecture

```text
                     [ Prometheus / Grafana / Sentry Alert ]
                                       │
                                       ▼ (POST /alerts/webhook)
┌───────────────────────────────────────────────────────────────────────────────┐
│ Stage 0: INGESTION & TRIAGE (Node: triage_node)                               │
│  ├── Parse alert payload (service, error_type, metrics, stack trace)          │
│  └── Classify Severity: P1-Critical / P2-High / P3-Medium                     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│              STAGE 1: INCIDENT COMMANDER (Node: supervisor_node)              │
│  ├── Inspects IncidentState (mitigation, investigation, fix, approval)        │
│  ├── Increments swarm_iterations counter (Circuit Breaker limit: 5)           │
│  └── Dispatches to Next Worker:                                               │
│       ├── If not mitigated ──────────────► Remediation Agent                  │
│       ├── If not investigated ───────────► Investigator Agent                 │
│       ├── If fix needed / feedback ──────► Patching Agent                     │
│       ├── If approved ───────────────────► Scribe Agent                       │
│       └── If iterations >= 5 ────────────► Emergency Escalation Pause         │
└───────┬───────────────────┬───────────────────┬───────────────────┬───────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ REMEDIATION  │    │ INVESTIGATOR │    │   PATCHING   │    │    SCRIBE    │
│    AGENT     │    │    AGENT     │    │    AGENT     │    │    AGENT     │
│ (Runbook     │    │ (ReAct Log   │    │ (AST Code    │    │ (GitHub PR   │
│  Mitigation) │    │  Analysis)   │    │  Synthesis)  │    │  Post-Mortem)│
└───────┬──────┘    └───────┬──────┘    └───────┬──────┘    └───────┬──────┘
        │                   │                   │                   │
        └───────────────────┴───────────────────┼───────────────────┘
                                                ▼
                                   ┌─────────────────────────┐
                                   │     HITL_GATE NODE      │
                                   │  (Interrupt / Break)    │
                                   └────────────┬────────────┘
                                                │
                                ┌───────────────┴───────────────┐
                                ▼                               ▼
                        [ REJECT + FEEDBACK ]            [ APPROVE PATCH ]
                                │                               │
                                └──────► Back to Supervisor ◄───┘
```

---

## 3. Project Directory Structure

```text
incident-response-agent/
├── Dockerfile                    # Multi-stage production container build (non-root appuser)
├── docker-compose.yml            # Container orchestration with volume persistence
├── .env.example                  # Enterprise configuration template for customers
├── .dockerignore                 # Excluded directories and artifacts
├── deploy/                       # Enterprise In-VPC deployment manifests
│   └── kubernetes/               # Kubernetes Deployment, Service, PVC, ConfigMap, Secret
├── docs/                         # Specifications & Implementation Plans
│   └── superpowers/
│       ├── specs/
│       │   ├── 2026-10-30-autonomous-sre-engine-design.md
│       │   ├── 2026-10-30-dockerization-and-github-pr-integration-design.md
│       │   └── 2026-10-30-multi-agent-sre-swarm-design.md
│       └── plans/
│           ├── 2026-10-30-autonomous-sre-engine.md
│           ├── 2026-10-30-dockerization-and-github-pr-integration.md
│           └── 2026-10-30-multi-agent-sre-swarm.md
├── scripts/                      # Diagnostic and helper scripts
├── src/
│   ├── core/                     # Central configuration management
│   │   ├── __init__.py
│   │   └── config.py             # Settings (API keys, GitHub tokens, paths)
│   ├── agent/                    # LangGraph core workflow
│   │   ├── swarm/                # Multi-Agent Swarm Modules
│   │   │   ├── __init__.py
│   │   │   ├── prompts.py        # System prompts for Commander & 4 Specialists
│   │   │   ├── supervisor.py     # Incident Commander supervisor logic
│   │   │   └── workers.py        # Remediation, Investigator, Patching, Scribe, HITL
│   │   ├── checkpointer.py       # PersistentSqliteSaver (SQLite-backed persistence)
│   │   ├── graph.py              # Multi-Agent Swarm StateGraph compilation
│   │   ├── nodes.py              # Core nodes & helper routines
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
├── tests/                        # 49 unit and integration tests
│   ├── test_agent.py
│   ├── test_communication_tools.py
│   ├── test_github_client.py
│   ├── test_mitigation_tools.py
│   ├── test_postmortem_tools.py
│   ├── test_sre_api.py
│   ├── test_sre_workflow.py
│   ├── test_state_and_persistence.py
│   └── test_swarm.py             # Multi-Agent Swarm unit and lifecycle tests
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

# Telegram Bot Integration (Optional - mobile alerts & remote HITL buttons)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_or_group_id
TELEGRAM_ENABLED=false
```

---

## 5. Running the Application

### Option A: Running with Docker Compose (Recommended)

1. Build and start the service in background:
```bash
docker compose up -d --build
```

2. Access Dashboard:
* **Interactive Dashboard:** [http://localhost:8000/](http://localhost:8000/)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

3. Stop the service:
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

### Option C: Enterprise Kubernetes Deployment (In-VPC)

For enterprise clusters (EKS, GKE, AKS, or on-premise Kubernetes):

1. Configure secrets and configmap in `deploy/kubernetes/configmap-and-secrets.yaml`.
2. Apply the deployment manifests:
```bash
kubectl apply -f deploy/kubernetes/configmap-and-secrets.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
```
3. Verify pod status:
```bash
kubectl get pods -n sre-agent
```

---

## 6. Remote Mobile Approval via Telegram Bot

The system provides on-call engineers with remote, mobile-friendly incident approval without requiring them to open a laptop:

1. **Create Bot & Obtain Credentials:**
   * Message [@BotFather](https://t.me/botfather) on Telegram: run `/newbot` to get your `TELEGRAM_BOT_TOKEN`.
   * Message [@userinfobot](https://t.me/userinfobot) or add your bot to your SRE War Room group to get the `TELEGRAM_CHAT_ID`.
2. **Configure `.env`:**
   ```dotenv
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   TELEGRAM_CHAT_ID=-1001234567890
   TELEGRAM_ENABLED=true
   ```
3. **Register Webhook with Telegram:**
   Point Telegram to your public API endpoint (via domain or tunneling such as ngrok/Cloudflare Tunnel):
   ```bash
   curl -F "url=https://your-domain.com/telegram/webhook" https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
   ```
4. **How It Works:**
   * When an incident occurs, **Remediation Agent** pushes an emergency mitigation alert to the chat.
   * When **Patching Agent** finishes drafting a safe AST fix, it pauses at `hitl_gate` and pushes an interactive card with `[✅ Duyệt & Mở GitHub PR]` and `[❌ Từ chối bản vá]` buttons directly to the engineer's phone.
   * Tapping the button updates the incident state in SQLite and automatically resumes the workflow in background to create the GitHub Pull Request and compile the Google SRE Post-Mortem.
   * Commands supported in chat: `/status <incident_id>` and `/help`.

---

## 7. Automated Testing

Run all 58 unit and integration tests:
```bash
pytest -v
```

Expected output:
```text
============================= 58 passed in 1.65s ==============================
```

---

## 8. License

This project is licensed under the [MIT License](LICENSE).
