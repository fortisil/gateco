import type { Plan, PlanLimits, PlanTier, FeatureKey } from '@/types/billing';
import { PLAN_FEATURES_MAP, TIER_ORDER, getRequiredTier } from '@/lib/planFeatures';

interface UseEntitlementsInput {
  plan: Plan;
  usage?: {
    connectors: { used: number; limit: number | null };
    secured_retrievals: { used: number; limit: number | null };
  };
}

export function useEntitlements({ plan, usage }: UseEntitlementsInput) {
  const hasFeature = (key: FeatureKey): boolean => {
    return plan.features[key] === true;
  };

  const getLimit = (key: keyof PlanLimits): number | null => {
    const val = plan.limits[key];
    return typeof val === 'number' ? val : null;
  };

  const isUnlimited = (key: keyof PlanLimits): boolean => {
    const val = plan.limits[key];
    return val === null || val === Infinity;
  };

  const getRemaining = (key: 'connectors' | 'secured_retrievals'): number | null => {
    if (!usage) return null;
    const metric = usage[key];
    if (metric.limit === null || metric.limit === Infinity) return Infinity;
    return Math.max(0, metric.limit - metric.used);
  };

  const getUsagePercentage = (key: 'connectors' | 'secured_retrievals'): number => {
    if (!usage) return 0;
    const metric = usage[key];
    if (metric.limit === null || metric.limit === Infinity || metric.limit === 0) return 0;
    return (metric.used / metric.limit) * 100;
  };

  const canPerformRetrieval = (): boolean => {
    if (!usage) return true;
    const { used, limit } = usage.secured_retrievals;
    if (limit === null || limit === Infinity) return true;
    return used < limit;
  };

  const isNearLimit = (key: 'connectors' | 'secured_retrievals'): boolean => {
    const pct = getUsagePercentage(key);
    return pct >= 70 && pct < 100;
  };

  const isAtLimit = (key: 'connectors' | 'secured_retrievals'): boolean => {
    return getUsagePercentage(key) >= 100;
  };

  const getUpgradeSuggestion = (key: FeatureKey | 'connectors' | 'secured_retrievals'): { recommendedPlan: PlanTier; benefit: string } | null => {
    if (plan.tier === 'enterprise') return null;

    if (key === 'connectors') {
      if (plan.tier === 'free') return { recommendedPlan: 'pro', benefit: 'Multiple vector DB connectors' };
      return null;
    }
    if (key === 'secured_retrievals') {
      if (plan.tier === 'free') return { recommendedPlan: 'pro', benefit: '10,000 secured retrievals/month' };
      return { recommendedPlan: 'enterprise', benefit: 'Unlimited secured retrievals' };
    }

    const requiredTier = getRequiredTier(key as FeatureKey);
    if (TIER_ORDER[plan.tier] >= TIER_ORDER[requiredTier]) return null;
    return { recommendedPlan: requiredTier, benefit: `Access to ${(key as string).replace(/_/g, ' ')}` };
  };

  const comparePlans = (from: PlanTier, to: PlanTier): { gains: FeatureKey[] } => {
    const fromFeatures = PLAN_FEATURES_MAP[from];
    const toFeatures = PLAN_FEATURES_MAP[to];
    const gains: FeatureKey[] = [];
    for (const key of Object.keys(fromFeatures) as FeatureKey[]) {
      if (!fromFeatures[key] && toFeatures[key]) {
        gains.push(key);
      }
    }
    return { gains };
  };

  return {
    hasFeature,
    getLimit,
    isUnlimited,
    getRemaining,
    getUsagePercentage,
    canPerformRetrieval,
    isNearLimit,
    isAtLimit,
    getUpgradeSuggestion,
    comparePlans,
  };
}
