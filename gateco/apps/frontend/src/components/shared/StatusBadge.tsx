import { cn } from '@/lib/utils';

type Status = 'connected' | 'error' | 'syncing' | 'disconnected' | 'active' | 'paused' | 'running';

const statusConfig: Record<Status, { label: string; className: string }> = {
  connected: { label: 'Connected', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  active: { label: 'Active', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  syncing: { label: 'Syncing', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  running: { label: 'Running', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  paused: { label: 'Paused', className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  disconnected: { label: 'Disconnected', className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  error: { label: 'Error', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
};

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.disconnected;
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium', config.className, className)}>
      <span className={cn(
        'h-1.5 w-1.5 rounded-full',
        status === 'syncing' || status === 'running' ? 'animate-pulse' : '',
        status === 'connected' || status === 'active' ? 'bg-emerald-500' :
        status === 'error' ? 'bg-red-500' :
        status === 'syncing' ? 'bg-amber-500' :
        status === 'running' ? 'bg-blue-500' :
        'bg-gray-400'
      )} />
      {config.label}
    </span>
  );
}
