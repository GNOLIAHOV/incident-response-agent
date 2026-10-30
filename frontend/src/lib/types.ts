export type IncidentSeverity = "P0" | "P1" | "P2" | "P3";

export type IncidentApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "revising"
  | "escalated"
  | "completed";

export type IncidentOverallStatus =
  | "processing"
  | "paused_at_breakpoint"
  | "escalated"
  | "completed";

export interface TimelineEvent {
  stage?: string;
  timestamp?: string;
  message?: string;
  agent?: string;
  details?: Record<string, any>;
  [key: string]: any;
}

export interface IncidentItem {
  thread_id: string;
  service_name: string;
  severity?: IncidentSeverity;
  status?: IncidentApprovalStatus | string;
  mitigation_action?: string;
  created_at?: string;
}

export interface IncidentDetail {
  thread_id: string;
  status: IncidentOverallStatus;
  severity?: IncidentSeverity;
  service_name?: string;
  approval_status?: IncidentApprovalStatus;
  next_node?: string | null;
  proposed_fix?: string | null;
  mitigation_action_taken?: string | null;
  timeline?: TimelineEvent[] | null;
  post_mortem_report?: string | null;
  is_paused: boolean;
}

export interface PostMortemData {
  incident_id: string;
  service_name: string;
  severity: IncidentSeverity;
  post_mortem_markdown: string;
}

export interface ApprovalPayload {
  approved: boolean;
  feedback?: string;
}

export interface ApprovalResponse {
  thread_id: string;
  status: string;
  final_output: string;
  post_mortem_report?: string | null;
}

export interface IncidentTriggerPayload {
  service_name: string;
  issue_description: string;
  thread_id?: string;
}

export interface IncidentTriggerResponse {
  thread_id: string;
  status: string;
  next_node?: string | null;
  proposed_fix?: string | null;
  message: string;
}

export interface GoldenMetrics {
  mttrSeconds: number; // Mean Time to Recover
  mttdSeconds: number; // Mean Time to Detect
  slaPercentage: number;
  totalIncidents: number;
  activeIncidents: number;
  resolvedIncidents: number;
  autonomousResolutionRate: number; // percentage resolved without human rewrite
}

export interface ServiceHealth {
  name: string;
  displayName: string;
  status: "healthy" | "warning" | "critical";
  latencyMs: number;
  uptime: string;
}
