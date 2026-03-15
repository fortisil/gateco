import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryKeys';
import { getPolicies, createPolicy, updatePolicy, deletePolicy, activatePolicy, archivePolicy } from '@/api/policies';
import type { CreatePolicyRequest } from '@/api/policies';

export function usePolicies() {
  return useQuery({
    queryKey: queryKeys.policies.list(),
    queryFn: getPolicies,
  });
}

export function useCreatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreatePolicyRequest) => createPolicy(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.policies.all }),
  });
}

export function useUpdatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreatePolicyRequest> }) => updatePolicy(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.policies.all }),
  });
}

export function useDeletePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deletePolicy(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.policies.all }),
  });
}

export function useActivatePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => activatePolicy(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.policies.all }),
  });
}

export function useArchivePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => archivePolicy(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.policies.all }),
  });
}
