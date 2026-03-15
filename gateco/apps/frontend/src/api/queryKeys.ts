export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  connectors: {
    all: ['connectors'] as const,
    list: () => ['connectors', 'list'] as const,
    detail: (id: string) => ['connectors', id] as const,
  },
  identityProviders: {
    all: ['identity-providers'] as const,
    list: () => ['identity-providers', 'list'] as const,
    detail: (id: string) => ['identity-providers', id] as const,
  },
  dataCatalog: {
    all: ['data-catalog'] as const,
    list: (params?: Record<string, unknown>) => ['data-catalog', 'list', params] as const,
    detail: (id: string) => ['data-catalog', id] as const,
  },
  pipelines: {
    all: ['pipelines'] as const,
    list: () => ['pipelines', 'list'] as const,
    detail: (id: string) => ['pipelines', id] as const,
    runs: (id: string) => ['pipelines', id, 'runs'] as const,
  },
  policies: {
    all: ['policies'] as const,
    list: () => ['policies', 'list'] as const,
    detail: (id: string) => ['policies', id] as const,
  },
  retrievals: {
    all: ['retrievals'] as const,
    list: (params?: Record<string, unknown>) => ['retrievals', 'list', params] as const,
    detail: (id: string) => ['retrievals', id] as const,
  },
  audit: {
    all: ['audit'] as const,
    list: (params?: Record<string, unknown>) => ['audit', 'list', params] as const,
  },
  dashboard: {
    stats: ['dashboard', 'stats'] as const,
  },
  billing: {
    plans: ['plans'] as const,
    usage: ['billing', 'usage'] as const,
    invoices: (params?: Record<string, unknown>) => ['billing', 'invoices', params] as const,
    subscription: ['billing', 'subscription'] as const,
  },
};
