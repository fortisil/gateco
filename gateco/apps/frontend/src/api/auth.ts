import { apiGet, apiPost, apiPatch } from './client';
import type { User, LoginRequest, LoginResponse, SignupRequest, SignupResponse, TokenResponse } from '@/types/auth';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return apiPost<LoginResponse>('/auth/login', data, false);
}

export async function signup(data: SignupRequest): Promise<SignupResponse> {
  return apiPost<SignupResponse>('/auth/signup', data, false);
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }, false);
}

export async function logout(): Promise<void> {
  return apiPost<void>('/auth/logout');
}

export async function getMe(): Promise<User> {
  return apiGet<User>('/users/me');
}

export async function exchangeCode(code: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/exchange', { code }, false);
}

export async function updateMe(data: Partial<Pick<User, 'name'>>): Promise<User> {
  return apiPatch<User>('/users/me', data);
}
