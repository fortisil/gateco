import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000/api';

// ── Auth Mock Data ──

const mockUser = {
  id: 'user_123',
  email: 'admin@acmecorp.com',
  name: 'Sarah Chen',
  role: 'org_admin' as const,
  organization: {
    id: 'org_456',
    name: 'Acme Corp',
    slug: 'acme-corp',
    plan: 'pro' as const,
  },
  created_at: '2026-01-15T12:00:00Z',
};

const mockTokens = {
  access_token: 'mock_access_token_123',
  refresh_token: 'mock_refresh_token_456',
  token_type: 'Bearer' as const,
  expires_in: 900,
};

// ── Connectors Mock Data ──

const mockConnectors = [
  {
    id: 'conn_1', name: 'Production pgvector', type: 'pgvector', status: 'connected',
    config: { host: 'db.acmecorp.internal', port: 5432, database: 'vectors_prod' },
    last_sync: '2026-03-12T08:30:00Z', index_count: 12, record_count: 145230,
    error_message: null, created_at: '2026-02-01T10:00:00Z', updated_at: '2026-03-12T08:30:00Z',
  },
  {
    id: 'conn_2', name: 'Staging pgvector', type: 'pgvector', status: 'connected',
    config: { host: 'staging-db.acmecorp.internal', port: 5432, database: 'vectors_staging' },
    last_sync: '2026-03-11T22:00:00Z', index_count: 8, record_count: 52100,
    error_message: null, created_at: '2026-02-15T14:00:00Z', updated_at: '2026-03-11T22:00:00Z',
  },
  {
    id: 'conn_3', name: 'Research Pinecone', type: 'pinecone', status: 'error',
    config: { api_key: '***', region: 'us-east-1', index_name: 'research-embeddings' },
    last_sync: '2026-03-10T16:00:00Z', index_count: 3, record_count: 0,
    error_message: 'Authentication failed: API key expired', created_at: '2026-03-01T09:00:00Z', updated_at: '2026-03-10T16:00:00Z',
  },
];

// ── Identity Providers Mock Data ──

const mockIdentityProviders = [
  {
    id: 'idp_1', name: 'Azure Entra ID - Acme Corp', type: 'azure_entra_id', status: 'connected',
    sync_config: { auto_sync: true, sync_interval_minutes: 60, sync_groups: true, sync_roles: true, sync_attributes: true },
    principal_count: 342, group_count: 28, last_sync: '2026-03-12T09:00:00Z',
    error_message: null, created_at: '2026-01-20T10:00:00Z', updated_at: '2026-03-12T09:00:00Z',
  },
  {
    id: 'idp_2', name: 'AWS IAM - Production', type: 'aws_iam', status: 'syncing',
    sync_config: { auto_sync: true, sync_interval_minutes: 120, sync_groups: true, sync_roles: true, sync_attributes: false },
    principal_count: 89, group_count: 12, last_sync: '2026-03-12T08:00:00Z',
    error_message: null, created_at: '2026-02-10T15:00:00Z', updated_at: '2026-03-12T10:00:00Z',
  },
];

// ── Data Catalog Mock Data ──

