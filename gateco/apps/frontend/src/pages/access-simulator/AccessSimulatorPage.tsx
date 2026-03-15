import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, Play, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { apiGet, apiPost } from '@/api/client';
import { EntitlementGate } from '@/components/billing/EntitlementGate';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { RetrievalOutcome } from '@/types/retrieval';

interface Principal {
  id: string;
  display_name: string;
  email: string;
  groups: string[];
  roles: string[];
  attributes: Record<string, unknown>;
}

interface SimulationResult {
  outcome: RetrievalOutcome;
  matched_resources: number;
  allowed: number;
  denied: number;
  policy_trace: { policy_id: string; policy_name: string; effect: string; evaluation_ms?: number; matched_rules?: string[] }[];
  denial_reasons: string[];
}

const outcomeConfig = {
  allowed: { icon: CheckCircle2, label: 'Allowed', className: 'text-emerald-600', bgClassName: 'bg-emerald-50 dark:bg-emerald-900/20' },
  partial: { icon: AlertTriangle, label: 'Partial', className: 'text-amber-600', bgClassName: 'bg-amber-50 dark:bg-amber-900/20' },
  denied: { icon: XCircle, label: 'Denied', className: 'text-red-600', bgClassName: 'bg-red-50 dark:bg-red-900/20' },
};

export function AccessSimulatorPage() {
  const [principalId, setPrincipalId] = useState('');
  const [query, setQuery] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string>();

  const { data: principals, isLoading: principalsLoading } = useQuery({
    queryKey: ['principals-for-simulator'],
    queryFn: async () => {
      const res = await apiGet<{ data: Principal[] }>('/principals', { per_page: 100 });
      return res.data;
    },
  });

  async function handleSimulate(e: React.FormEvent) {
    e.preventDefault();
    if (!principalId || !query.trim()) return;
    setIsRunning(true);
    setResult(null);
    setError(undefined);
    try {
      const res = await apiPost<SimulationResult>('/simulator/run', {
        principal_id: principalId,
        query: query.trim(),
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setIsRunning(false);
    }
  }

  const selectClass = 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Access Simulator</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Simulate retrieval queries to see exactly what a principal can access before deploying policies to production.
        </p>
      </div>

      <EntitlementGate feature="access_simulator">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold mb-4">Run Simulation</h3>
          <form onSubmit={handleSimulate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Principal</label>
                {principalsLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <select value={principalId} onChange={(e) => setPrincipalId(e.target.value)} className={selectClass}>
                    <option value="">Select a principal...</option>
                    {(principals ?? []).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.display_name} ({p.email})
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Query</label>
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. Show me the customer support transcripts"
                />
              </div>
            </div>
            <Button type="submit" disabled={!principalId || !query.trim() || isRunning}>
              <Play className="h-4 w-4 mr-2" />
              {isRunning ? 'Simulating...' : 'Run Simulation'}
            </Button>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </form>
        </div>

        {result && (
          <div className="space-y-4">
            {/* Outcome Summary */}
            <div className={`rounded-lg border p-6 ${(outcomeConfig[result.outcome] ?? outcomeConfig.denied).bgClassName}`}>
              <div className="flex items-center gap-3 mb-4">
                {(() => {
                  const cfg = outcomeConfig[result.outcome] ?? outcomeConfig.denied;
                  const Icon = cfg.icon;
                  return <Icon className={`h-6 w-6 ${cfg.className}`} />;
                })()}
                <div>
                  <h3 className={`font-semibold text-lg ${(outcomeConfig[result.outcome] ?? outcomeConfig.denied).className}`}>
                    {(outcomeConfig[result.outcome] ?? outcomeConfig.denied).label}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    &ldquo;{query}&rdquo;
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">Matched Resources</p>
                  <p className="font-semibold">{result.matched_resources}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Allowed</p>
                  <p className="font-semibold text-emerald-600">{result.allowed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Denied</p>
                  <p className="font-semibold text-red-600">{result.denied}</p>
                </div>
              </div>
            </div>

            {/* Policy Trace */}
            {result.policy_trace.length > 0 && (
              <div className="rounded-lg border bg-card p-6">
                <h3 className="font-semibold mb-3">Policy Trace</h3>
                <div className="space-y-2">
                  {result.policy_trace.map((trace, i) => (
                    <div key={i} className="flex items-center justify-between rounded-md border px-4 py-3 text-sm">
                      <div className="flex items-center gap-3">
                        {trace.effect === 'allow' ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                        )}
                        <p className="font-medium">{trace.policy_name}</p>
                      </div>
                      <Badge variant={trace.effect === 'allow' ? 'default' : 'destructive'}>
                        {trace.effect}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Denial Reasons */}
            {result.denial_reasons.length > 0 && (
              <div className="rounded-lg border bg-card p-6">
                <h3 className="font-semibold mb-3">Denial Reasons</h3>
                <div className="space-y-2">
                  {result.denial_reasons.map((reason, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-md border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/10 px-4 py-3 text-sm">
                      <XCircle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
                      <p className="text-red-600 dark:text-red-300 text-xs">{reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !isRunning && (
          <div className="rounded-lg border border-dashed p-12 text-center">
            <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold">Select a principal and enter a query</h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
              Choose a synced principal and describe what they're trying to access. The simulator will evaluate all active policies against the real data catalog.
            </p>
          </div>
        )}
      </EntitlementGate>
    </div>
  );
}
