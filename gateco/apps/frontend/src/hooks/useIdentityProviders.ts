import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryKeys';
import { getIdentityProviders, createIdentityProvider, updateIdentityProvider, syncIdentityProvider, deleteIdentityProvider } from '@/api/identity-providers';
import type { CreateIdentityProviderRequest } from '@/types/identity-provider';

export function useIdentityProviders() {
  return useQuery({
    queryKey: queryKeys.identityProviders.list(),
    queryFn: getIdentityProviders,
  });
}

export function useCreateIdentityProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateIdentityProviderRequest) => createIdentityProvider(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.identityProviders.all }),
  });
}

export function useUpdateIdentityProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateIdentityProviderRequest> }) => updateIdentityProvider(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.identityProviders.all }),
  });
}

export function useSyncIdentityProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => syncIdentityProvider(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.identityProviders.all }),
  });
}

export function useDeleteIdentityProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteIdentityProvider(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.identityProviders.all }),
  });
}
