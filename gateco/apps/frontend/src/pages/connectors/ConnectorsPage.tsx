import { useState } from 'react';
import { Database, Plus, Pencil, TestTube, Trash2, AlertTriangle, CheckCircle2, XCircle, Loader2, Settings2, Upload, Shield, ArrowDownToLine, Sparkles } from 'lucide-react';
import { useConnectors, useTestConnector, useDeleteConnector } from '@/hooks/useConnectors';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeDate, formatNumber } from '@/lib/formatters';
import { ConnectorDialog } from './ConnectorDialog';
import { SearchConfigDialog } from './SearchConfigDialog';
import { IngestionConfigDialog } from './IngestionConfigDialog';
import { BindingDialog } from './BindingDialog';
import { SuggestionReviewDialog } from '@/pages/SuggestionReviewDialog';
import type { ConnectorType, VectorDBConnector, TestConnectorResponse } from '@/types/connector';

const connectorLabels: Record<ConnectorType, string> = {
  pgvector: 'pgvector',
  pinecone: 'Pinecone',
  opensearch: 'OpenSearch',
  supabase: 'Supabase',
  neon: 'Neon',
  weaviate: 'Weaviate',
  qdrant: 'Qdrant',
  milvus: 'Milvus',
  chroma: 'Chroma',
};

const MAX_DISPLAYED_RESOURCES = 10;

function HealthBadge({ status }: { status: string }) {
  if (status === 'ok') {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/20 rounded-full px-2 py-0.5">
        <CheckCircle2 className="h-3 w-3" />Healthy
      </span>
    );
  }
  if (status === 'degraded') {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20 rounded-full px-2 py-0.5">
        <AlertTriangle className="h-3 w-3" />Degraded
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/20 rounded-full px-2 py-0.5">
      <XCircle className="h-3 w-3" />Failed
    </span>
  );
}

const READINESS_CONFIG: Record<0 | 1 | 2 | 3 | 4, { label: string; color: string; tooltip: string; next: string }> = {
  0: {
    label: 'Not Ready',
    color: 'text-gray-700 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20',
    tooltip: 'Connector not reachable.',
    next: 'Test connection to reach L1.',
  },
  1: {
    label: 'Connection Ready',
    color: 'text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20',
    tooltip: 'Database reachable, auth valid.',
    next: 'Configure search to reach L2.',
  },
  2: {
    label: 'Search Ready',
    color: 'text-orange-700 bg-orange-50 dark:text-orange-400 dark:bg-orange-900/20',
    tooltip: 'Can search, coarse controls only.',
    next: 'Add active policies + resource-level bindings to reach L3.',
  },
  3: {
    label: 'Resource Policy',
    color: 'text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20',
    tooltip: 'Resource-level enforcement active.',
    next: 'Use inline or SQL view metadata for chunk-level enforcement (L4).',
  },
  4: {
    label: 'Chunk Policy',
    color: 'text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/20',
    tooltip: 'Full chunk-level enforcement.',
    next: '',
  },
};

function PolicyReadinessBadge({ level, coveragePct }: { level: 0 | 1 | 2 | 3 | 4; coveragePct: number | null }) {
  const config = READINESS_CONFIG[level];
  return (
    <div className="group relative inline-flex">
      <span className={`inline-flex items-center gap-1 text-xs font-medium rounded-full px-2 py-0.5 ${config.color}`}>
        <Shield className="h-3 w-3" />{config.label}
        {coveragePct != null && level >= 2 && <span className="ml-0.5 opacity-75">({coveragePct}% bound)</span>}
      </span>
      <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block bg-popover text-popover-foreground text-xs rounded px-2 py-1 shadow whitespace-nowrap border z-10 max-w-xs">
        <p className="font-medium">L{level}: {config.label}</p>
        <p>{config.tooltip}</p>
        {config.next && <p className="text-muted-foreground mt-0.5">{config.next}</p>}
      </div>
    </div>
  );
}

function CoverageBar({ coveragePct }: { coveragePct: number | null }) {
  const pct = coveragePct ?? 0;
  return (
    <div className="group relative">
      <div className="w-full bg-muted rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all ${
            pct === 0 ? 'bg-gray-300 dark:bg-gray-600' : pct < 80 ? 'bg-yellow-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block bg-popover text-popover-foreground text-xs rounded px-2 py-1 shadow whitespace-nowrap border">
        Estimated metadata binding coverage
      </div>
    </div>
  );
}

