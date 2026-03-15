import { useState, useEffect } from 'react';
import { useAdminApi } from './useAdminApi';

interface DbStatus {
  status: string;
  mode: string;
  lastError: string | null;
  migrationsApplied: number;
  dbUrlConfigured: boolean;
}

interface DbStatusBannerProps {
  onSetupClick: () => void;
}

/**
 * Banner that polls the database status on mount.
 * Hidden when status is "ready". Shows an amber bar when
 * the database is unconfigured or in error state.
 */
export function DbStatusBanner({ onSetupClick }: DbStatusBannerProps) {
  const { callApi } = useAdminApi();
  const [status, setStatus] = useState<DbStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchStatus() {
      const result = await callApi<DbStatus>('/api/admin/db/status');
      if (!cancelled) {
        setStatus(result.data);
        setLoading(false);
      }
    }

    fetchStatus();
    return () => { cancelled = true; };
  }, []);

  if (loading) return null;
  if (!status) return null;
  if (status.status === 'ready') return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-amber-400" />
        <span className="text-amber-800 text-sm font-medium">
          {status.status === 'error'
            ? `Database error: ${status.lastError || 'Unknown'}`
            : 'Database is not configured'}
        </span>
      </div>
      <button
        onClick={onSetupClick}
        className="bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium px-4 py-1.5 rounded transition-colors"
      >
        Set up database
      </button>
    </div>
  );
}
