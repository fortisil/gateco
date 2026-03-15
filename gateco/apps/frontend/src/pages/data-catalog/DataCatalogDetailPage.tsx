import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Lock, Unlock, CheckCircle, XCircle } from 'lucide-react';
import { useDataCatalogItem } from '@/hooks/useDataCatalog';
import { ClassificationBadge } from '@/components/shared/ClassificationBadge';
import { SensitivityBadge } from '@/components/shared/SensitivityBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeDate } from '@/lib/formatters';

export function DataCatalogDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: item, isLoading } = useDataCatalogItem(id!);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!item) {
    return <p className="text-muted-foreground">Resource not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/data-catalog"><ArrowLeft className="h-4 w-4 mr-1" />Back</Link>
        </Button>
      </div>

      {/* Header */}
      <div className="rounded-lg border bg-card p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{item.title}</h1>
            {item.description && <p className="text-muted-foreground mt-1">{item.description}</p>}
          </div>
          <div className="flex gap-2">
            <ClassificationBadge classification={item.classification} />
            <SensitivityBadge sensitivity={item.sensitivity} />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground text-xs">Domain</p>
            <p className="font-medium">{item.domain}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Encryption</p>
            <p className="font-medium capitalize">{item.encryption_mode.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Source</p>
            <p className="font-medium">{item.source_connector_name}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Chunks</p>
            <p className="font-medium">{item.chunk_ids.length}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-1">
          {item.labels.map((label) => (
            <Badge key={label} variant="outline">{label}</Badge>
          ))}
        </div>
      </div>

      {/* Chunks */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Chunks</h2>
        <div className="space-y-2">
          {item.chunks.map((chunk) => (
            <div key={chunk.id} className="rounded-lg border p-4 flex items-start gap-3">
              <div className="mt-0.5">
                {chunk.encrypted
                  ? <Lock className="h-4 w-4 text-amber-500" />
                  : <Unlock className="h-4 w-4 text-muted-foreground" />
                }
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-muted-foreground">#{chunk.index}</span>
                  <span className="text-xs text-muted-foreground">{chunk.vector_id}</span>
                  {chunk.encrypted && <Badge variant="outline" className="text-xs">Encrypted</Badge>}
                </div>
                <p className="text-sm">{chunk.preview}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Applicable Policies */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Applicable Policies</h2>
        <div className="space-y-2">
          {item.applicable_policies.map((pol) => (
            <div key={pol.id} className="rounded-lg border p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge variant={pol.effect === 'allow' ? 'default' : 'destructive'} className="text-xs">
                  {pol.effect}
                </Badge>
                <span className="font-medium">{pol.name}</span>
              </div>
              <Badge variant="outline" className="text-xs uppercase">{pol.type}</Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Access */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recent Access</h2>
        <div className="space-y-2">
          {item.recent_access.map((access) => (
            <div key={access.id} className="rounded-lg border p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {access.outcome === 'allowed'
                  ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                  : <XCircle className="h-4 w-4 text-red-500" />
                }
                <span className="text-sm">{access.principal_name}</span>
              </div>
              <span className="text-xs text-muted-foreground">{formatRelativeDate(access.timestamp)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
