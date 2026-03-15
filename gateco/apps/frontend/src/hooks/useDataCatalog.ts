import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryKeys';
import { getDataCatalog, getDataCatalogItem, updateDataCatalogItem } from '@/api/data-catalog';
import type { DataCatalogFilters } from '@/api/data-catalog';
import type { GatedResource } from '@/types/gated-resource';

export function useDataCatalog(filters?: DataCatalogFilters) {
  return useQuery({
    queryKey: queryKeys.dataCatalog.list(filters as Record<string, unknown>),
    queryFn: () => getDataCatalog(filters),
  });
}

export function useDataCatalogItem(id: string) {
  return useQuery({
    queryKey: queryKeys.dataCatalog.detail(id),
    queryFn: () => getDataCatalogItem(id),
    enabled: !!id,
  });
}

export function useUpdateDataCatalogItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<GatedResource, 'classification' | 'sensitivity' | 'labels'>> }) =>
      updateDataCatalogItem(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.dataCatalog.all }),
  });
}
