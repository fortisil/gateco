import { cn } from '@/lib/utils';
import type { Sensitivity } from '@/types/gated-resource';

const sensitivityConfig: Record<Sensitivity, { label: string; className: string }> = {
  low: { label: 'Low', className: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' },
  medium: { label: 'Medium', className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  high: { label: 'High', className: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  critical: { label: 'Critical', className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 font-semibold' },
};

interface SensitivityBadgeProps {
  sensitivity: Sensitivity;
  className?: string;
}

export function SensitivityBadge({ sensitivity, className }: SensitivityBadgeProps) {
  const config = sensitivityConfig[sensitivity];
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', config.className, className)}>
      {config.label}
    </span>
  );
}
