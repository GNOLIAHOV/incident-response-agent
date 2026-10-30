# Dockerization & Real GitHub PR Integration Design Document

**Date:** 2026-10-30  
**Project:** `incident-response-agent`  
**Status:** Approved by Human Partner  
**Target Approach:** Approach 1 (GitHub REST API Native Client + Multi-Stage Docker)

---

## 1. Intent & Purpose

Transform `incident-response-agent` into a containerized, production-ready SRE service capable of:
1. Packaging the complete application (FastAPI, LangGraph 5-stage engine, SQLite persistent store, static Web Dashboard) into a secure, portable, production-grade Docker container with data volume persistence.
2. Interacting directly with the official GitHub REST API (v3) using a Personal Access Token (`GITHUB_TOKEN`) to automatically generate branches, commit synthesized incident bugfixes as structured patch documents (`incidents/patches/{incident_id}-{service_slug}.md`), open real Pull Requests, and file preventive GitHub Issues upon incident approval, while maintaining a robust fallback for offline/test environments.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
1. **Real GitHub Pull Request & Issue Creation:**
   - Implement `GitHubClient` using `httpx` to interface with GitHub REST API:
     - Target repository resolved cleanly via `GITHUB_DEFAULT_REPO` and `GITHUB_OWNER` from settings (Decision 2A).
     - Query latest commit SHA of base branch (`main`).
     - Create a feature/fix branch: `fix/{service_slug}-{incident_id_clean}`.
     - Commit the AI-synthesized code fix as an incident patch artifact at `incidents/patches/{incident_id}-{service_slug}.md` (Decision 1A).
     - Open a Pull Request referencing the incident ID, RCA summary, and MTTR.
     - Create a post-incident prevention Issue with proper labels (`sre`, `prevention`, severity).
2. **Graceful Offline / Simulation Fallback:**
   - When `GITHUB_TOKEN` is unset or invalid, seamlessly fallback to deterministic simulation without crashing the SRE lifecycle or failing automated tests.
   - Return `{ "status": "created", "simulated": True, ... }` to guarantee 100% backward compatibility with existing tests.
3. **Production Dockerization:**
   - Multi-stage `Dockerfile` based on `python:3.11-slim`.
   - Run under an unprivileged user (`appuser`, non-root, UID 1001) for container security.
   - Configure a persistent volume mount for `/app/data` to ensure SQLite checkpoint persistence across container reboots.
   - Include Docker healthchecks against `/health`.
4. **`docker-compose.yml` Deployment:**
   - Orchestrate the agent service with port mapping `8000:8000`, volume mounts (`./data:/app/data`), and `.env` secret injection.
5. **100% Test Coverage & Verification:**
   - Add unit tests for `GitHubClient` covering both active token flows (mocked HTTP) and fallback simulation mode.
   - Ensure all existing 33 pytest tests pass without regressions.

### Non-Goals
* Embedding local `git` CLI binaries or managing SSH keys inside the Docker container.
* Automatically auto-merging Pull Requests without human review.

### Anti-Goals
* **No Hardcoded Secrets or Leaked Tokens:** Never commit personal access tokens or passwords into git or Docker images.
* **No Brittle Container Failures on Network Drops:** If GitHub API is unreachable, the agent must log clear diagnostic messages and mark the incident status gracefully rather than crashing the background worker.

---

## 3. Approaches Considered & Human Decisions

### 3.1 Architecture Approach
* **Approach 1 (Selected): GitHub REST API Native Client + Multi-Stage Docker**
  - Ultra-lightweight Docker image, no Git/SSH daemon dependencies inside container, secure token handling, deterministic HTTP mocking in tests.
* **Approach 2 (Rejected): Git CLI Subprocess Inside Container**
  - Image bloat (+150MB), complicated credential helpers and SSH agent forwarding, risk of volume permission mismatches on host.

### 3.2 Human Decisions on Architecture Gaps
* **Decision 1A (Target File Path):** The PR will commit a dedicated incident patch artifact file at `incidents/patches/{incident_id}-{service_slug}.md` containing the diagnosis, full patch diff, and verification steps. This eliminates risky blind-overwriting of production source files and allows human reviewers to inspect the proposal cleanly.
* **Decision 2A (Repository Target Resolution):** The target repository is configured centrally via `GITHUB_DEFAULT_REPO` and `GITHUB_OWNER` in `.env`. If `repo` passed to tools is a relative slug (like `backend/auth-service`), the client routes to `GITHUB_DEFAULT_REPO` (or `{GITHUB_OWNER}/{repo_name}`).
* **Builder Call (Backward Compatibility):** Tools will continue to return `{"status": "created", ...}` in both live and fallback simulation modes so all existing unit tests in `test_postmortem_tools.py` and `test_agent.py` pass without any breaking changes.

