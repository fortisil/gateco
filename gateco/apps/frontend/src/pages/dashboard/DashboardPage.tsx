import { Shield, Database, KeyRound, XCircle, CheckCircle, ShieldCheck } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useDashboardStats } from '@/hooks/useDashboard';
import { useUsage } from '@/hooks/useBilling';
import { PlanBadge } from '@/components/billing/PlanBadge';
import { UsageMeter } from '@/components/billing/UsageMeter';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeDate } from '@/lib/formatters';
import type { PlanTier } from '@/types/billing';

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data: stats, isLoading } = useDashboardStats();
  const { data: usage } = useUsage();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /></div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const deniedPct = stats && stats.retrievals_today > 0
    ? ((stats.retrievals_denied / stats.retrievals_today) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.name}</h1>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-muted-foreground">{user?.organization?.name}</span>
          {user?.organization?.plan && <PlanBadge tier={user.organization.plan as PlanTier} />}
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Retrieval Activity */}
        <div className="rounded-lg border bg-card p-6 space-y-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Retrieval Activity</span>
          </div>
          <p className="text-3xl font-bold">{stats?.retrievals_today.toLocaleString() ?? 0}</p>
          <p className="text-xs text-muted-foreground">retrievals today</p>
          <div className="flex gap-4 text-xs">
            <span className="flex items-center gap-1 text-emerald-600"><CheckCircle className="h-3 w-3" />{stats?.retrievals_allowed.toLocaleString()} allowed</span>
            <span className="flex items-center gap-1 text-red-600"><XCircle className="h-3 w-3" />{stats?.retrievals_denied} denied ({deniedPct}%)</span>
          </div>
        </div>

        {/* Connector Status */}
        <div className="rounded-lg border bg-card p-6 space-y-3">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Connector Status</span>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-3xl font-bold">{stats?.connectors_connected ?? 0}</p>
            <StatusBadge status="connected" />
          </div>
          {(stats?.connectors_error ?? 0) > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-600">{stats?.connectors_error} with errors</span>
              <StatusBadge status="error" />
            </div>
          )}
        </div>

        {/* Identity Provider Status */}
        <div className="rounded-lg border bg-card p-6 space-y-3">
          <div className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Identity Providers</span>
          </div>
          <p className="text-3xl font-bold">{stats?.idps_principal_count.toLocaleString() ?? 0}</p>
          <p className="text-xs text-muted-foreground">principals synced</p>
          <p className="text-xs text-muted-foreground">
            {stats?.idps_connected} provider{stats?.idps_connected !== 1 ? 's' : ''} connected
            {stats?.last_idp_sync && <> &middot; Last sync {formatRelativeDate(stats.last_idp_sync)}</>}
          </p>
        </div>

        {/* Policy Coverage */}
        <div className="rounded-lg border bg-card p-6 space-y-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Policy Coverage</span>
          </div>
          <p className="text-3xl font-bold">
            {stats?.overall_coverage_pct != null ? `~${stats.overall_coverage_pct}%` : '—'}
          </p>
          <p className="text-xs text-muted-foreground">
            {stats?.total_bound_vectors.toLocaleString()} of {stats?.total_vectors.toLocaleString()} vectors bound
          </p>
          <p className="text-xs text-muted-foreground">
            {stats?.connectors_policy_ready} connector{stats?.connectors_policy_ready !== 1 ? 's' : ''} production-ready
          </p>
        </div>
      </div>

      {/* Usage Meter */}
      {usage && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-sm font-medium mb-4">Usage This Period</h2>
          <UsageMeter
            used={usage.secured_retrievals.used}
            limit={usage.secured_retrievals.limit}
            label="Secured Retrievals"
          />
        </div>
      )}

      {/* Recent Denied Retrievals */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Recent Denied Retrievals</h2>
        {stats?.recent_denied && stats.recent_denied.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Query</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Principal</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Denial Reason</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Time</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_denied.map((item) => (
                  <tr key={item.id} className="border-b last:border-0">
                    <td className="px-4 py-3 max-w-xs truncate font-medium">{item.query}</td>
                    <td className="px-4 py-3 text-muted-foreground">{item.principal_name}</td>
                    <td className="px-4 py-3 text-xs text-red-600 max-w-sm truncate">{item.denial_reason}</td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatRelativeDate(item.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No denied retrievals recently.</p>
        )}
      </div>
    </div>
  );
}
