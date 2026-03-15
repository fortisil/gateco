import { useState } from 'react';
import { ArrowRightLeft, Pencil, Play, Plus } from 'lucide-react';
import { usePipelines, useRunPipeline } from '@/hooks/usePipelines';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeDate, formatNumber } from '@/lib/formatters';
import { PipelineDialog } from './PipelineDialog';
import type { IngestionPipeline } from '@/types/pipeline';

export function PipelinesPage() {
  const { data: pipelines, isLoading } = usePipelines();
  const runMutation = useRunPipeline();
  const [showDialog, setShowDialog] = useState(false);
  const [editingPipeline, setEditingPipeline] = useState<IngestionPipeline | undefined>();

  function openCreate() {
    setEditingPipeline(undefined);
    setShowDialog(true);
  }

  function openEdit(pipeline: IngestionPipeline) {
    setEditingPipeline(pipeline);
    setShowDialog(true);
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ingestion Pipelines</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage pipelines that ingest data from connectors, apply Gateco envelopes, and populate the data catalog.
          </p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Create Pipeline</Button>
      </div>

      {!pipelines || pipelines.length === 0 ? (
        <EmptyState
          icon={<ArrowRightLeft className="h-12 w-12" />}
          title="No pipelines configured"
          description="Create a pipeline to ingest and classify data from your connected vector databases."
          action={<Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Create Pipeline</Button>}
        />
      ) : (
        <div className="space-y-4">
          {pipelines.map((pipeline) => (
            <div key={pipeline.id} className="rounded-lg border bg-card p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold text-lg">{pipeline.name}</h3>
                    <StatusBadge status={pipeline.status} />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Source: {pipeline.source_connector_name}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => openEdit(pipeline)}>
                    <Pencil className="h-3 w-3 mr-1" />Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runMutation.mutate(pipeline.id)}
                    disabled={runMutation.isPending || pipeline.status === 'running'}
                  >
                    <Play className="h-3 w-3 mr-1" />Run Now
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">Schedule</p>
                  <p className="font-medium font-mono text-xs">{pipeline.schedule ?? 'Manual'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Last Run</p>
                  <p className="font-medium">{pipeline.last_run ? formatRelativeDate(pipeline.last_run) : 'Never'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Records Processed</p>
                  <p className="font-medium">{formatNumber(pipeline.records_processed)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Errors</p>
                  <p className={`font-medium ${pipeline.error_count > 0 ? 'text-red-600' : ''}`}>
                    {pipeline.error_count}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Envelope</p>
                  <div className="flex gap-1 mt-0.5">
                    {pipeline.envelope_config.encrypt && <span className="text-xs bg-primary/10 text-primary rounded px-1.5 py-0.5">Encrypt</span>}
                    {pipeline.envelope_config.classify && <span className="text-xs bg-primary/10 text-primary rounded px-1.5 py-0.5">Classify</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <PipelineDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        mode={editingPipeline ? 'edit' : 'create'}
        initialData={editingPipeline}
      />
    </div>
  );
}
