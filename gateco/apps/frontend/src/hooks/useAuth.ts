import { useCallback, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import * as authApi from '@/api/auth';
import type { LoginRequest, SignupRequest } from '@/types/auth';

export function useAuth() {
  const { user, isAuthenticated, isLoading, setAuth, clearAuth, setLoading } = useAuthStore();

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    if (storedToken && !isAuthenticated && !isLoading) {
      restoreSession();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const restoreSession = async () => {
    setLoading(true);
    try {
      const user = await authApi.getMe();
      const accessToken = localStorage.getItem('access_token')!;
      const refreshToken = localStorage.getItem('refresh_token') || '';
      setAuth(user, accessToken, refreshToken);
    } catch {
      // Try refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const tokens = await authApi.refresh(refreshToken);
          localStorage.setItem('access_token', tokens.access_token);
          localStorage.setItem('refresh_token', tokens.refresh_token);
          const user = await authApi.getMe();
          setAuth(user, tokens.access_token, tokens.refresh_token);
        } catch {
          clearAuth();
        }
      } else {
        clearAuth();
      }
    }
  };

  const login = useCallback(async (data: LoginRequest) => {
    const response = await authApi.login(data);
    setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token);
    return response;
  }, [setAuth]);

  const signup = useCallback(async (data: SignupRequest) => {
    const response = await authApi.signup(data);
    setAuth(response.user, response.tokens.access_token, response.tokens.refresh_token);
    return response;
  }, [setAuth]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout API errors
    }
    clearAuth();
  }, [clearAuth]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    signup,
    logout,
  };
}
