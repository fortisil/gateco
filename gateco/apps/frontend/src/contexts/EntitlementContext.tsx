import { createContext, useContext, useMemo } from 'react';
import type { ReactNode } from 'react';
import type { FeatureKey, PlanTier } from '@/types/billing';
import { useAuthStore } from '@/store/authStore';
import { PLAN_FEATURES_MAP, TIER_ORDER, getRequiredTier } from '@/lib/planFeatures';

interface EntitlementContextValue {
  tier: PlanTier;
  hasFeature: (key: FeatureKey) => boolean;
  getRequiredTierForFeature: (key: FeatureKey) => PlanTier;
  needsUpgrade: (key: FeatureKey) => boolean;
}

const EntitlementContext = createContext<EntitlementContextValue | null>(null);

export function EntitlementProvider({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const tier: PlanTier = (user?.organization?.plan as PlanTier) || 'free';

  const value = useMemo<EntitlementContextValue>(() => {
    const features = PLAN_FEATURES_MAP[tier];
    return {
      tier,
      hasFeature: (key: FeatureKey) => features[key] === true,
      getRequiredTierForFeature: (key: FeatureKey) => getRequiredTier(key),
      needsUpgrade: (key: FeatureKey) => {
        const required = getRequiredTier(key);
        return TIER_ORDER[tier] < TIER_ORDER[required];
      },
    };
  }, [tier]);

  return (
    <EntitlementContext.Provider value={value}>
      {children}
    </EntitlementContext.Provider>
  );
}

export function useEntitlementContext() {
  const ctx = useContext(EntitlementContext);
  if (!ctx) throw new Error('useEntitlementContext must be used within EntitlementProvider');
  return ctx;
}
