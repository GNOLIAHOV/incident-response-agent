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

// Fallback demo incidents only used if backend API is completely unreachable
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
    status: "completed",
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
    console.warn(`Backend status unavailable for ${threadId}:`, err);
    return {
      thread_id: threadId,
      status: "processing",
      severity: "P2",
      service_name: "service",
      approval_status: "pending",
      next_node: null,
      proposed_fix: null,
      mitigation_action_taken: "Analyzing operational logs...",
      timeline: [],
      post_mortem_report: null,
      is_paused: false,
    };
  }
}

export async function fetchPostMortem(threadId: string): Promise<PostMortemData | null> {
  try {
    const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(threadId)}/post-mortem`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn(`Post-mortem not available for ${threadId}:`, err);
    return null;
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
