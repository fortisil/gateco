import { useQuery } from '@tanstack/react-query';
import { getMe } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { queryKeys } from '@/api/queryKeys';

export function useMe() {
  const { isAuthenticated, setUser } = useAuthStore();

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      const user = await getMe();
      setUser(user);
      return user;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}
