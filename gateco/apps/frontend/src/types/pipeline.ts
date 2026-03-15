export type PipelineStatus = 'active' | 'paused' | 'error' | 'running';

export interface EnvelopeConfig {
  encrypt: boolean;
  classify: boolean;
  default_classification: 'public' | 'internal' | 'confidential' | 'restricted';
  default_sensitivity: 'low' | 'medium' | 'high' | 'critical';
  label_extraction: boolean;
}

export interface IngestionPipeline {
  id: string;
  name: string;
  source_connector_id: string;
  source_connector_name: string;
  envelope_config: EnvelopeConfig;
  status: PipelineStatus;
  schedule: string | null;
  last_run: string | null;
  records_processed: number;
  error_count: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  status: 'completed' | 'failed' | 'running';
  records_processed: number;
  errors: number;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface CreatePipelineRequest {
  name: string;
  source_connector_id: string;
  envelope_config: EnvelopeConfig;
  schedule: string | null;
}
