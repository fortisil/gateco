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
import { useCreateConnector, useUpdateConnector } from '@/hooks/useConnectors';
import { CONNECTOR_FIELDS } from '@/lib/connectorFields';
import type { ConnectorType, VectorDBConnector } from '@/types/connector';

const CONNECTOR_TYPES: { value: ConnectorType; label: string }[] = [
  { value: 'pgvector', label: 'pgvector' },
  { value: 'pinecone', label: 'Pinecone' },
  { value: 'opensearch', label: 'OpenSearch' },
  { value: 'supabase', label: 'Supabase' },
  { value: 'neon', label: 'Neon' },
  { value: 'weaviate', label: 'Weaviate' },
  { value: 'qdrant', label: 'Qdrant' },
  { value: 'milvus', label: 'Milvus' },
  { value: 'chroma', label: 'Chroma' },
];

interface ConnectorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  initialData?: VectorDBConnector;
}

export function ConnectorDialog({ open, onOpenChange, mode, initialData }: ConnectorDialogProps) {
  const createMutation = useCreateConnector();
  const updateMutation = useUpdateConnector();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const [name, setName] = React.useState('');
  const [type, setType] = React.useState<ConnectorType>('pgvector');
  const [config, setConfig] = React.useState<Record<string, string>>({});
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (open) {
      if (mode === 'edit' && initialData) {
        setName(initialData.name);
        setType(initialData.type);
        const nonSecretConfig: Record<string, string> = {};
        const fields = CONNECTOR_FIELDS[initialData.type];
        for (const field of fields) {
          if (!field.secret && initialData.config[field.name] !== undefined) {
            nonSecretConfig[field.name] = String(initialData.config[field.name]);
          }
        }
        setConfig(nonSecretConfig);
      } else {
        setName('');
        setType('pgvector');
        setConfig({});
      }
      setError('');
    }
  }, [open, mode, initialData]);

  const fields = CONNECTOR_FIELDS[type];

  const isDirty = React.useMemo(() => {
    if (mode === 'create') return name.trim().length > 0;
    if (!initialData) return false;
    if (name !== initialData.name) return true;
    return Object.keys(config).some((key) => {
      const field = fields.find((f) => f.name === key);
      if (field?.secret) return config[key]?.length > 0;
      return config[key] !== String(initialData.config[key] ?? '');
    });
  }, [name, config, mode, initialData, fields]);

  function validate(): string | null {
    if (!name.trim()) return 'Name is required';
    for (const field of fields) {
      if (field.required) {
        if (mode === 'create' && !config[field.name]?.trim()) {
          return `${field.label} is required`;
        }
        if (mode === 'edit' && !field.secret && !config[field.name]?.trim()) {
          return `${field.label} is required`;
        }
      }
      if (field.type === 'number' && config[field.name]) {
        const num = Number(config[field.name]);
        if (isNaN(num) || num < 1 || num > 65535) {
          return `${field.label} must be a number between 1 and 65535`;
        }
      }
    }
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

    const configPayload: Record<string, string | number> = {};
    for (const field of fields) {
      const val = config[field.name];
      if (mode === 'edit' && field.secret && !val) continue;
      if (val !== undefined && val !== '') {
        configPayload[field.name] = field.type === 'number' ? Number(val) : val;
      }
    }

    if (mode === 'edit' && initialData) {
      updateMutation.mutate(
        { id: initialData.id, data: { name: name.trim(), config: configPayload } },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to update connector'),
        }
      );
    } else {
      createMutation.mutate(
        { name: name.trim(), type, config: configPayload },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to create connector'),
        }
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? 'Add Connector' : 'Edit Connector'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Connect a vector database to gate access to stored embeddings.'
              : 'Update connector configuration.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Connector"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Type</label>
            <select
              value={type}
              onChange={(e) => {
                setType(e.target.value as ConnectorType);
                setConfig({});
              }}
              disabled={mode === 'edit'}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {CONNECTOR_TYPES.map((ct) => (
                <option key={ct.value} value={ct.value}>{ct.label}</option>
              ))}
            </select>
          </div>
          {fields.map((field) => (
            <div key={field.name} className="space-y-2">
              <label className="text-sm font-medium">{field.label}</label>
              <Input
                type={field.type === 'password' ? 'password' : 'text'}
                value={config[field.name] ?? ''}
                onChange={(e) => setConfig((prev) => ({ ...prev, [field.name]: e.target.value }))}
                placeholder={
                  mode === 'edit' && field.secret
                    ? '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022 (already set)'
                    : field.placeholder
                }
                required={mode === 'create' && field.required}
              />
            </div>
          ))}
          {error && (
            <p className="text-sm text-destructive bg-destructive/10 rounded-md p-2">{error}</p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending || (mode === 'edit' && !isDirty)}>
              {isPending ? 'Saving...' : mode === 'create' ? 'Add Connector' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
