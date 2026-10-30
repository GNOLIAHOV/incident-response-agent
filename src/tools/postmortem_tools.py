from datetime import datetime, timezone
from typing import List, Optional
from langchain_core.tools import tool
from src.tools.github_client import github_client


def generate_google_sre_postmortem(
    incident_id: str,
    service_name: str,
    severity: str,
    issue_description: str,
    timeline: List[dict],
    rca_summary: str,
    fix_applied: str,
    mttd_seconds: int = 30,
    mttr_seconds: int = 120,
) -> str:
    """Tạo báo cáo Post-Mortem sự cố chuẩn theo hướng dẫn của Google SRE Book."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    timeline_rows = []
    for item in timeline:
        t = item.get("time", "N/A")
        stage = item.get("stage", "general").upper()
        event = item.get("event", "")
        timeline_rows.append(f"| {t} | **[{stage}]** {event} |")
    timeline_str = "\n".join(timeline_rows) if timeline_rows else "| N/A | No timeline events recorded |"

    return f"""# 📄 Google SRE Incident Post-Mortem Report

## 1. Incident Summary
* **Incident ID:** `{incident_id}`
* **Target Service:** `{service_name}`
* **Severity Level:** `{severity}`
* **Date Published:** `{now_iso}`
* **Status:** Resolved ✅
* **Initial Symptom:** {issue_description}

---

## 2. Impact & SRE Metrics
* **User Impact:** High-rate 5xx failures affecting user operations during incident duration.
* **Mean Time to Detect (MTTD):** `{mttd_seconds}s` (Time from alert trigger to automated triage).
* **Mean Time to Remediate (MTTR):** `{mttr_seconds}s` (Time from alert trigger to mitigation & patch resolution).

---

## 3. Timeline
| Timestamp | Event Description |
| :--- | :--- |
{timeline_str}

---

## 4. Root Cause Analysis (5 Whys)
1. **Why did the service fail?** The service threw unhandled exceptions resulting in HTTP 500 responses.
2. **Why was the exception thrown?** An essential parameter/field was missing from the incoming payload.
3. **Why was the field missing?** Client requests or upstream token issuers omitted the expected key without schema validation.
4. **Why was it unhandled?** The application code directly accessed the dictionary key without safe fallback mechanisms.
5. **Technical Root Cause:** {rca_summary}

---

## 5. Recovery & Mitigation Action
* **Immediate Remediation:** Service container was restarted / traffic shed to restore availability.
* **Permanent Fix Applied:** {fix_applied}

---

## 6. Preventative Action Items
* [ ] Add automated regression test suite covering null/missing payload fields (`Priority: P1`).
* [ ] Integrate API input schema validation with strict Pydantic/Joi models (`Priority: P2`).
* [ ] Update Grafana dashboard and synthetic alerts for anomaly spikes (`Priority: P2`).
"""


@tool
def create_github_prevention_issue(
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> dict:
    """Tạo GitHub Issue tự động để theo dõi các đầu việc phòng ngừa tái diễn sau sự cố."""
    return github_client.create_issue(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )
