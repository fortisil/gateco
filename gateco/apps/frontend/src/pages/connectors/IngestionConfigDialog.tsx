import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { INGESTION_CONFIG_FIELDS } from '@/lib/connectorFields';
import { useUpdateIngestionConfig } from '@/hooks/useConnectors';
import type { VectorDBConnector, IngestionConfig } from '@/types/connector';

interface IngestionConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connector: VectorDBConnector;
}

export function IngestionConfigDialog({ open, onOpenChange, connector }: IngestionConfigDialogProps) {
  const fields = useMemo(() => INGESTION_CONFIG_FIELDS[connector.type] || [], [connector.type]);
  const mutation = useUpdateIngestionConfig();
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      const initial: Record<string, string> = {};
      for (const field of fields) {
        const existing = connector.ingestion_config?.[field.name];
        if (existing != null) {
          initial[field.name] = Array.isArray(existing) ? existing.join(', ') : String(existing);
        } else {
          initial[field.name] = '';
        }
      }
      setValues(initial);
      setError(null);
    }
  }, [open, connector.id, connector.ingestion_config, fields]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    for (const field of fields) {
      if (field.required && !values[field.name]?.trim()) {
        setError(`${field.label} is required`);
        return;
      }
    }

    const ingestion_config: IngestionConfig = {};
    for (const field of fields) {
      const val = values[field.name]?.trim();
      if (!val) continue;
      if (field.type === 'number') {
        ingestion_config[field.name] = String(parseInt(val, 10));
      } else if (field.name === 'metadata_fields') {
        ingestion_config[field.name] = val.split(',').map((s: string) => s.trim()).filter(Boolean);
      } else {
        ingestion_config[field.name] = val;
      }
    }

    mutation.mutate(
      { id: connector.id, ingestion_config },
      {
        onSuccess: () => onOpenChange(false),
        onError: (err) => setError(err instanceof Error ? err.message : 'Failed to save'),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Configure Ingestion — {connector.name}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((field) => (
            <div key={field.name} className="space-y-1">
              <label className="text-sm font-medium">
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              {field.type === 'select' && field.options ? (
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={values[field.name] || field.placeholder}
                  onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                >
                  {field.options.map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              ) : (
                <Input
                  type={field.type === 'number' ? 'number' : 'text'}
                  placeholder={field.placeholder}
                  value={values[field.name] || ''}
                  onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                />
              )}
            </div>
          ))}

          {fields.length === 0 && (
            <p className="text-sm text-muted-foreground">
              This connector type does not support ingestion.
            </p>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-50 dark:bg-red-900/10 rounded p-2">{error}</p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending || fields.length === 0}>
              {mutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
