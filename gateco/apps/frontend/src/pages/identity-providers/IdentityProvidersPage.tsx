import { useState } from 'react';
import { KeyRound, Plus, Pencil, RefreshCw, Trash2 } from 'lucide-react';
import { useIdentityProviders, useSyncIdentityProvider, useDeleteIdentityProvider } from '@/hooks/useIdentityProviders';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeDate, formatNumber } from '@/lib/formatters';
import { IdentityProviderDialog } from './IdentityProviderDialog';
import type { IdentityProviderType, IdentityProvider } from '@/types/identity-provider';

const providerIcons: Record<IdentityProviderType, string> = {
  azure_entra_id: 'Azure Entra ID',
  aws_iam: 'AWS IAM',
  gcp: 'Google Cloud',
  okta: 'Okta',
};

export function IdentityProvidersPage() {
  const { data: providers, isLoading } = useIdentityProviders();
  const syncMutation = useSyncIdentityProvider();
  const deleteMutation = useDeleteIdentityProvider();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingProvider, setEditingProvider] = useState<IdentityProvider | undefined>();

  function openCreate() {
    setEditingProvider(undefined);
    setShowDialog(true);
  }

  function openEdit(idp: IdentityProvider) {
    setEditingProvider(idp);
    setShowDialog(true);
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2].map((i) => <Skeleton key={i} className="h-48" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Identity Providers</h1>
          <p className="text-sm text-muted-foreground mt-1">Connect identity providers to sync principals, groups, and roles.</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Connect Provider</Button>
      </div>

      {!providers || providers.length === 0 ? (
        <EmptyState
          icon={<KeyRound className="h-12 w-12" />}
          title="No identity providers connected"
          description="Connect an identity provider to sync your users, groups, and roles for policy evaluation."
          action={<Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Connect Provider</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {providers.map((idp) => (
            <div key={idp.id} className="rounded-lg border bg-card p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                    {providerIcons[idp.type]}
                  </p>
                  <h3 className="font-semibold mt-1">{idp.name}</h3>
                </div>
                <StatusBadge status={idp.status} />
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">Principals</p>
                  <p className="font-medium">{formatNumber(idp.principal_count)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Groups</p>
                  <p className="font-medium">{formatNumber(idp.group_count)}</p>
                </div>
              </div>

              {idp.last_sync && (
                <p className="text-xs text-muted-foreground">Last sync: {formatRelativeDate(idp.last_sync)}</p>
              )}

              {idp.error_message && (
                <p className="text-xs text-red-600 bg-red-50 dark:bg-red-900/10 rounded p-2">{idp.error_message}</p>
              )}

              <div className="flex gap-2 pt-2 border-t">
                <Button variant="outline" size="sm" onClick={() => openEdit(idp)}>
                  <Pencil className="h-3 w-3 mr-1" />Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => syncMutation.mutate(idp.id)}
                  disabled={syncMutation.isPending}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />Sync
                </Button>
                {confirmDelete === idp.id ? (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => { deleteMutation.mutate(idp.id); setConfirmDelete(null); }}
                  >
                    Confirm Delete
                  </Button>
                ) : (
                  <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(idp.id)}>
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <IdentityProviderDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        mode={editingProvider ? 'edit' : 'create'}
        initialData={editingProvider}
      />
    </div>
  );
}
