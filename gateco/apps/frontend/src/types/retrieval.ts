export type RetrievalOutcome = 'allowed' | 'partial' | 'denied';

export interface DenialReason {
  chunk_id: string;
  policy_id: string;
  policy_name: string;
  reason: string;
}

export interface PolicyTrace {
  policy_id: string;
  policy_name: string;
  effect: 'allow' | 'deny';
  evaluation_ms: number;
  matched_rules: string[];
}

export interface SecuredRetrieval {
  id: string;
  query: string;
  principal_id: string;
  principal_name: string;
  connector_id: string;
  connector_name: string;
  matched_chunks: number;
  allowed_chunks: number;
  denied_chunks: number;
  outcome: RetrievalOutcome;
  denial_reasons: DenialReason[];
  policy_trace: PolicyTrace[];
  latency_ms: number;
  timestamp: string;
}
