# Dockerization & Real GitHub PR Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package `incident-response-agent` into a production-grade multi-stage Docker container with persistent SQLite storage, and integrate real GitHub PR and Issue creation via GitHub REST API with safe offline simulation fallback.

**Architecture:** A native `GitHubClient` using Python `httpx` interfaces with GitHub REST API v3 to branch, commit incident patch artifacts (`incidents/patches/INC-xxx-{service}.md`), and open PRs/Issues against a configurable default repository. A multi-stage `Dockerfile` with non-root `appuser` and `docker-compose.yml` orchestrates the containerized service and mounts persistent SQLite data volumes.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, httpx, Docker, Docker Compose, Pytest, SQLite.

**Spec:** [docs/superpowers/specs/2026-10-30-dockerization-and-github-pr-integration-design.md](file:///d:/Projects/incident-response-agent/docs/superpowers/specs/2026-10-30-dockerization-and-github-pr-integration-design.md)

## Global Constraints

- **Strict Local Git:** NEVER run `git push`. All commits must remain strictly local.
- **Backward Compatibility:** All existing 33 pytest tests must pass without breaking contracts (`status: created`).
- **Safe Fallback:** If `GITHUB_TOKEN` is unset or empty, the system must transparently fall back to simulation mode without failing incidents or raising unhandled exceptions.
- **Container Security:** Container must run as unprivileged `appuser` (non-root) and protect SQLite database files across container lifecycle events.

## Review Focus

1. **Missing or Expired `GITHUB_TOKEN`:** Must not crash agent graph execution; returns structured simulated PR/Issue metadata.
2. **Repository Slug Resolution:** Must map relative names (e.g. `backend/auth-service`) cleanly to `{GITHUB_OWNER}/{GITHUB_DEFAULT_REPO}` so GitHub API endpoints do not 404.
3. **Commit Existing vs New File:** When committing `incidents/patches/{incident_id}-{service_slug}.md`, query blob SHA if file exists to prevent GitHub HTTP 422 Conflict.
4. **Volume Permissions:** Container `/app/data` must be writable by `appuser` (UID 1001) so SQLite WAL mode can write `incidents.db`.
5. **No Token Leaks:** Neither logs, timeline events, nor Docker images should expose raw `GITHUB_TOKEN`.

---

### Task 1: GitHub Settings & Native REST Client (`GitHubClient`)

**Files:**
- Modify: `src/core/config.py`
- Create: `src/tools/github_client.py`
- Test: `tests/test_github_client.py`

**Interfaces:**
- Consumes: `settings.GITHUB_TOKEN`, `settings.GITHUB_OWNER`, `settings.GITHUB_DEFAULT_REPO` from `src.core.config`.
- Produces: `GitHubClient.create_patch_pull_request(repo, branch, title, patch_content, incident_id, service_slug) -> dict` and `GitHubClient.create_issue(repo, title, body, labels) -> dict`.

- [ ] **Step 1: Write failing test in `tests/test_github_client.py`**

```python
import pytest
from src.tools.github_client import GitHubClient

def test_github_client_fallback_mode():
    client = GitHubClient(token="")
    assert not client.is_configured()
    
    pr_result = client.create_patch_pull_request(
        repo="backend/auth-service",
        branch="fix/auth-service-patch",
        title="fix(auth-service): null pointer",
        patch_content="Sample patch",
        incident_id="INC-101",
        service_slug="auth-service",
    )
    assert pr_result["status"] == "created"
    assert pr_result["simulated"] is True
    assert "https://github.com" in pr_result["pr_url"]
    
    issue_result = client.create_issue(
        repo="backend/auth-service",
        title="[SRE Prevention] Hardening",
        body="Action item",
        labels=["sre", "prevention"],
    )
    assert issue_result["status"] == "created"
    assert issue_result["simulated"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_github_client.py -v`  
Expected: FAIL (ModuleNotFoundError or ImportError: cannot import name 'GitHubClient').

- [ ] **Step 3: Update `src/core/config.py` and implement `GitHubClient` in `src/tools/github_client.py`**

Add `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_DEFAULT_REPO` in `src/core/config.py`.  
Implement `GitHubClient` using `httpx`:
- `resolve_repo(repo: str) -> str`: If repo contains `/` and owner is set, normalizes to valid GitHub `{owner}/{repo}` format.
- `create_or_update_branch(repo_full, branch_name, base_branch="main")`
- `commit_patch_file(repo_full, branch_name, file_path, content, commit_message)`
- `create_patch_pull_request(...)`
- `create_issue(...)`
- Full offline fallback when `token` is empty or API returns error.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_github_client.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes locally**

```bash
git add src/core/config.py src/tools/github_client.py tests/test_github_client.py
git commit -m "feat(github): implement GitHubClient with REST API integration and simulation fallback"
```

---

### Task 2: Connect GitHub Client to SRE Tools & Agent Nodes

**Files:**
- Modify: `src/tools/incident_tools.py:42-47`
- Modify: `src/tools/postmortem_tools.py:76-91`
- Modify: `src/agent/nodes.py:230-286`
- Test: `tests/test_agent.py`, `tests/test_postmortem_tools.py`, `tests/test_sre_workflow.py`

**Interfaces:**
- Consumes: `GitHubClient` from `src.tools.github_client`.
- Produces: Updated `create_github_pr` and `create_github_prevention_issue` langchain tools returning structured, compatible results, and `execute_fix_node` dynamically binding `github_pr_url`.

- [ ] **Step 1: Write integration test for real/simulated PR generation in `tests/test_sre_workflow.py`**

Verify that running the graph to resolution produces a valid `github_pr_url` and stores it into `IncidentState`.

- [ ] **Step 2: Run test to check current behavior**

Run: `pytest tests/test_sre_workflow.py -v`  
Expected: Runs against old mock.

- [ ] **Step 3: Update `incident_tools.py`, `postmortem_tools.py`, and `nodes.py`**

- In `src/tools/incident_tools.py`: Update `create_github_pr` to invoke `github_client.create_patch_pull_request(...)` and return a backward-compatible success string including the PR URL.
- In `src/tools/postmortem_tools.py`: Update `create_github_prevention_issue` to invoke `github_client.create_issue(...)` and return dict with `{"status": "created", ...}`.
- In `src/agent/nodes.py`: In `execute_fix_node`, extract the resulting PR URL and issue URL dynamically and record them in the state and timeline.

- [ ] **Step 4: Run full test suite to verify 0 regressions**

Run: `pytest tests/ -v`  
Expected: PASS (All 34+ tests pass).

- [ ] **Step 5: Commit changes locally**

```bash
git add src/tools/incident_tools.py src/tools/postmortem_tools.py src/agent/nodes.py tests/
git commit -m "feat(agent): wire GitHubClient into incident execution nodes and post-mortem tools"
```

---

### Task 3: Production Dockerization & Docker Compose Setup

**Files:**
- Create: `.dockerignore`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Modify: `README.md`
- Test: Configuration validation & local run verification

**Interfaces:**
- Exposes: Container port `8000`, HTTP endpoint `/health`, static dashboard `/`.
- Mounts: `./data:/app/data` (persistent volume).
- Injects: `.env` environment variables (`GOOGLE_API_KEY`, `GITHUB_TOKEN`, `PORT`).

- [ ] **Step 1: Create `.dockerignore`**

Exclude `.venv`, `.git`, `__pycache__`, `tests`, `*.db`, `.pytest_cache`, `docs`.

- [ ] **Step 2: Create multi-stage `Dockerfile`**

- Base: `python:3.11-slim`
- User: Non-root `appuser` (UID 1001)
- Persistence: `/app/data` directory owned by `appuser`
- Healthcheck: `HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`
- Entrypoint: `uvicorn src.api.app:app --host 0.0.0.0 --port 8000`

- [ ] **Step 3: Create `docker-compose.yml`**

Define `incident-agent` service with build context, ports `8000:8000`, volume `./data:/app/data`, `.env` injection, and restart policy.

- [ ] **Step 4: Update `README.md` with Docker and GitHub Token setup guide**

Document how to run via Docker Compose, configure `GITHUB_TOKEN`, and verify health.

- [ ] **Step 5: Verify all tests and syntax**

Run: `pytest tests/ -v`  
Expected: PASS.

- [ ] **Step 6: Commit changes locally**

```bash
git add .dockerignore Dockerfile docker-compose.yml README.md
git commit -m "feat(docker): add production multi-stage Dockerfile and docker-compose deployment"
```