const mockCatalogItems = [
  {
    id: 'res_1', title: 'Customer Support Transcripts', description: 'Q1 2026 support call transcripts',
    classification: 'confidential', sensitivity: 'high', domain: 'customer-support',
    labels: ['pii', 'customer-data', 'q1-2026'], chunk_ids: ['ch_1', 'ch_2', 'ch_3', 'ch_4', 'ch_5'],
    acl_refs: ['pol_1', 'pol_2'], encryption_mode: 'envelope', source_connector_id: 'conn_1',
    source_connector_name: 'Production pgvector', policy_ids: ['pol_1', 'pol_2'],
    created_at: '2026-02-20T12:00:00Z', updated_at: '2026-03-10T14:00:00Z',
  },
  {
    id: 'res_2', title: 'Engineering Design Docs', description: 'Architecture and design documentation',
    classification: 'internal', sensitivity: 'medium', domain: 'engineering',
    labels: ['architecture', 'design', 'technical'], chunk_ids: ['ch_6', 'ch_7', 'ch_8'],
    acl_refs: ['pol_3'], encryption_mode: 'at_rest', source_connector_id: 'conn_1',
    source_connector_name: 'Production pgvector', policy_ids: ['pol_3'],
    created_at: '2026-02-15T09:00:00Z', updated_at: '2026-03-08T11:00:00Z',
  },
  {
    id: 'res_3', title: 'Public API Reference', description: 'External-facing API documentation',
    classification: 'public', sensitivity: 'low', domain: 'documentation',
    labels: ['api', 'public', 'reference'], chunk_ids: ['ch_9', 'ch_10'],
    acl_refs: [], encryption_mode: 'none', source_connector_id: 'conn_2',
    source_connector_name: 'Staging pgvector', policy_ids: [],
    created_at: '2026-03-01T10:00:00Z', updated_at: '2026-03-05T16:00:00Z',
  },
  {
    id: 'res_4', title: 'HR Compensation Data', description: 'Employee compensation and benefits info',
    classification: 'restricted', sensitivity: 'critical', domain: 'human-resources',
    labels: ['pii', 'compensation', 'restricted'], chunk_ids: ['ch_11', 'ch_12', 'ch_13', 'ch_14'],
    acl_refs: ['pol_4'], encryption_mode: 'full', source_connector_id: 'conn_1',
    source_connector_name: 'Production pgvector', policy_ids: ['pol_4'],
    created_at: '2026-02-25T08:00:00Z', updated_at: '2026-03-11T10:00:00Z',
  },
  {
    id: 'res_5', title: 'Product Roadmap Notes', description: 'Strategic planning and product direction',
    classification: 'confidential', sensitivity: 'high', domain: 'product',
    labels: ['strategy', 'roadmap', 'confidential'], chunk_ids: ['ch_15', 'ch_16'],
    acl_refs: ['pol_1', 'pol_5'], encryption_mode: 'envelope', source_connector_id: 'conn_1',
    source_connector_name: 'Production pgvector', policy_ids: ['pol_1', 'pol_5'],
    created_at: '2026-03-02T13:00:00Z', updated_at: '2026-03-12T07:00:00Z',
  },
];

// ── Pipelines Mock Data ──

const mockPipelines = [
  {
    id: 'pipe_1', name: 'Support Docs Ingestion', source_connector_id: 'conn_1',
    source_connector_name: 'Production pgvector',
    envelope_config: { encrypt: true, classify: true, default_classification: 'confidential', default_sensitivity: 'high', label_extraction: true },
    status: 'active', schedule: '0 */6 * * *', last_run: '2026-03-12T06:00:00Z',
    records_processed: 14523, error_count: 3, created_at: '2026-02-20T10:00:00Z', updated_at: '2026-03-12T06:00:00Z',
  },
  {
    id: 'pipe_2', name: 'Engineering Knowledge Base', source_connector_id: 'conn_2',
    source_connector_name: 'Staging pgvector',
    envelope_config: { encrypt: false, classify: true, default_classification: 'internal', default_sensitivity: 'medium', label_extraction: true },
    status: 'paused', schedule: '0 0 * * *', last_run: '2026-03-10T00:00:00Z',
    records_processed: 8910, error_count: 0, created_at: '2026-02-25T14:00:00Z', updated_at: '2026-03-10T00:00:00Z',
  },
];

const mockPipelineRuns = [
  { id: 'run_1', pipeline_id: 'pipe_1', status: 'completed', records_processed: 230, errors: 0, started_at: '2026-03-12T06:00:00Z', completed_at: '2026-03-12T06:05:23Z', duration_ms: 323000 },
  { id: 'run_2', pipeline_id: 'pipe_1', status: 'completed', records_processed: 198, errors: 1, started_at: '2026-03-12T00:00:00Z', completed_at: '2026-03-12T00:04:12Z', duration_ms: 252000 },
  { id: 'run_3', pipeline_id: 'pipe_1', status: 'failed', records_processed: 45, errors: 3, started_at: '2026-03-11T18:00:00Z', completed_at: '2026-03-11T18:01:30Z', duration_ms: 90000 },
];

// ── Policies Mock Data ──

