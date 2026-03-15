import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { useDataCatalog } from '@/hooks/useDataCatalog';
import { ClassificationBadge } from '@/components/shared/ClassificationBadge';
import { SensitivityBadge } from '@/components/shared/SensitivityBadge';
import { DataTable, type Column } from '@/components/shared/DataTable';
import { EmptyState } from '@/components/shared/EmptyState';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { GatedResource, Classification, Sensitivity } from '@/types/gated-resource';

export function DataCatalogPage() {
  const navigate = useNavigate();
  const [classification, setClassification] = useState<Classification | ''>('');
  const [sensitivity, setSensitivity] = useState<Sensitivity | ''>('');

  const filters = {
    ...(classification ? { classification } : {}),
    ...(sensitivity ? { sensitivity } : {}),
  };

  const { data, isLoading } = useDataCatalog(Object.keys(filters).length > 0 ? filters : undefined);

  const columns: Column<GatedResource>[] = [
    {
      key: 'title',
      header: 'Title',
      render: (item) => (
        <div>
          <p className="font-medium">{item.title}</p>
          {item.description && <p className="text-xs text-muted-foreground truncate max-w-xs">{item.description}</p>}
        </div>
      ),
    },
    {
      key: 'classification',
      header: 'Classification',
      render: (item) => <ClassificationBadge classification={item.classification} />,
    },
    {
      key: 'sensitivity',
      header: 'Sensitivity',
      render: (item) => <SensitivityBadge sensitivity={item.sensitivity} />,
    },
    {
      key: 'domain',
      header: 'Domain',
      render: (item) => <span className="text-muted-foreground">{item.domain}</span>,
    },
    {
      key: 'labels',
      header: 'Labels',
      render: (item) => (
        <div className="flex flex-wrap gap-1">
          {item.labels.slice(0, 3).map((label) => (
            <Badge key={label} variant="outline" className="text-xs">{label}</Badge>
          ))}
          {item.labels.length > 3 && <Badge variant="outline" className="text-xs">+{item.labels.length - 3}</Badge>}
        </div>
      ),
    },
    {
      key: 'chunks',
      header: 'Chunks',
      render: (item) => <span className="text-muted-foreground">{item.chunk_ids.length}</span>,
      className: 'text-center',
    },
    {
      key: 'source',
      header: 'Source',
      render: (item) => <span className="text-xs text-muted-foreground">{item.source_connector_name}</span>,
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const items = data?.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Data Catalog</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Browse and manage gated resources ingested from your vector databases.
          Resources are created through ingestion pipelines.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={classification}
          onChange={(e) => setClassification(e.target.value as Classification | '')}
          className="rounded-md border bg-background px-3 py-2 text-sm"
        >
          <option value="">All Classifications</option>
          <option value="public">Public</option>
          <option value="internal">Internal</option>
          <option value="confidential">Confidential</option>
          <option value="restricted">Restricted</option>
        </select>

        <select
          value={sensitivity}
          onChange={(e) => setSensitivity(e.target.value as Sensitivity | '')}
          className="rounded-md border bg-background px-3 py-2 text-sm"
        >
          <option value="">All Sensitivities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-12 w-12" />}
          title="No resources in catalog"
          description="Resources appear here after being ingested through pipelines. Set up a connector and pipeline to get started."
        />
      ) : (
        <DataTable
          columns={columns}
          data={items}
          keyExtractor={(item) => item.id}
          onRowClick={(item) => navigate(`/data-catalog/${item.id}`)}
        />
      )}
    </div>
  );
}
