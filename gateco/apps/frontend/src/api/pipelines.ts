import { apiGet, apiPost, apiPatch } from './client';
import type { IngestionPipeline, PipelineRun, CreatePipelineRequest } from '@/types/pipeline';

export async function getPipelines(): Promise<IngestionPipeline[]> {
  const res = await apiGet<{ data: IngestionPipeline[] }>('/pipelines');
  return res.data;
}

export function getPipeline(id: string): Promise<IngestionPipeline> {
  return apiGet<IngestionPipeline>(`/pipelines/${id}`);
}

export function createPipeline(data: CreatePipelineRequest): Promise<IngestionPipeline> {
  return apiPost<IngestionPipeline>('/pipelines', data);
}

export function runPipeline(id: string): Promise<PipelineRun> {
  return apiPost<PipelineRun>(`/pipelines/${id}/run`);
}

export function updatePipeline(id: string, data: Partial<CreatePipelineRequest>): Promise<IngestionPipeline> {
  return apiPatch<IngestionPipeline>(`/pipelines/${id}`, data);
}

export async function getPipelineRuns(id: string): Promise<PipelineRun[]> {
  const res = await apiGet<{ data: PipelineRun[] }>(`/pipelines/${id}/runs`);
  return res.data;
}
