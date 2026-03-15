export type Classification = 'public' | 'internal' | 'confidential' | 'restricted';

export type Sensitivity = 'low' | 'medium' | 'high' | 'critical';

export type EncryptionMode = 'none' | 'at_rest' | 'envelope' | 'full';

export interface GatedResource {
  id: string;
  title: string;
  description: string | null;
  classification: Classification;
  sensitivity: Sensitivity;
  domain: string;
  labels: string[];
  chunk_ids: string[];
  acl_refs: string[];
  encryption_mode: EncryptionMode;
  source_connector_id: string;
  source_connector_name: string;
  policy_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface GatedResourceDetail extends GatedResource {
  chunks: ResourceChunk[];
  applicable_policies: ApplicablePolicy[];
  recent_access: RecentAccess[];
}

export interface ResourceChunk {
  id: string;
  index: number;
  preview: string;
  encrypted: boolean;
  vector_id: string;
}

export interface ApplicablePolicy {
  id: string;
  name: string;
  type: 'rbac' | 'abac' | 'rebac';
  effect: 'allow' | 'deny';
}

export interface RecentAccess {
  id: string;
  principal_name: string;
  outcome: 'allowed' | 'denied';
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    pagination: PaginationMeta;
  };
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
