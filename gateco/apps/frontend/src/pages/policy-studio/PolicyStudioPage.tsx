import { useState } from 'react';
import { Shield, Plus, Pencil, Trash2, Play, Archive } from 'lucide-react';
import { EntitlementGate } from '@/components/billing/EntitlementGate';
import { EmptyState } from '@/components/shared/EmptyState';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { usePolicies, useDeletePolicy, useActivatePolicy, useArchivePolicy } from '@/hooks/usePolicies';
import { PolicyDialog } from './PolicyDialog';
import { formatRelativeDate } from '@/lib/formatters';
import type { Policy, PolicyType } from '@/types/policy';

const typeLabels: Record<PolicyType, string> = {
  rbac: 'RBAC',
  abac: 'ABAC',
  rebac: 'ReBAC',
};

const statusMap = {
  active: 'active',
  draft: 'paused',
  archived: 'disconnected',
} as const;

export function PolicyStudioPage() {
  const { data: policies, isLoading } = usePolicies();
  const deleteMutation = useDeletePolicy();
  const activateMutation = useActivatePolicy();
  const archiveMutation = useArchivePolicy();
  const [showDialog, setShowDialog] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | undefined>();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  function openCreate() {
    setEditingPolicy(undefined);
    setShowDialog(true);
  }

  function openEdit(policy: Policy) {
    setEditingPolicy(policy);
    setShowDialog(true);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Policy Studio</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Create and manage RBAC, ABAC, and ReBAC policies that control access to your gated resources.
          </p>
        </div>
        <EntitlementGate feature="policy_studio" mode="hide">
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Create Policy</Button>
        </EntitlementGate>
      </div>

      <EntitlementGate feature="policy_studio">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}
          </div>
        ) : !policies || policies.length === 0 ? (
          <EmptyState
            icon={<Shield className="h-12 w-12" />}
            title="No policies created"
            description="Create your first access control policy to start gating retrieval access."
            action={<Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Create Policy</Button>}
          />
        ) : (
          <div className="space-y-4">
            {policies.map((policy) => (
              <div key={policy.id} className="rounded-lg border bg-card p-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{policy.name}</h3>
                      <Badge variant="outline">{typeLabels[policy.type]}</Badge>
                      <StatusBadge status={statusMap[policy.status] ?? policy.status} />
                      <Badge variant={policy.effect === 'allow' ? 'default' : 'destructive'}>
                        {policy.effect}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{policy.description}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button variant="outline" size="sm" onClick={() => openEdit(policy)}>
                      <Pencil className="h-3 w-3 mr-1" />Edit
                    </Button>
                    {policy.status === 'draft' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => activateMutation.mutate(policy.id)}
                        disabled={activateMutation.isPending}
                      >
                        <Play className="h-3 w-3 mr-1" />Activate
                      </Button>
                    )}
                    {policy.status === 'active' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => archiveMutation.mutate(policy.id)}
                        disabled={archiveMutation.isPending}
                      >
                        <Archive className="h-3 w-3 mr-1" />Archive
                      </Button>
                    )}
                    {confirmDelete === policy.id ? (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => { deleteMutation.mutate(policy.id); setConfirmDelete(null); }}
                      >
                        Confirm Delete
                      </Button>
                    ) : (
                      <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(policy.id)}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs">Rules</p>
                    <p className="font-medium">{policy.rules.length}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Resource Selectors</p>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {policy.resource_selectors.map((sel) => (
                        <span key={sel} className="text-xs bg-primary/10 text-primary rounded px-1.5 py-0.5 font-mono">{sel}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Version</p>
                    <p className="font-medium">v{policy.version}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Last Updated</p>
                    <p className="font-medium">{formatRelativeDate(policy.updated_at)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </EntitlementGate>

      <PolicyDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        mode={editingPolicy ? 'edit' : 'create'}
        initialData={editingPolicy}
      />
    </div>
  );
}
