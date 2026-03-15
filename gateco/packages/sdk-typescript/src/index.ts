/**
 * @gateco/sdk -- TypeScript SDK for the Gateco API.
 *
 * @example
 * ```ts
 * import { GatecoClient } from "@gateco/sdk";
 *
 * const client = new GatecoClient({ baseUrl: "https://api.gateco.dev" });
 * await client.login("user@example.com", "secret");
 *
 * const page = await client.connectors.list();
 * console.log(page.items);
 *
 * client.close();
 * ```
 */

// Client
export { GatecoClient } from "./client.js";
export type { GatecoClientOptions, InternalRequestOptions } from "./client.js";

// Errors
export {
  GatecoError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  EntitlementError,
  RateLimitError,
  ValidationError,
  errorFromResponse,
} from "./errors.js";

// Auth
export { TokenManager } from "./auth.js";

// Transport
export { Transport } from "./transport.js";
export type { TransportOptions, RequestOptions } from "./transport.js";

// Pagination
export type { Page } from "./pagination.js";
export { parsePage, listAll, collectAll } from "./pagination.js";
export type { FetchFn } from "./pagination.js";

// Resources
export {
  AuthResource,
  ConnectorsResource,
  IngestionResource,
  RetrievalsResource,
  PoliciesResource,
  IdentityProvidersResource,
  PrincipalsResource,
  DataCatalogResource,
  PipelinesResource,
  BillingResource,
  AuditResource,
  SimulatorResource,
  DashboardResource,
  RetroactiveResource,
} from "./resources/index.js";
export type {
  IngestDocumentOptions,
  ExecuteRetrievalOptions,
  ListRetrievalsFilters,
  CreatePolicyOptions,
  UpdatePolicyOptions,
  CreateIdentityProviderOptions,
  UpdateIdentityProviderOptions,
  UpdateGatedResourceOptions,
  CreatePipelineOptions,
  UpdatePipelineOptions,
  AuditListFilters,
  AuditExportFilters,
  RunSimulationOptions,
  RetroactiveRegisterOptions,
} from "./resources/index.js";

// Types
export type {
  Organization,
  User,
  LoginRequest,
  SignupRequest,
  TokenResponse,
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
  IngestDocumentRequest,
  IngestDocumentResponse,
  BatchIngestRequest,
  BatchIngestResponse,
  DenialReason,
  PolicyTrace,
  RetrievalOutcome,
  ExecuteRetrievalRequest,
  SecuredRetrieval,
  PolicyType,
  PolicyStatus,
  PolicyEffect,
  PolicyCondition,
  PolicyRule,
  Policy,
  CreatePolicyRequest,
  PaginationMeta,
  IdentityProviderType,
  IdentityProviderStatus,
  SyncConfig,
  IdentityProvider,
  CreateIdentityProviderRequest,
  PrincipalAttributes,
  Principal,
  DataCatalogFilters,
  ResourceChunk,
  GatedResource,
  GatedResourceDetail,
  EnvelopeConfig,
  Pipeline,
  PipelineRun,
  CreatePipelineRequest,
  PlanLimits,
  PlanFeatures,
  Plan,
  UsageMetric,
  Usage,
  Invoice,
  Subscription,
  CheckoutRequest,
  CheckoutResponse,
  AuditEventType,
  AuditEvent,
  AuditExportRequest,
  SimulationRequest,
  SimulationResult,
  DashboardStats,
  RetroactiveRegisterRequest,
  RetroactiveRegisterResponse,
} from "./types/index.js";
