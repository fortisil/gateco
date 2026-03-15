import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/api/queryKeys';
import { getPipelines, createPipeline, updatePipeline, runPipeline, getPipelineRuns } from '@/api/pipelines';
import type { CreatePipelineRequest } from '@/types/pipeline';

export function usePipelines() {
  return useQuery({
    queryKey: queryKeys.pipelines.list(),
    queryFn: getPipelines,
  });
}

export function useCreatePipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreatePipelineRequest) => createPipeline(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.pipelines.all }),
  });
}

export function useUpdatePipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreatePipelineRequest> }) => updatePipeline(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.pipelines.all }),
  });
}

export function useRunPipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => runPipeline(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pipelines.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.pipelines.runs(id) });
    },
  });
}

export function usePipelineRuns(id: string) {
  return useQuery({
    queryKey: queryKeys.pipelines.runs(id),
    queryFn: () => getPipelineRuns(id),
    enabled: !!id,
  });
}
