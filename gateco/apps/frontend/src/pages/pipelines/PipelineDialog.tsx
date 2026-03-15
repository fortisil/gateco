import * as React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreatePipeline, useUpdatePipeline } from '@/hooks/usePipelines';
import { useConnectors } from '@/hooks/useConnectors';
import type { IngestionPipeline, EnvelopeConfig } from '@/types/pipeline';

const DEFAULT_ENVELOPE: EnvelopeConfig = {
  encrypt: false,
  classify: true,
  default_classification: 'internal',
  default_sensitivity: 'medium',
  label_extraction: true,
};

interface PipelineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  initialData?: IngestionPipeline;
}

export function PipelineDialog({ open, onOpenChange, mode, initialData }: PipelineDialogProps) {
  const createMutation = useCreatePipeline();
  const updateMutation = useUpdatePipeline();
  const { data: connectors } = useConnectors();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const [name, setName] = React.useState('');
  const [sourceConnectorId, setSourceConnectorId] = React.useState('');
  const [schedule, setSchedule] = React.useState('manual');
  const [envelope, setEnvelope] = React.useState<EnvelopeConfig>(DEFAULT_ENVELOPE);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (open) {
      if (mode === 'edit' && initialData) {
        setName(initialData.name);
        setSourceConnectorId(initialData.source_connector_id);
        setSchedule(initialData.schedule ?? 'manual');
        setEnvelope({ ...initialData.envelope_config });
      } else {
        setName('');
        setSourceConnectorId(connectors?.[0]?.id ?? '');
        setSchedule('manual');
        setEnvelope({ ...DEFAULT_ENVELOPE });
      }
      setError('');
    }
  }, [open, mode, initialData, connectors]);

  const isDirty = React.useMemo(() => {
    if (mode === 'create') return name.trim().length > 0;
    if (!initialData) return false;
    if (name !== initialData.name) return true;
    if (sourceConnectorId !== initialData.source_connector_id) return true;
    const origSchedule = initialData.schedule ?? 'manual';
    if (schedule !== origSchedule) return true;
    const ec = initialData.envelope_config;
    return (
      envelope.encrypt !== ec.encrypt ||
      envelope.classify !== ec.classify ||
      envelope.default_classification !== ec.default_classification ||
      envelope.default_sensitivity !== ec.default_sensitivity ||
      envelope.label_extraction !== ec.label_extraction
    );
  }, [name, sourceConnectorId, schedule, envelope, mode, initialData]);

  function validate(): string | null {
    if (!name.trim()) return 'Name is required';
    if (!sourceConnectorId) return 'Source connector is required';
    if (!schedule.trim()) return 'Schedule is required';
    return null;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setError(err);
      return;
    }
    setError('');

    const payload = {
      name: name.trim(),
      source_connector_id: sourceConnectorId,
      schedule: schedule === 'manual' ? null : schedule,
      envelope_config: envelope,
    };

    if (mode === 'edit' && initialData) {
      updateMutation.mutate(
        { id: initialData.id, data: payload },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to update pipeline'),
        }
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => onOpenChange(false),
        onError: (err) => setError(err instanceof Error ? err.message : 'Failed to create pipeline'),
      });
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? 'Create Pipeline' : 'Edit Pipeline'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Set up a pipeline to ingest and classify data from a connector.'
              : 'Update pipeline configuration.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Pipeline" required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Source Connector</label>
            <select
              value={sourceConnectorId}
              onChange={(e) => setSourceConnectorId(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select a connector...</option>
              {connectors?.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Schedule</label>
            <Input
              value={schedule}
              onChange={(e) => setSchedule(e.target.value)}
              placeholder="manual or cron expression (e.g. 0 */6 * * *)"
            />
            <p className="text-xs text-muted-foreground">Enter "manual" for manual runs or a cron expression.</p>
          </div>

          <div className="space-y-3 border-t pt-4">
            <h4 className="text-sm font-medium text-muted-foreground">Envelope Configuration</h4>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={envelope.encrypt}
                onChange={(e) => setEnvelope((prev) => ({ ...prev, encrypt: e.target.checked }))}
                className="rounded border-input"
              />
              Enable encryption
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={envelope.classify}
                onChange={(e) => setEnvelope((prev) => ({ ...prev, classify: e.target.checked }))}
                className="rounded border-input"
              />
              Enable classification
            </label>
            <div className="space-y-1">
              <label className="text-sm font-medium">Default Classification</label>
              <select
                value={envelope.default_classification}
                onChange={(e) => setEnvelope((prev) => ({ ...prev, default_classification: e.target.value as EnvelopeConfig['default_classification'] }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="public">Public</option>
                <option value="internal">Internal</option>
                <option value="confidential">Confidential</option>
                <option value="restricted">Restricted</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Default Sensitivity</label>
              <select
                value={envelope.default_sensitivity}
                onChange={(e) => setEnvelope((prev) => ({ ...prev, default_sensitivity: e.target.value as EnvelopeConfig['default_sensitivity'] }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={envelope.label_extraction}
                onChange={(e) => setEnvelope((prev) => ({ ...prev, label_extraction: e.target.checked }))}
                className="rounded border-input"
              />
              Enable label extraction
            </label>
          </div>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 rounded-md p-2">{error}</p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending || (mode === 'edit' && !isDirty)}>
              {isPending ? 'Saving...' : mode === 'create' ? 'Create Pipeline' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
