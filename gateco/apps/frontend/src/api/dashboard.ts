import { apiGet } from './client';

export interface DashboardStats {
  retrievals_today: number;
  retrievals_allowed: number;
  retrievals_denied: number;
  connectors_connected: number;
  connectors_error: number;
  idps_connected: number;
  idps_principal_count: number;
  last_idp_sync: string | null;
  recent_denied: RecentDeniedRetrieval[];
  total_bound_vectors: number;
  total_vectors: number;
  overall_coverage_pct: number | null;
  connectors_policy_ready: number;
}

export interface RecentDeniedRetrieval {
  id: string;
  query: string;
  principal_name: string;
  denial_reason: string;
  timestamp: string;
}

export function getDashboardStats(): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/dashboard/stats');
}
