export interface PrincipalAttributes {
  department: string;
  clearance: string;
  org_path: string;
  [key: string]: string;
}

export interface Principal {
  id: string;
  external_id: string;
  display_name: string;
  email: string;
  groups: string[];
  roles: string[];
  attributes: PrincipalAttributes;
  identity_provider_id: string;
  identity_provider_name: string;
  status: 'active' | 'inactive' | 'suspended';
  last_seen: string | null;
  created_at: string;
  updated_at: string;
}
