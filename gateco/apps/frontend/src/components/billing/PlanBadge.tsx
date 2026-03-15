import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { PlanTier } from '@/types/billing';

interface PlanBadgeProps {
  tier: PlanTier;
  className?: string;
}

const tierStyles: Record<PlanTier, string> = {
  free: 'bg-gray-500/15 text-gray-300 border-gray-500/30',
  pro: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  enterprise: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
};

export function PlanBadge({ tier, className }: PlanBadgeProps) {
  return (
    <Badge variant="outline" className={cn('capitalize', tierStyles[tier], className)}>
      {tier}
    </Badge>
  );
}
