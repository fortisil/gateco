import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CheckCircle2,
  XCircle,
  Shield,
  Database,
  KeyRound,
  ArrowRightLeft,
  AlertTriangle,
  LogIn,
  Settings,
  Filter,
} from 'lucide-react';
import { apiGet } from '@/api/client';
import { EntitlementGate } from '@/components/billing/EntitlementGate';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { downloadJsonFile } from '@/lib/export';
import { formatRelativeDate } from '@/lib/formatters';
import type { AuditEventType } from '@/types/audit';

interface AuditEntry {
  id: string;
  event_type: AuditEventType;
  actor_id: string | null;
  actor_name: string;
  principal_id: string | null;
  details: string;
  ip_address: string | null;
  resource_ids: string[];
  timestamp: string;
}

interface AuditResponse {
  data: AuditEntry[];
  meta: { pagination: { page: number; per_page: number; total: number; total_pages: number } };
}

const EVENT_CONFIG: Record<string, { icon: typeof CheckCircle2; label: string; color: string }> = {
  retrieval_allowed: { icon: CheckCircle2, label: 'Retrieval Allowed', color: 'text-emerald-500' },
  retrieval_denied: { icon: XCircle, label: 'Retrieval Denied', color: 'text-red-500' },
  policy_created: { icon: Shield, label: 'Policy Created', color: 'text-blue-500' },
  policy_updated: { icon: Shield, label: 'Policy Updated', color: 'text-blue-500' },
  policy_activated: { icon: Shield, label: 'Policy Activated', color: 'text-emerald-500' },
  policy_archived: { icon: Shield, label: 'Policy Archived', color: 'text-gray-500' },
  connector_added: { icon: Database, label: 'Connector Added', color: 'text-blue-500' },
  connector_removed: { icon: Database, label: 'Connector Removed', color: 'text-red-500' },
  connector_synced: { icon: Database, label: 'Connector Synced', color: 'text-emerald-500' },
  idp_added: { icon: KeyRound, label: 'IdP Added', color: 'text-blue-500' },
  idp_synced: { icon: KeyRound, label: 'IdP Synced', color: 'text-emerald-500' },
  pipeline_run: { icon: ArrowRightLeft, label: 'Pipeline Run', color: 'text-emerald-500' },
  pipeline_error: { icon: AlertTriangle, label: 'Pipeline Error', color: 'text-red-500' },
  pipeline_created: { icon: ArrowRightLeft, label: 'Pipeline Created', color: 'text-blue-500' },
  pipeline_updated: { icon: ArrowRightLeft, label: 'Pipeline Updated', color: 'text-blue-500' },
  user_login: { icon: LogIn, label: 'User Login', color: 'text-blue-500' },
  user_logout: { icon: LogIn, label: 'User Logout', color: 'text-gray-500' },
  settings_changed: { icon: Settings, label: 'Settings Changed', color: 'text-gray-500' },
  resource_updated: { icon: Database, label: 'Resource Updated', color: 'text-blue-500' },
};

type FilterCategory = 'all' | 'retrieval' | 'policy' | 'connector' | 'identity' | 'pipeline' | 'user';

const FILTER_CATEGORIES: { value: FilterCategory; label: string }[] = [
  { value: 'all', label: 'All Events' },
  { value: 'retrieval', label: 'Retrievals' },
  { value: 'policy', label: 'Policies' },
  { value: 'connector', label: 'Connectors' },
  { value: 'identity', label: 'Identity' },
  { value: 'pipeline', label: 'Pipelines' },
  { value: 'user', label: 'User Actions' },
];

const CATEGORY_PREFIXES: Record<FilterCategory, string[]> = {
  all: [],
  retrieval: ['retrieval_'],
  policy: ['policy_'],
  connector: ['connector_'],
  identity: ['idp_'],
  pipeline: ['pipeline_'],
  user: ['user_', 'settings_'],
};

function buildEventTypesParam(filter: FilterCategory): string | undefined {
  if (filter === 'all') return undefined;
  const prefixes = CATEGORY_PREFIXES[filter];
  const allTypes = Object.keys(EVENT_CONFIG);
  const matching = allTypes.filter((t) => prefixes.some((p) => t.startsWith(p)));
  return matching.length > 0 ? matching.join(',') : undefined;
}

export function AuditLogPage() {
  const [isExporting, setIsExporting] = useState(false);
  const [filter, setFilter] = useState<FilterCategory>('all');

  const eventTypes = buildEventTypesParam(filter);

  const { data: auditData, isLoading } = useQuery({
    queryKey: ['audit-log', filter],
    queryFn: () =>
      apiGet<AuditResponse>('/audit-log', {
        per_page: 50,
        ...(eventTypes ? { event_types: eventTypes } : {}),
      }),
  });

  const events = auditData?.data ?? [];

  function handleExport() {
    setIsExporting(true);
    downloadJsonFile(events, 'gateco-audit-log');
    setTimeout(() => setIsExporting(false), 500);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audit Logs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Complete audit trail of all retrieval decisions, policy changes, connector events, and user actions.
          </p>
        </div>
        <EntitlementGate feature="audit_export" mode="hide">
          <Button variant="outline" onClick={handleExport} disabled={isExporting}>
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </EntitlementGate>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {FILTER_CATEGORIES.map((cat) => (
          <Button
            key={cat.value}
            variant={filter === cat.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(cat.value)}
          >
            {cat.label}
          </Button>
        ))}
      </div>

      {/* Event Timeline */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-16" />)}
        </div>
      ) : events.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No audit events found.</p>
      ) : (
        <div className="space-y-1">
          {events.map((evt) => {
            const config = EVENT_CONFIG[evt.event_type] ?? EVENT_CONFIG.settings_changed;
            const Icon = config.icon;
            return (
              <div
                key={evt.id}
                className="flex items-start gap-4 rounded-lg border bg-card px-4 py-3 hover:bg-accent/50 transition-colors"
              >
                <div className={`mt-0.5 shrink-0 ${config.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs font-mono shrink-0">
                      {config.label}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{evt.details}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs font-medium">{evt.actor_name}</p>
                  <p className="text-xs text-muted-foreground">{formatRelativeDate(evt.timestamp)}</p>
                  {evt.ip_address && (
                    <p className="text-xs text-muted-foreground font-mono">{evt.ip_address}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-xs text-muted-foreground text-center">
        Showing {events.length} of {auditData?.meta?.pagination?.total ?? 0} events
      </p>
    </div>
  );
}