const mockPolicies = [
  {
    id: 'pol_1', name: 'CX Team Access', description: 'Allow customer success team to access support transcripts',
    type: 'rbac', status: 'active', effect: 'allow',
    rules: [
      { id: 'rule_1', description: 'Allow CX team members', effect: 'allow', conditions: [{ field: 'principal.group', operator: 'in', value: ['cx-team', 'cx-managers'] }], priority: 1 },
    ],
    resource_selectors: ['domain:customer-support'], version: 2, created_by: 'admin@acmecorp.com',
    created_at: '2026-02-01T10:00:00Z', updated_at: '2026-03-10T14:00:00Z',
  },
  {
    id: 'pol_2', name: 'PII Protection', description: 'Deny access to PII-labeled resources for non-authorized roles',
    type: 'abac', status: 'active', effect: 'deny',
    rules: [
      { id: 'rule_2', description: 'Deny if resource has PII label and principal lacks pii_authorized', effect: 'deny', conditions: [{ field: 'resource.labels', operator: 'contains', value: 'pii' }, { field: 'principal.attributes.pii_authorized', operator: 'neq', value: 'true' }], priority: 1 },
    ],
    resource_selectors: ['label:pii'], version: 1, created_by: 'admin@acmecorp.com',
    created_at: '2026-02-10T09:00:00Z', updated_at: '2026-02-10T09:00:00Z',
  },
  {
    id: 'pol_3', name: 'Engineering Docs', description: 'Allow engineering team access to internal documentation',
    type: 'rbac', status: 'active', effect: 'allow',
    rules: [
      { id: 'rule_3', description: 'Allow engineering group', effect: 'allow', conditions: [{ field: 'principal.group', operator: 'eq', value: 'engineering' }], priority: 1 },
    ],
    resource_selectors: ['domain:engineering'], version: 1, created_by: 'admin@acmecorp.com',
    created_at: '2026-02-15T11:00:00Z', updated_at: '2026-03-08T11:00:00Z',
  },
  {
    id: 'pol_4', name: 'HR-Restricted', description: 'Restrict HR compensation data to HR managers only',
    type: 'rbac', status: 'active', effect: 'allow',
    rules: [
      { id: 'rule_4', description: 'Only HR managers', effect: 'allow', conditions: [{ field: 'principal.role', operator: 'eq', value: 'hr_manager' }], priority: 1 },
    ],
    resource_selectors: ['domain:human-resources', 'classification:restricted'], version: 3, created_by: 'admin@acmecorp.com',
    created_at: '2026-01-20T08:00:00Z', updated_at: '2026-03-11T10:00:00Z',
  },
  {
    id: 'pol_5', name: 'Internal-Only', description: 'Deny external contractors access to internal and above resources',
    type: 'abac', status: 'active', effect: 'deny',
    rules: [
      { id: 'rule_5', description: 'Deny external contractors', effect: 'deny', conditions: [{ field: 'principal.group', operator: 'in', value: ['external-contractors', 'vendors'] }], priority: 1 },
    ],
    resource_selectors: ['classification:internal', 'classification:confidential', 'classification:restricted'], version: 1, created_by: 'admin@acmecorp.com',
    created_at: '2026-03-01T13:00:00Z', updated_at: '2026-03-01T13:00:00Z',
  },
  {
    id: 'pol_6', name: 'Roadmap Access Draft', description: 'Draft policy for product roadmap access control',
    type: 'rbac', status: 'draft', effect: 'allow',
    rules: [
      { id: 'rule_6', description: 'Allow product and leadership teams', effect: 'allow', conditions: [{ field: 'principal.group', operator: 'in', value: ['product', 'leadership'] }], priority: 1 },
    ],
    resource_selectors: ['domain:product'], version: 1, created_by: 'admin@acmecorp.com',
    created_at: '2026-03-12T15:00:00Z', updated_at: '2026-03-12T15:00:00Z',
  },
];

// ── Dashboard Mock Data ──