function TestResultPanel({ result }: { result: TestConnectorResponse }) {
  const [showAll, setShowAll] = useState(false);
  const resources = result.resources ?? [];
  const displayedResources = showAll ? resources : resources.slice(0, MAX_DISPLAYED_RESOURCES);
  const hiddenCount = resources.length - MAX_DISPLAYED_RESOURCES;

  return (
    <div className="space-y-2 text-xs">
      <div className="flex items-center justify-between">
        <HealthBadge status={result.health_status} />
        <span className="text-muted-foreground">{result.latency_ms}ms</span>
      </div>

      {result.server_version && (
        <p className="text-muted-foreground">Server: {result.server_version}</p>
      )}

      {result.error && (
        <p className="text-red-600 bg-red-50 dark:bg-red-900/10 rounded p-2">{result.error}</p>
      )}

      {resources.length > 0 && (
        <div className="space-y-1">
          <p className="font-medium text-muted-foreground">
            {resources.length} {result.resource_kind}{resources.length !== 1 ? 's' : ''} discovered
            {result.approximate_counts && <span className="ml-1 italic">(approx. counts)</span>}
          </p>
          <div className="space-y-0.5">
            {displayedResources.map((r) => (
              <div key={r.name} className="flex items-center justify-between rounded bg-muted/50 px-2 py-1">
                <span className="font-mono truncate max-w-[60%]">{r.name}</span>
                <span className="text-muted-foreground whitespace-nowrap ml-2">
                  {r.record_count != null ? formatNumber(r.record_count) + ' records' : '—'}
                  {r.dimension != null && <span className="ml-1">({r.dimension}d{r.metric ? `, ${r.metric}` : ''})</span>}
                </span>
              </div>
            ))}
          </div>
          {!showAll && hiddenCount > 0 && (
            <button
              onClick={() => setShowAll(true)}
              className="text-primary hover:underline text-xs"
            >
              +{hiddenCount} more
            </button>
          )}
        </div>
      )}

      {result.warnings.length > 0 && (
        <div className="rounded bg-amber-50 dark:bg-amber-900/10 p-2 text-amber-700 dark:text-amber-400 space-y-0.5">
          {result.warnings.map((w, i) => (
            <p key={i} className="flex items-start gap-1">
              <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />{w}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export function ConnectorsPage() {
  const { data: connectors, isLoading } = useConnectors();
  const testMutation = useTestConnector();
  const deleteMutation = useDeleteConnector();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, TestConnectorResponse | null>>({});
  const [testingId, setTestingId] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingConnector, setEditingConnector] = useState<VectorDBConnector | undefined>();
  const [searchConfigConnector, setSearchConfigConnector] = useState<VectorDBConnector | null>(null);
  const [ingestionConfigConnector, setIngestionConfigConnector] = useState<VectorDBConnector | null>(null);
  const [bindingConnector, setBindingConnector] = useState<VectorDBConnector | null>(null);
  const [suggestionConnector, setSuggestionConnector] = useState<VectorDBConnector | null>(null);

  function openCreate() {
    setEditingConnector(undefined);
    setShowDialog(true);
  }

  function openEdit(conn: VectorDBConnector) {
    setEditingConnector(conn);
    setShowDialog(true);
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-48" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Vector DB Connectors</h1>
          <p className="text-sm text-muted-foreground mt-1">Connect your vector databases to gate access to stored embeddings.</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Add Connector</Button>
      </div>

      {!connectors || connectors.length === 0 ? (
        <EmptyState
          icon={<Database className="h-12 w-12" />}
          title="No connectors configured"
          description="Add a vector database connector to start protecting your AI retrieval pipeline."
          action={<Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Add Connector</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {connectors.map((conn) => {
            const activeResult = testResult[conn.id] ?? conn.diagnostics;
            return (
              <div key={conn.id} className="rounded-lg border bg-card p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                      {connectorLabels[conn.type] ?? conn.type}
                    </p>
                    <h3 className="font-semibold mt-1">{conn.name}</h3>
                  </div>
                  <StatusBadge status={conn.status} />
                </div>

                {/* Three-signal status row */}
                <div className="flex flex-wrap items-center gap-1.5">
                  {conn.connection_ready && !conn.search_ready && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-900/20 rounded-full px-2 py-0.5">
                      <AlertTriangle className="h-3 w-3" />No search config
                    </span>
                  )}
                  {conn.search_ready && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/20 rounded-full px-2 py-0.5">
                      <CheckCircle2 className="h-3 w-3" />Search ready
                    </span>
                  )}
                  {conn.ingestion_capable && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20 rounded-full px-2 py-0.5">
                      <ArrowDownToLine className="h-3 w-3" />Ingestion capable
                    </span>
                  )}
                  {conn.ingestion_ready && (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-violet-700 bg-violet-50 dark:text-violet-400 dark:bg-violet-900/20 rounded-full px-2 py-0.5">
                      <CheckCircle2 className="h-3 w-3" />Write configured
                    </span>
                  )}
                  <PolicyReadinessBadge level={conn.policy_readiness_level} coveragePct={conn.coverage_pct} />
                </div>

                <CoverageBar coveragePct={conn.coverage_pct} />

                {conn.connection_ready && !conn.search_ready && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    Connected, but not configured for retrieval.
                  </p>
                )}

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs">Indexes</p>
                    <p className="font-medium">{conn.index_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Records</p>
                    <p className="font-medium">{formatNumber(conn.record_count)}</p>
                  </div>
                </div>

                {conn.last_sync && (
                  <p className="text-xs text-muted-foreground">Last sync: {formatRelativeDate(conn.last_sync)}</p>
                )}

                {conn.last_tested_at && (
                  <p className="text-xs text-muted-foreground">Last tested: {formatRelativeDate(conn.last_tested_at)}</p>
                )}

                {conn.server_version && !activeResult && (
                  <p className="text-xs text-muted-foreground">Server: {conn.server_version}</p>
                )}

                {conn.error_message && !activeResult && (
                  <p className="text-xs text-red-600 bg-red-50 dark:bg-red-900/10 rounded p-2">{conn.error_message}</p>
                )}

                {activeResult && <TestResultPanel result={activeResult} />}

                <div className="flex flex-wrap gap-2 pt-2 border-t">
                  <Button variant="outline" size="sm" onClick={() => openEdit(conn)}>
                    <Pencil className="h-3 w-3 mr-1" />Edit
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setSearchConfigConnector(conn)}>
                    <Settings2 className="h-3 w-3 mr-1" />{conn.search_ready ? 'Search Config' : 'Configure Search'}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setBindingConnector(conn)}>
                    <Upload className="h-3 w-3 mr-1" />Bind Metadata
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setSuggestionConnector(conn)}>
                    <Sparkles className="h-3 w-3 mr-1" />Suggest Classifications
                  </Button>
                  {conn.ingestion_capable && (
                    <Button variant="outline" size="sm" onClick={() => setIngestionConfigConnector(conn)}>
                      <ArrowDownToLine className="h-3 w-3 mr-1" />{conn.ingestion_ready ? 'Write Config' : 'Configure Write'}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setTestingId(conn.id);
                      testMutation.mutate(conn.id, {
                        onSuccess: (result) => {
                          setTestResult((prev) => ({ ...prev, [conn.id]: result }));
                          setTestingId(null);
                        },
                        onError: () => setTestingId(null),
                      });
                    }}
                    disabled={testingId === conn.id}
                  >
                    {testingId === conn.id ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <TestTube className="h-3 w-3 mr-1" />
                    )}
                    Test
                  </Button>
                  {confirmDelete === conn.id ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => { deleteMutation.mutate(conn.id); setConfirmDelete(null); }}
                    >
                      Confirm Delete
                    </Button>
                  ) : (
                    <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(conn.id)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <ConnectorDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        mode={editingConnector ? 'edit' : 'create'}
        initialData={editingConnector}
      />

      {searchConfigConnector && (
        <SearchConfigDialog
          open={!!searchConfigConnector}
          onOpenChange={(open) => { if (!open) setSearchConfigConnector(null); }}
          connector={searchConfigConnector}
        />
      )}

      {ingestionConfigConnector && (
        <IngestionConfigDialog
          open={!!ingestionConfigConnector}
          onOpenChange={(open) => { if (!open) setIngestionConfigConnector(null); }}
          connector={ingestionConfigConnector}
        />
      )}

      {bindingConnector && (
        <BindingDialog
          open={!!bindingConnector}
          onOpenChange={(open) => { if (!open) setBindingConnector(null); }}
          connectorId={bindingConnector.id}
          connectorName={bindingConnector.name}
        />
      )}

      {suggestionConnector && (
        <SuggestionReviewDialog
          open={!!suggestionConnector}
          onOpenChange={(open) => { if (!open) setSuggestionConnector(null); }}
          connectorId={suggestionConnector.id}
          connectorName={suggestionConnector.name}
        />
      )}
    </div>
  );
}
