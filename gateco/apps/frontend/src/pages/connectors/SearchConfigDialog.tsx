import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SEARCH_CONFIG_FIELDS } from '@/lib/connectorFields';
import { useUpdateSearchConfig } from '@/hooks/useConnectors';
import type { VectorDBConnector, SearchConfig, DiscoveredResource } from '@/types/connector';

interface SearchConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connector: VectorDBConnector;
}

export function SearchConfigDialog({ open, onOpenChange, connector }: SearchConfigDialogProps) {
  const fields = useMemo(() => SEARCH_CONFIG_FIELDS[connector.type] || [], [connector.type]);
  const mutation = useUpdateSearchConfig();
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  // Discovered resources from diagnostics for dropdown suggestions
  const discoveredResources: DiscoveredResource[] = connector.diagnostics?.resources ?? [];

  useEffect(() => {
    if (open) {
      const initial: Record<string, string> = {};
      for (const field of fields) {
        const existing = connector.search_config?.[field.name];
        if (existing != null) {
          initial[field.name] = Array.isArray(existing) ? existing.join(', ') : String(existing);
        } else {
          initial[field.name] = '';
        }
      }
      setValues(initial);
      setError(null);
    }
  }, [open, connector.id, connector.search_config, fields]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validate required fields
    for (const field of fields) {
      if (field.required && !values[field.name]?.trim()) {
        setError(`${field.label} is required`);
        return;
      }
    }

    // Build search_config
    const search_config: SearchConfig = {};
    for (const field of fields) {
      const val = values[field.name]?.trim();
      if (!val) continue;
      if (field.type === 'number') {
        search_config[field.name] = parseInt(val, 10);
      } else if (field.name === 'properties' || field.name === 'output_fields') {
        search_config[field.name] = val.split(',').map((s: string) => s.trim()).filter(Boolean);
      } else {
        search_config[field.name] = val;
      }
    }

    mutation.mutate(
      { id: connector.id, search_config },
      {
        onSuccess: () => onOpenChange(false),
        onError: (err) => setError(err instanceof Error ? err.message : 'Failed to save'),
      },
    );
  }

  // Get suggestions for the primary resource field based on discovered resources
  function getSuggestions(fieldName: string): string[] {
    if (!discoveredResources.length) return [];
    if (['table_name', 'index_name', 'collection_name', 'class_name'].includes(fieldName)) {
      return discoveredResources.map((r) => r.name);
    }
    return [];
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Configure Search — {connector.name}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((field) => {
            const suggestions = getSuggestions(field.name);
            return (
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
                  <>
                    <Input
                      type={field.type === 'number' ? 'number' : 'text'}
                      placeholder={field.placeholder}
                      value={values[field.name] || ''}
                      onChange={(e) => setValues((prev) => ({ ...prev, [field.name]: e.target.value }))}
                      list={suggestions.length > 0 ? `suggestions-${field.name}` : undefined}
                    />
                    {suggestions.length > 0 && (
                      <datalist id={`suggestions-${field.name}`}>
                        {suggestions.map((s) => (
                          <option key={s} value={s} />
                        ))}
                      </datalist>
                    )}
                  </>
                )}
              </div>
            );
          })}

          {discoveredResources.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {discoveredResources.length} {connector.diagnostics?.resource_kind ?? 'resource'}
              {discoveredResources.length !== 1 ? 's' : ''} discovered — suggestions available in dropdowns.
            </p>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-50 dark:bg-red-900/10 rounded p-2">{error}</p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
