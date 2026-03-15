export interface User {
  id: string;
  email: string;
  name: string;
  role: 'org_admin' | 'security_admin' | 'data_owner' | 'developer';
  organization: Organization;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: PlanTier;
}

export type PlanTier = 'free' | 'pro' | 'enterprise';

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
  organization_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'Bearer';
  expires_in: number;
}

export interface LoginResponse {
  user: User;
  tokens: TokenResponse;
}

export interface SignupResponse {
  user: User;
  tokens: TokenResponse;
}
