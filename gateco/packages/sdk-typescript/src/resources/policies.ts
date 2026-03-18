/**
 * Policies resource -- CRUD, activate, archive.
 */

import type { GatecoClient } from "../client.js";
import type { Page } from "../pagination.js";
import { parsePage, listAll } from "../pagination.js";
import type { Policy } from "../types/policies.js";
import { parsePolicy } from "../types/policies.js";

/** Options for creating a policy. */
export interface CreatePolicyOptions {
  name: string;
  description?: string;
  type: string;
  effect: string;
  resourceSelectors?: Record<string, unknown>[];
  rules?: Record<string, unknown>[];
}

/** Options for updating a policy. */
export interface UpdatePolicyOptions {
  name?: string;
  description?: string;
  effect?: string;
  resourceSelectors?: Record<string, unknown>[];
  rules?: Record<string, unknown>[];
}

/** Namespace for policy endpoints. Accessed as `client.policies`. */
export class PoliciesResource {
  constructor(private readonly client: GatecoClient) {}

  // ------------------------------------------------------------------
  // List
  // ------------------------------------------------------------------

  /** Fetch a single page of policies. */
  async list(page = 1, perPage = 20): Promise<Page<Policy>> {
    const raw = await this.client._request("GET", "/api/policies", {
      params: { page, per_page: perPage },
    });
    return parsePage(raw, page, perPage, parsePolicy);
  }

  /** Return an async generator that lazily paginates through all policies. */
  listAll(perPage = 100): AsyncGenerator<Policy, void, undefined> {
    return listAll(
      async (page, pp) =>
        (await this.client._request("GET", "/api/policies", {
          params: { page, per_page: pp },
        })) ?? {},
      parsePolicy,
      perPage,
    );
  }

  // ------------------------------------------------------------------
  // CRUD
  // ------------------------------------------------------------------

  /** Get a single policy by ID. */
  async get(policyId: string): Promise<Policy> {
    const data = await this.client._request("GET", `/api/policies/${policyId}`);
    return parsePolicy(data as Record<string, unknown>);
  }

  /**
   * Create a new policy.
   *
   * Each rule's `conditions` array contains objects with `field`, `operator`, and `value`.
   * Fields must be prefixed: `resource.classification`, `principal.roles`, etc.
   * Bare field names silently resolve against the principal.
   *
   * Operators: `eq`, `ne`, `in`, `contains`, `lte`, `gte`.
   *
   * Deny policy note: when a deny policy's selectors match but no rules match,
   * the policy-level `effect=deny` fires. Add a catch-all allow rule to deny
   * only specific conditions.
   */
  async create(options: CreatePolicyOptions): Promise<Policy> {
    const body: Record<string, unknown> = {
      name: options.name,
      type: options.type,
      effect: options.effect,
    };
    if (options.description !== undefined) body["description"] = options.description;
    if (options.resourceSelectors !== undefined) body["resource_selectors"] = options.resourceSelectors;
    if (options.rules !== undefined) body["rules"] = options.rules;

    const data = await this.client._request("POST", "/api/policies", { json: body });
    return parsePolicy(data as Record<string, unknown>);
  }

  /** Update an existing policy. */
  async update(policyId: string, options: UpdatePolicyOptions = {}): Promise<Policy> {
    const body: Record<string, unknown> = {};
    if (options.name !== undefined) body["name"] = options.name;
    if (options.description !== undefined) body["description"] = options.description;
    if (options.effect !== undefined) body["effect"] = options.effect;
    if (options.resourceSelectors !== undefined) body["resource_selectors"] = options.resourceSelectors;
    if (options.rules !== undefined) body["rules"] = options.rules;

    const data = await this.client._request("PATCH", `/api/policies/${policyId}`, {
      json: body,
    });
    return parsePolicy(data as Record<string, unknown>);
  }

  /** Delete a policy. */
  async delete(policyId: string): Promise<void> {
    await this.client._request("DELETE", `/api/policies/${policyId}`);
  }

  // ------------------------------------------------------------------
  // Lifecycle
  // ------------------------------------------------------------------

  /** Activate a policy. */
  async activate(policyId: string): Promise<Policy> {
    const data = await this.client._request(
      "POST",
      `/api/policies/${policyId}/activate`,
    );
    return parsePolicy(data as Record<string, unknown>);
  }

  /** Archive a policy. */
  async archive(policyId: string): Promise<Policy> {
    const data = await this.client._request(
      "POST",
      `/api/policies/${policyId}/archive`,
    );
    return parsePolicy(data as Record<string, unknown>);
  }
}
