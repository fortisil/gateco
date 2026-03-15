/**
 * Re-exports all SDK types.
 */

export type {
  Organization,
  User,
  LoginRequest,
  SignupRequest,
  TokenResponse,
} from "./auth.js";
export { parseTokenResponse, parseUser, parseOrganization } from "./auth.js";

export type {
  ConnectorType,
  ConnectorStatus,
  Connector,
  CreateConnectorRequest,
  TestConnectorResponse,
  SearchConfig,
  IngestionConfig,
  BindingEntry,
  BindResult,
  CoverageDetail,
} from "./connectors.js";
export {
  parseConnector,
  parseTestConnectorResponse,
  parseBindResult,
  parseCoverageDetail,
} from "./connectors.js";

export type {
  IngestDocumentRequest,
  IngestDocumentResponse,
  BatchIngestRequest,
  BatchIngestResponse,
} from "./ingestion.js";
export { parseIngestDocumentResponse, parseBatchIngestResponse } from "./ingestion.js";

export type {
  DenialReason,
  PolicyTrace,
  RetrievalOutcome,
  ExecuteRetrievalRequest,
  SecuredRetrieval,
} from "./retrievals.js";
export {
  parseSecuredRetrieval,
  parseRetrievalOutcome,
  parseDenialReason,
  parsePolicyTrace,
} from "./retrievals.js";

export type {
  PolicyType,
  PolicyStatus,
  PolicyEffect,
  PolicyCondition,
  PolicyRule,
  Policy,
  CreatePolicyRequest,
} from "./policies.js";
export { parsePolicy, parsePolicyRule } from "./policies.js";

export type { PaginationMeta } from "./common.js";

export type {
  IdentityProviderType,
  IdentityProviderStatus,
  SyncConfig,
  IdentityProvider,
  CreateIdentityProviderRequest,
} from "./identity-providers.js";
export { parseIdentityProvider } from "./identity-providers.js";

export type {
  PrincipalAttributes,
  Principal,
} from "./principals.js";
export { parsePrincipal } from "./principals.js";

export type {
  DataCatalogFilters,
  ResourceChunk,
  GatedResource,
  GatedResourceDetail,
} from "./data-catalog.js";
export {
  parseGatedResource,
  parseGatedResourceDetail,
  parseResourceChunk,
} from "./data-catalog.js";

export type {
  EnvelopeConfig,
  Pipeline,
  PipelineRun,
  CreatePipelineRequest,
} from "./pipelines.js";
export { parsePipeline, parsePipelineRun } from "./pipelines.js";

export type {
  PlanLimits,
  PlanFeatures,
  Plan,
  UsageMetric,
  Usage,
  Invoice,
  Subscription,
  CheckoutRequest,
  CheckoutResponse,
} from "./billing.js";
export {
  parsePlanLimits,
  parsePlanFeatures,
  parseUsageMetric,
  parsePlan,
  parseUsage,
  parseInvoice,
  parseSubscription,
  parseCheckoutResponse,
} from "./billing.js";

export type {
  AuditEventType,
  AuditEvent,
  AuditExportRequest,
} from "./audit.js";
export { parseAuditEvent } from "./audit.js";

export type {
  SimulationRequest,
  SimulationResult,
} from "./simulator.js";
export { parseSimulationResult } from "./simulator.js";

export type { DashboardStats } from "./dashboard.js";
export { parseDashboardStats } from "./dashboard.js";

export type {
  RetroactiveRegisterRequest,
  RetroactiveRegisterResponse,
} from "./retroactive.js";
export { parseRetroactiveRegisterResponse } from "./retroactive.js";
