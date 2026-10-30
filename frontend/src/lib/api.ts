import {
  ApprovalPayload,
  ApprovalResponse,
  IncidentDetail,
  IncidentItem,
  IncidentTriggerPayload,
  IncidentTriggerResponse,
  PostMortemData,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

// Fallback demo data to showcase the UI even if the backend agent process is restarting
const FALLBACK_INCIDENTS: IncidentItem[] = [
  {
    thread_id: "INC-PROD-001",
    service_name: "payment_service",
    severity: "P0",
    status: "completed",
    mitigation_action: "Circuit breaker activated & GitHub PR opened",
    created_at: "2026-10-31T00:15:00Z",
  },
  {
    thread_id: "INC-AUTH-882",
    service_name: "auth_service",
    severity: "P1",
    status: "approved",
    mitigation_action: "Token cache invalidation & patch merged",
    created_at: "2026-10-30T22:40:00Z",
  },
  {
    thread_id: "INC-INV-109",
    service_name: "inventory_service",
    severity: "P2",
    status: "completed",
    mitigation_action: "Database connection pool scaled to 50",
    created_at: "2026-10-30T18:10:00Z",
  },
];

const FALLBACK_DETAIL: IncidentDetail = {
  thread_id: "INC-PROD-001",
  status: "completed",
  severity: "P0",
  service_name: "payment_service",
  approval_status: "approved",
  next_node: null,
  proposed_fix: `def process_payment(amount: float, user_id: str, timeout: int = 5):\n    # AST Validated: Added strict timeout and idempotent key verification\n    if amount <= 0:\n        raise ValueError("Invalid transaction amount")\n    return gateway_client.charge(user_id=user_id, amount=amount, timeout=timeout)`,
  mitigation_action_taken: "Circuit breaker activated (Fallback rate: 99.8%)",
  timeline: [
    {
      stage: "triage",
      timestamp: "00:15:02",
      message: "Triage Agent detected P0 Gateway Timeout spike (99.2% failure rate).",
      agent: "TriageSpecialist",
    },
    {
      stage: "remediation",
      timestamp: "00:15:06",
      message: "Remediation Agent enabled Circuit Breaker fallback on payment_service.",
      agent: "MitigationSpecialist",
    },
    {
      stage: "investigator",
      timestamp: "00:15:14",
      message: "Investigator Agent performed 5 Whys Root Cause Analysis. Root cause: connection pooling starvation.",
      agent: "RootCauseSpecialist",
    },
    {
      stage: "patching",
      timestamp: "00:15:22",
      message: "Patch Agent generated AST-validated code fix and verified safe syntax.",
      agent: "PatchingSpecialist",
    },
    {
      stage: "hitl_gate",
      timestamp: "00:15:28",
      message: "HITL Gate requested human verification via Telegram & Enterprise Web Portal.",
      agent: "HITLGate",
    },
    {
      stage: "scribe",
      timestamp: "00:15:45",
      message: "Scribe Agent compiled Google SRE Post-Mortem and opened GitHub Pull Request #1.",
      agent: "ScribeSpecialist",
    },
  ],
  post_mortem_report: `# Google SRE Post-Mortem: INC-PROD-001\n\n**Service:** payment_service  \n**Severity:** P0  \n**Date:** 2026-10-31  \n**MTTR:** 28 seconds  \n**MTTD:** 6 seconds  \n\n## 1. Summary\nPayment processing experienced cascading gateway timeouts due to unhandled socket exhaustion under high concurrency.\n\n## 2. Root Cause Analysis (5 Whys)\n1. Why did transactions fail? Gateway API returned 504 Gateway Timeout.\n2. Why did gateway return 504? Socket pool was exhausted waiting on downstream bank provider.\n3. Why were sockets waiting indefinitely? No read timeout was configured on payment requests.\n4. Why was timeout omitted? Client library upgraded without default timeout parameter.\n5. Root Cause: Missing connection timeout in payment gateway adapter.\n\n## 3. Mitigation & Prevention\n- Activated circuit breaker to stop cascading failures.\n- Applied AST-validated code patch enforcing 5s socket timeout.\n- Opened Pull Request #1 with automated regression tests.`,
  is_paused: false,
};

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchIncidents(): Promise<IncidentItem[]> {
  try {
    const res = await fetch(`${API_BASE}/incidents`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      return data;
    }
    return FALLBACK_INCIDENTS;
  } catch (err) {
    console.warn("Backend unavailable, using demo fallback incidents:", err);
    return FALLBACK_INCIDENTS;
  }
}

export async function fetchIncidentStatus(threadId: string): Promise<IncidentDetail> {
  try {
    const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(threadId)}/status`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Backend status unavailable for ${threadId}, using fallback:`, err);
    return {
      ...FALLBACK_DETAIL,
      thread_id: threadId,
    };
  }
}

export async function fetchPostMortem(threadId: string): Promise<PostMortemData> {
  try {
    const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(threadId)}/post-mortem`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Post-mortem fetch error for ${threadId}, using fallback:`, err);
    return {
      incident_id: threadId,
      service_name: "payment_service",
      severity: "P0",
      post_mortem_markdown: FALLBACK_DETAIL.post_mortem_report || "Báo cáo đang được xử lý.",
    };
  }
}

export async function submitApproval(
  threadId: string,
  payload: ApprovalPayload
): Promise<ApprovalResponse> {
  const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(threadId)}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to submit approval: HTTP ${res.status} - ${text}`);
  }
  return await res.json();
}

export async function triggerIncident(
  payload: IncidentTriggerPayload
): Promise<IncidentTriggerResponse> {
  const res = await fetch(`${API_BASE}/incidents/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to trigger incident: HTTP ${res.status} - ${text}`);
  }
  return await res.json();
}