const mockDashboardStats = {
  retrievals_today: 1247,
  retrievals_allowed: 1183,
  retrievals_denied: 64,
  connectors_connected: 2,
  connectors_error: 1,
  idps_connected: 1,
  idps_principal_count: 431,
  last_idp_sync: '2026-03-12T09:00:00Z',
  recent_denied: [
    { id: 'ret_d1', query: 'What are the Q1 compensation adjustments?', principal_name: 'intern@acmecorp.com', denial_reason: "Policy 'HR-Restricted' denied: principal lacks role 'hr_manager'", timestamp: '2026-03-12T10:23:00Z' },
    { id: 'ret_d2', query: 'Show me the product roadmap for Q3', principal_name: 'contractor@vendor.com', denial_reason: "Policy 'Internal-Only' denied: principal group 'external-contractors' excluded", timestamp: '2026-03-12T10:15:00Z' },
    { id: 'ret_d3', query: 'Customer churn analysis report', principal_name: 'dev@acmecorp.com', denial_reason: "Policy 'CX-Team-Only' denied: principal department is 'engineering', required 'customer-success'", timestamp: '2026-03-12T09:58:00Z' },
  ],
};

// ── Billing Mock Data ──

const mockPlans = [
  {
    id: 'free', name: 'Free', tier: 'free',
    price_monthly_cents: 0, price_yearly_cents: 0,
    features: {
      rbac_policies: true, abac_policies: false, policy_studio: false, policy_versioning: false,
      access_simulator: false, vendor_iam: false, multi_connector: false, advanced_analytics: false,
      audit_export: false, siem_export: false, content_ref_mode: false, custom_kms: false,
      sso_scim: false, private_data_plane: false,
    },
    limits: { secured_retrievals: 100, connectors: 1, identity_providers: 1, policies: 3, team_members: 1, overage_price_cents: 0 },
  },
  {
    id: 'pro', name: 'Pro', tier: 'pro',
    price_monthly_cents: 4900, price_yearly_cents: 49000,
    features: {
      rbac_policies: true, abac_policies: true, policy_studio: true, policy_versioning: true,
      access_simulator: true, vendor_iam: true, multi_connector: true, advanced_analytics: true,
      audit_export: true, siem_export: false, content_ref_mode: false, custom_kms: false,
      sso_scim: false, private_data_plane: false,
    },
    limits: { secured_retrievals: 10000, connectors: 5, identity_providers: 3, policies: null, team_members: 10, overage_price_cents: 50 },
  },
  {
    id: 'enterprise', name: 'Enterprise', tier: 'enterprise',
    price_monthly_cents: 19900, price_yearly_cents: 199000,
    features: {
      rbac_policies: true, abac_policies: true, policy_studio: true, policy_versioning: true,
      access_simulator: true, vendor_iam: true, multi_connector: true, advanced_analytics: true,
      audit_export: true, siem_export: true, content_ref_mode: true, custom_kms: true,
      sso_scim: true, private_data_plane: true,
    },
    limits: { secured_retrievals: null, connectors: null, identity_providers: null, policies: null, team_members: null, overage_price_cents: 0 },
  },
];

const mockUsage = {
  period_start: '2026-03-01T00:00:00Z',
  period_end: '2026-03-31T23:59:59Z',
  secured_retrievals: { used: 4523, limit: 10000, overage: 0 },
  connectors: { used: 3, limit: 5 },
  policies: { used: 5, limit: null },
  estimated_overage_cents: 0,
};

// ── Handlers ──

