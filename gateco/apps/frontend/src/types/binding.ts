export interface BindingEntry {
  vector_id: string;
  external_resource_id: string;
  classification?: string;
  sensitivity?: string;
  domain?: string;
  labels?: string[];
}

export interface BindResult {
  created_resources: number;
  updated_resources: number;
  created_chunks: number;
  rebound_chunks: number;
  errors: Array<{ external_resource_id: string; reason: string }>;
  coverage_after: number | null;
}

export interface CoverageDetail {
  bound_vector_count: number;
  total_vector_count: number;
  coverage_pct: number | null;
  coverage_approximate: boolean;
  policy_readiness_level: number;
  classification_breakdown: Record<string, number>;
}
