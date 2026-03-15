import { cn } from '@/lib/utils';

interface UsageMeterProps {
  used: number;
  limit: number | null;
  label: string;
  tooltip?: string;
}

export function UsageMeter({ used, limit, label, tooltip }: UsageMeterProps) {
  const isUnlimited = limit === null;
  const percentage = isUnlimited ? 0 : limit === 0 ? 0 : Math.min((used / limit) * 100, 100);

  const status = percentage >= 95 ? 'danger' : percentage >= 80 ? 'warning' : 'normal';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-muted-foreground">
          {used} / {isUnlimited ? 'Unlimited' : limit}
        </span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={isUnlimited ? 0 : Math.round(percentage)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
        title={tooltip}
        className={cn(
          'h-2 w-full rounded-full bg-muted overflow-hidden',
          status === 'warning' && 'warning',
          status === 'danger' && 'danger'
        )}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all',
            status === 'normal' && 'bg-primary',
            status === 'warning' && 'bg-amber-400',
            status === 'danger' && 'bg-destructive'
          )}
          style={{ width: isUnlimited ? '0%' : `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
