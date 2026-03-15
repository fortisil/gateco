import { cn } from '@/lib/utils';
import type { Classification } from '@/types/gated-resource';

const classificationConfig: Record<Classification, { label: string; className: string }> = {
  public: { label: 'Public', className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  internal: { label: 'Internal', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  confidential: { label: 'Confidential', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  restricted: { label: 'Restricted', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
};

interface ClassificationBadgeProps {
  classification: Classification;
  className?: string;
}

export function ClassificationBadge({ classification, className }: ClassificationBadgeProps) {
  const config = classificationConfig[classification];
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', config.className, className)}>
      {config.label}
    </span>
  );
}
