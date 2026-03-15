import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryKeys';
import { getConnectors, createConnector, updateConnector, testConnector, deleteConnector, updateSearchConfig, updateIngestionConfig, bindMetadata, getConnectorCoverage } from '@/api/connectors';
import type { CreateConnectorRequest, SearchConfig, IngestionConfig } from '@/types/connector';
import type { BindingEntry } from '@/types/binding';

export function useConnectors() {
  return useQuery({
    queryKey: queryKeys.connectors.list(),
    queryFn: getConnectors,
  });
}

export function useCreateConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateConnectorRequest) => createConnector(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all }),
  });
}

export function useUpdateConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateConnectorRequest> }) => updateConnector(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all }),
  });
}

export function useTestConnector() {
  return useMutation({
    mutationFn: (id: string) => testConnector(id),
  });
}

export function useDeleteConnector() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteConnector(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all }),
  });
}

export function useUpdateSearchConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, search_config }: { id: string; search_config: SearchConfig }) =>
      updateSearchConfig(id, search_config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all }),
  });
}

export function useUpdateIngestionConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ingestion_config }: { id: string; ingestion_config: IngestionConfig }) =>
      updateIngestionConfig(id, ingestion_config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all }),
  });
}

export function useBindMetadata() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, bindings }: { id: string; bindings: BindingEntry[] }) =>
      bindMetadata(id, bindings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.connectors.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats });
    },
  });
}

export function useConnectorCoverage(id: string) {
  return useQuery({
    queryKey: queryKeys.connectors.detail(id),
    queryFn: () => getConnectorCoverage(id),
    enabled: !!id,
  });
}
