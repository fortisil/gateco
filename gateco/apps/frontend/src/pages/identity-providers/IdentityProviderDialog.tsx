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
import { useCreateIdentityProvider, useUpdateIdentityProvider } from '@/hooks/useIdentityProviders';
import { IDENTITY_PROVIDER_FIELDS } from '@/lib/identityProviderFields';
import type { IdentityProviderType, IdentityProvider, SyncConfig } from '@/types/identity-provider';

const PROVIDER_TYPES: { value: IdentityProviderType; label: string }[] = [
  { value: 'azure_entra_id', label: 'Azure Entra ID' },
  { value: 'aws_iam', label: 'AWS IAM' },
  { value: 'gcp', label: 'Google Cloud' },
  { value: 'okta', label: 'Okta' },
];

const DEFAULT_SYNC_CONFIG: SyncConfig = {
  auto_sync: true,
  sync_interval_minutes: 60,
  sync_groups: true,
  sync_roles: true,
  sync_attributes: true,
};

interface IdentityProviderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  initialData?: IdentityProvider;
}

export function IdentityProviderDialog({ open, onOpenChange, mode, initialData }: IdentityProviderDialogProps) {
  const createMutation = useCreateIdentityProvider();
  const updateMutation = useUpdateIdentityProvider();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const [name, setName] = React.useState('');
  const [type, setType] = React.useState<IdentityProviderType>('azure_entra_id');
  const [config, setConfig] = React.useState<Record<string, string>>({});
  const [syncConfig, setSyncConfig] = React.useState<SyncConfig>(DEFAULT_SYNC_CONFIG);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (open) {
      if (mode === 'edit' && initialData) {
        setName(initialData.name);
        setType(initialData.type);
        setConfig({});
        setSyncConfig({ ...initialData.sync_config });
      } else {
        setName('');
        setType('azure_entra_id');
        setConfig({});
        setSyncConfig({ ...DEFAULT_SYNC_CONFIG });
      }
      setError('');
    }
  }, [open, mode, initialData]);

  const fields = IDENTITY_PROVIDER_FIELDS[type];

  const isDirty = React.useMemo(() => {
    if (mode === 'create') return name.trim().length > 0;
    if (!initialData) return false;
    if (name !== initialData.name) return true;
    if (Object.values(config).some((v) => v.length > 0)) return true;
    const sc = initialData.sync_config;
    return (
      syncConfig.auto_sync !== sc.auto_sync ||
      syncConfig.sync_interval_minutes !== sc.sync_interval_minutes ||
      syncConfig.sync_groups !== sc.sync_groups ||
      syncConfig.sync_roles !== sc.sync_roles ||
      syncConfig.sync_attributes !== sc.sync_attributes
    );
  }, [name, config, syncConfig, mode, initialData]);

  function validate(): string | null {
    if (!name.trim()) return 'Name is required';
    if (mode === 'create') {
      for (const field of fields) {
        if (field.required && !config[field.name]?.trim()) {
          return `${field.label} is required`;
        }
      }
    }
    if (syncConfig.sync_interval_minutes < 1) return 'Sync interval must be at least 1 minute';
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

    const configPayload: Record<string, string> = {};
    for (const field of fields) {
      const val = config[field.name];
      if (mode === 'edit' && field.secret && !val) continue;
      if (val) configPayload[field.name] = val;
    }

    if (mode === 'edit' && initialData) {
      updateMutation.mutate(
        {
          id: initialData.id,
          data: {
            name: name.trim(),
            config: Object.keys(configPayload).length > 0 ? configPayload : undefined,
            sync_config: syncConfig,
          },
        },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to update provider'),
        }
      );
    } else {
      createMutation.mutate(
        { name: name.trim(), type, config: configPayload, sync_config: syncConfig },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to create provider'),
        }
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? 'Connect Identity Provider' : 'Edit Identity Provider'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Connect an identity provider to sync principals, groups, and roles.'
              : 'Update identity provider configuration.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Identity Provider" required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Type</label>
            <select
              value={type}
              onChange={(e) => { setType(e.target.value as IdentityProviderType); setConfig({}); }}
              disabled={mode === 'edit'}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {PROVIDER_TYPES.map((pt) => (
                <option key={pt.value} value={pt.value}>{pt.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Configuration</h4>
            {fields.map((field) => (
              <div key={field.name} className="space-y-1">
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
          </div>

          <div className="space-y-3 border-t pt-4">
            <h4 className="text-sm font-medium text-muted-foreground">Sync Settings</h4>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={syncConfig.auto_sync}
                onChange={(e) => setSyncConfig((prev) => ({ ...prev, auto_sync: e.target.checked }))}
                className="rounded border-input"
              />
              Enable auto sync
            </label>
            <div className="space-y-1">
              <label className="text-sm font-medium">Sync Interval (minutes)</label>
              <Input
                type="number"
                min={1}
                value={syncConfig.sync_interval_minutes}
                onChange={(e) => setSyncConfig((prev) => ({ ...prev, sync_interval_minutes: Number(e.target.value) || 60 }))}
              />
            </div>
            <div className="space-y-2">
              {(['sync_groups', 'sync_roles', 'sync_attributes'] as const).map((key) => (
                <label key={key} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={syncConfig[key]}
                    onChange={(e) => setSyncConfig((prev) => ({ ...prev, [key]: e.target.checked }))}
                    className="rounded border-input"
                  />
                  Sync {key.replace('sync_', '')}
                </label>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 rounded-md p-2">{error}</p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending || (mode === 'edit' && !isDirty)}>
              {isPending ? 'Saving...' : mode === 'create' ? 'Connect Provider' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