export const handlers = [
  // Auth
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    if (body.email === 'admin@acmecorp.com' && body.password === 'password123') {
      return HttpResponse.json({ user: mockUser, tokens: mockTokens });
    }
    return HttpResponse.json(
      { error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'Invalid email or password', request_id: 'req_1' } },
      { status: 401 }
    );
  }),

  http.post(`${API_BASE}/auth/signup`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    if (!body.email || !body.password || !body.name || !body.organization_name) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Missing required fields', request_id: 'req_1' } },
        { status: 422 }
      );
    }
    return HttpResponse.json({
      user: { ...mockUser, email: body.email, name: body.name, organization: { ...mockUser.organization, name: body.organization_name } },
      tokens: mockTokens,
    }, { status: 201 });
  }),

  http.post(`${API_BASE}/auth/refresh`, () => {
    return HttpResponse.json({ access_token: 'new_access_token', refresh_token: 'new_refresh_token', token_type: 'Bearer', expires_in: 900 });
  }),

  http.post(`${API_BASE}/auth/logout`, () => new HttpResponse(null, { status: 204 })),

  http.get(`${API_BASE}/users/me`, () => HttpResponse.json(mockUser)),

  http.patch(`${API_BASE}/users/me`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockUser, name: (body.name as string) || mockUser.name });
  }),

  // Dashboard
  http.get(`${API_BASE}/dashboard/stats`, () => HttpResponse.json(mockDashboardStats)),

  // Connectors
  http.get(`${API_BASE}/connectors`, () => HttpResponse.json(mockConnectors)),

  http.post(`${API_BASE}/connectors`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      id: `conn_${Date.now()}`, ...body, status: 'connected',
      last_sync: null, index_count: 0, record_count: 0, error_message: null,
      created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.post(`${API_BASE}/connectors/:id/test`, () => {
    return HttpResponse.json({ success: true, message: 'Connection successful', latency_ms: 23 });
  }),

  http.patch(`${API_BASE}/connectors/:id`, async ({ params, request }) => {
    const connector = mockConnectors.find((c) => c.id === params.id);
    if (!connector) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...connector, ...body, updated_at: new Date().toISOString() });
  }),

  http.delete(`${API_BASE}/connectors/:id`, () => new HttpResponse(null, { status: 204 })),

  // Identity Providers
  http.get(`${API_BASE}/identity-providers`, () => HttpResponse.json(mockIdentityProviders)),

  http.post(`${API_BASE}/identity-providers`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      id: `idp_${Date.now()}`, ...body, status: 'connected',
      principal_count: 0, group_count: 0, last_sync: null, error_message: null,
      created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.post(`${API_BASE}/identity-providers/:id/sync`, () => {
    return HttpResponse.json({ message: 'Sync initiated' });
  }),

  http.patch(`${API_BASE}/identity-providers/:id`, async ({ params, request }) => {
    const idp = mockIdentityProviders.find((p) => p.id === params.id);
    if (!idp) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...idp, ...body, updated_at: new Date().toISOString() });
  }),

  http.delete(`${API_BASE}/identity-providers/:id`, () => new HttpResponse(null, { status: 204 })),

  // Data Catalog
  http.get(`${API_BASE}/data-catalog`, ({ request }) => {
    const url = new URL(request.url);
    let items = [...mockCatalogItems];
    const classification = url.searchParams.get('classification');
    const sensitivity = url.searchParams.get('sensitivity');
    const domain = url.searchParams.get('domain');
    if (classification) items = items.filter((i) => i.classification === classification);
    if (sensitivity) items = items.filter((i) => i.sensitivity === sensitivity);
    if (domain) items = items.filter((i) => i.domain === domain);
    return HttpResponse.json({
      data: items,
      meta: { pagination: { page: 1, per_page: 20, total: items.length, total_pages: 1 } },
    });
  }),

  http.get(`${API_BASE}/data-catalog/:id`, ({ params }) => {
    const item = mockCatalogItems.find((i) => i.id === params.id);
    if (!item) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    return HttpResponse.json({
      ...item,
      chunks: [
        { id: 'ch_1', index: 0, preview: 'Customer reported issue with billing system...', encrypted: true, vector_id: 'vec_001' },
        { id: 'ch_2', index: 1, preview: 'Resolution: Applied credit and updated account...', encrypted: true, vector_id: 'vec_002' },
        { id: 'ch_3', index: 2, preview: 'Follow-up call scheduled for next week...', encrypted: true, vector_id: 'vec_003' },
      ],
      applicable_policies: [
        { id: 'pol_1', name: 'CX Team Access', type: 'rbac', effect: 'allow' },
        { id: 'pol_2', name: 'PII Protection', type: 'abac', effect: 'deny' },
      ],
      recent_access: [
        { id: 'acc_1', principal_name: 'cx-agent@acmecorp.com', outcome: 'allowed', timestamp: '2026-03-12T09:30:00Z' },
        { id: 'acc_2', principal_name: 'dev@acmecorp.com', outcome: 'denied', timestamp: '2026-03-12T08:45:00Z' },
      ],
    });
  }),

  http.patch(`${API_BASE}/data-catalog/:id`, async ({ params, request }) => {
    const item = mockCatalogItems.find((i) => i.id === params.id);
    if (!item) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...item, ...body, updated_at: new Date().toISOString() });
  }),

  // Policies
  http.get(`${API_BASE}/policies`, () => HttpResponse.json(mockPolicies)),

  http.post(`${API_BASE}/policies`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      id: `pol_${Date.now()}`, ...body, status: 'draft', version: 1,
      created_by: 'admin@acmecorp.com',
      created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.patch(`${API_BASE}/policies/:id`, async ({ params, request }) => {
    const policy = mockPolicies.find((p) => p.id === params.id);
    if (!policy) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...policy, ...body, updated_at: new Date().toISOString() });
  }),

  http.delete(`${API_BASE}/policies/:id`, () => new HttpResponse(null, { status: 204 })),

  http.post(`${API_BASE}/policies/:id/activate`, ({ params }) => {
    const policy = mockPolicies.find((p) => p.id === params.id);
    if (!policy) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    return HttpResponse.json({ ...policy, status: 'active', updated_at: new Date().toISOString() });
  }),

  http.post(`${API_BASE}/policies/:id/archive`, ({ params }) => {
    const policy = mockPolicies.find((p) => p.id === params.id);
    if (!policy) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    return HttpResponse.json({ ...policy, status: 'archived', updated_at: new Date().toISOString() });
  }),

  // Pipelines
  http.get(`${API_BASE}/pipelines`, () => HttpResponse.json(mockPipelines)),

  http.post(`${API_BASE}/pipelines`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      id: `pipe_${Date.now()}`, ...body, status: 'active',
      last_run: null, records_processed: 0, error_count: 0,
      created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  http.patch(`${API_BASE}/pipelines/:id`, async ({ params, request }) => {
    const pipeline = mockPipelines.find((p) => p.id === params.id);
    if (!pipeline) return HttpResponse.json({ error: { code: 'NOT_FOUND', message: 'Not found' } }, { status: 404 });
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...pipeline, ...body, updated_at: new Date().toISOString() });
  }),

  http.post(`${API_BASE}/pipelines/:id/run`, () => {
    return HttpResponse.json({
      id: `run_${Date.now()}`, pipeline_id: 'pipe_1', status: 'running',
      records_processed: 0, errors: 0,
      started_at: new Date().toISOString(), completed_at: null, duration_ms: null,
    });
  }),

  http.get(`${API_BASE}/pipelines/:id/runs`, () => HttpResponse.json(mockPipelineRuns)),

  // Billing
  http.get(`${API_BASE}/plans`, () => HttpResponse.json({ plans: mockPlans })),
  http.get(`${API_BASE}/billing/usage`, () => HttpResponse.json(mockUsage)),

  http.get(`${API_BASE}/billing/invoices`, () => HttpResponse.json({
    data: [
      { id: 'inv_1', stripe_invoice_id: 'in_test_123', amount_cents: 4900, currency: 'USD', status: 'paid',
        period_start: '2026-02-01T00:00:00Z', period_end: '2026-02-28T23:59:59Z',
        pdf_url: 'https://invoice.stripe.com/test/pdf', created_at: '2026-03-01T00:00:00Z' },
    ],
    meta: { pagination: { page: 1, per_page: 20, total: 1, total_pages: 1 } },
  })),

  http.post(`${API_BASE}/checkout/start`, () => {
    return HttpResponse.json({ checkout_url: 'https://checkout.stripe.com/pay/cs_test_123', session_id: 'cs_test_123' });
  }),

  http.post(`${API_BASE}/billing/portal`, () => {
    return HttpResponse.json({ portal_url: 'https://billing.stripe.com/session/bps_test_123' });
  }),

  http.get(`${API_BASE}/billing/subscription`, () => {
    return HttpResponse.json({
      id: 'sub_test_123', plan_id: 'pro', status: 'active',
      current_period_start: '2026-03-01T00:00:00Z', current_period_end: '2026-03-31T23:59:59Z',
      cancel_at_period_end: false,
    });
  }),
];
