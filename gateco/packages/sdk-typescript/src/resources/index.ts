/**
 * Re-exports all resource namespaces.
 */

export { AuthResource } from "./auth.js";
export { ConnectorsResource } from "./connectors.js";
export { IngestionResource } from "./ingestion.js";
export type { IngestDocumentOptions } from "./ingestion.js";
export { RetrievalsResource } from "./retrievals.js";
export type { ExecuteRetrievalOptions, ListRetrievalsFilters } from "./retrievals.js";
export { PoliciesResource } from "./policies.js";
export type { CreatePolicyOptions, UpdatePolicyOptions } from "./policies.js";
export { IdentityProvidersResource } from "./identity-providers.js";
export type {
  CreateIdentityProviderOptions,
  UpdateIdentityProviderOptions,
} from "./identity-providers.js";
export { PrincipalsResource } from "./principals.js";
export { DataCatalogResource } from "./data-catalog.js";
export type { UpdateGatedResourceOptions } from "./data-catalog.js";
export { PipelinesResource } from "./pipelines.js";
export type { CreatePipelineOptions, UpdatePipelineOptions } from "./pipelines.js";
export { BillingResource } from "./billing.js";
export { AuditResource } from "./audit.js";
export type { AuditListFilters, AuditExportFilters } from "./audit.js";
export { SimulatorResource } from "./simulator.js";
export type { RunSimulationOptions } from "./simulator.js";
export { DashboardResource } from "./dashboard.js";
export { RetroactiveResource } from "./retroactive.js";
export type { RetroactiveRegisterOptions } from "./retroactive.js";
