import type { ReactNode } from 'react';
import type { FeatureKey } from '@/types/billing';
import { useEntitlementContext } from '@/contexts/EntitlementContext';
import { UpgradeModal } from './UpgradeModal';

interface EntitlementGateProps {
  feature?: FeatureKey;
  features?: FeatureKey[];
  requireAll?: boolean;
  mode?: 'disable' | 'hide' | 'replace';
  fallback?: ReactNode;
  children: ReactNode;
}

export function EntitlementGate({
  feature,
  features,
  requireAll = true,
  mode = 'replace',
  fallback,
  children,
}: EntitlementGateProps) {
  const { hasFeature, getRequiredTierForFeature } = useEntitlementContext();

  let isEntitled = false;
  if (feature) {
    isEntitled = hasFeature(feature);
  } else if (features && features.length > 0) {
    isEntitled = requireAll
      ? features.every((f) => hasFeature(f))
      : features.some((f) => hasFeature(f));
  } else {
    isEntitled = true;
  }

  if (isEntitled) {
    return <>{children}</>;
  }

  if (mode === 'hide') {
    return null;
  }

  if (mode === 'disable') {
    return <div className="opacity-50 pointer-events-none">{children}</div>;
  }

  // mode === 'replace'
  if (fallback) {
    return <>{fallback}</>;
  }

  const gatingFeature = feature ?? features?.[0];
  if (gatingFeature) {
    return <UpgradeModal feature={gatingFeature} requiredTier={getRequiredTierForFeature(gatingFeature)} />;
  }

  return null;
}