---

## 4. Technical Specifications

### 4.1 Configuration Additions (`src/core/config.py`)
```python
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER: str = os.getenv("GITHUB_OWNER", "GNOLIAHOV")
GITHUB_DEFAULT_REPO: str = os.getenv("GITHUB_DEFAULT_REPO", "incident-response-agent")
```

### 4.2 GitHub Client (`src/tools/github_client.py`)
Class `GitHubClient`:
- `__init__(token: Optional[str] = None, owner: Optional[str] = None, default_repo: Optional[str] = None)`
- `is_configured() -> bool`: Returns `True` if `token` is non-empty.
- `resolve_repo_name(repo: str) -> str`: Resolves `{owner}/{repo}` format using `GITHUB_OWNER` and `GITHUB_DEFAULT_REPO`.
- `create_or_update_branch(repo_full: str, branch_name: str, base_branch: str = "main") -> dict`:
  - `GET /repos/{owner}/{repo}/git/ref/heads/{base_branch}` -> get SHA.
  - `POST /repos/{owner}/{repo}/git/refs` (`ref="refs/heads/{branch_name}"`, `sha=...`).
- `commit_patch_file(repo_full: str, branch_name: str, file_path: str, content: str, commit_message: str) -> dict`:
  - Checks if file exists on branch to retrieve existing `sha` if present.
  - `PUT /repos/{owner}/{repo}/contents/{file_path}` with base64 encoded content.
- `open_pull_request(repo: str, branch_name: str, title: str, body: str, base_branch: str = "main") -> dict`:
  - `POST /repos/{owner}/{repo}/pulls` (`title`, `body`, `head=branch_name`, `base=base_branch`).
- `create_issue(repo: str, title: str, body: str, labels: list[str]) -> dict`:
  - `POST /repos/{owner}/{repo}/issues`.
- Fallback logic: If `not is_configured()`, return deterministic dictionary with `"status": "created"`, `"simulated": True`, and mock URLs.

### 4.3 Updating Incident Tools
- Update `src/tools/incident_tools.py` (`create_github_pr`): Delegate to `github_client.create_patch_pull_request(...)`.
- Update `src/tools/postmortem_tools.py` (`create_github_prevention_issue`): Delegate to `github_client.create_issue(...)`.
- Update `src/agent/nodes.py` (`execute_fix_node`): Dynamically consume the generated `pr_url` from client result.

### 4.4 Docker Architecture
- **`.dockerignore`**:
  ```text
  .git
  .venv
  __pycache__
  *.pyc
  .pytest_cache
  tests
  data/*.db
  .env
  docs
  ```
- **`Dockerfile`**:
  - Base: `python:3.11-slim`
  - Install system packages: `curl`
  - Create non-root user: `useradd -m -u 1001 appuser`
  - Set working directory: `/app`
  - Copy `requirements.txt` and install dependencies with `--no-cache-dir`
  - Copy application code: `src/`, `pytest.ini`
  - Create `/app/data` with ownership `appuser:appuser`
  - Switch to `USER appuser`
  - Expose port `8000`
  - `HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1`
  - `CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]`
- **`docker-compose.yml`**:
  - Service: `incident-agent`
  - Build context: `.`
  - Container name: `incident_response_agent`
  - Ports: `"8000:8000"`
  - Volumes: `./data:/app/data`
  - Env File: `.env`
  - Restart: `unless-stopped`

---

## 5. Verification Plan

1. **Automated Unit Tests:**
   - `tests/test_github_client.py`:
     - Test fallback simulation mode when `GITHUB_TOKEN` is missing.
     - Test live REST flow with mocked `httpx` responses (branch ref, commit file, open PR, create issue).
   - Full test suite: Verify that all 33 existing tests + new GitHub client tests pass 100%.
2. **Container Build & Health Verification:**
   - Test Dockerfile syntax and compose schema.
   - Verify `/health` response structure.
