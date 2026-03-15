import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { PlanTier, FeatureKey } from '@/types/billing';
import { getFeatureInfo } from '@/lib/planFeatures';

interface UpgradeModalProps {
  feature: FeatureKey;
  requiredTier: PlanTier;
}

export function UpgradeModal({ feature, requiredTier }: UpgradeModalProps) {
  const info = getFeatureInfo(feature);
  const tierLabel = requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1);

  return (
    <div className="rounded-lg border border-dashed border-primary/30 bg-primary/5 p-8 text-center space-y-4">
      <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
        <Sparkles className="h-6 w-6 text-primary" />
      </div>
      <div>
        <h3 className="text-lg font-semibold">{info?.label ?? 'Feature'}</h3>
        <p className="text-sm text-muted-foreground mt-1">
          {info?.description ?? 'This feature requires an upgrade.'}
        </p>
      </div>
      <p className="text-sm text-muted-foreground">
        Available on the <span className="font-medium text-foreground">{tierLabel}</span> plan and above.
      </p>
      <Button asChild>
        <Link to="/usage-billing">Upgrade to {tierLabel}</Link>
      </Button>
    </div>
  );
}
