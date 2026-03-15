import { Check, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Plan, PlanTier } from '@/types/billing';

interface PlanCardProps {
  plan: Plan;
  interval: 'monthly' | 'yearly';
  isCurrentPlan?: boolean;
  currentPlan?: PlanTier;
  isRecommended?: boolean;
  isLoading?: boolean;
  onSelect?: (planId: string, interval: 'monthly' | 'yearly') => void;
  className?: string;
  showSavings?: boolean;
}

const TIER_ORDER: Record<PlanTier, number> = { free: 0, pro: 1, enterprise: 2 };

const FEATURE_LABELS: Record<string, string> = {
  rbac_policies: 'RBAC Policies',
  abac_policies: 'ABAC Policies',
  policy_studio: 'Policy Studio',
  policy_versioning: 'Policy Versioning',
  access_simulator: 'Access Simulator',
  vendor_iam: 'Vendor IAM Providers',
  multi_connector: 'Multiple Connectors',
  advanced_analytics: 'Advanced Analytics',
  audit_export: 'Audit Export',
  siem_export: 'SIEM Integration',
  content_ref_mode: 'Content Reference Mode',
  custom_kms: 'Custom KMS',
  sso_scim: 'SSO & SCIM',
  private_data_plane: 'Private Data Plane',
};

const LIMIT_LABELS: Record<string, (v: number | null) => string> = {
  secured_retrievals: (v) => v === null ? 'Unlimited retrievals' : `${v.toLocaleString()} retrievals/mo`,
  connectors: (v) => v === null ? 'Unlimited connectors' : `${v} connector${v === 1 ? '' : 's'}`,
  identity_providers: (v) => v === null ? 'Unlimited identity providers' : `${v} identity provider${v === 1 ? '' : 's'}`,
  policies: (v) => v === null ? 'Unlimited policies' : `${v} policies`,
  team_members: (v) => v === null ? 'Unlimited team members' : `${v} team member${v === 1 ? '' : 's'}`,
};

export function PlanCard({
  plan, interval, isCurrentPlan, currentPlan, isRecommended,
  isLoading, onSelect, className, showSavings,
}: PlanCardProps) {
  const priceCents = interval === 'monthly' ? plan.price_monthly_cents : plan.price_yearly_cents;
  const priceDollars = Math.floor(priceCents / 100);
  const period = interval === 'monthly' ? '/month' : '/year';

  let buttonLabel = 'Subscribe';
  let buttonDisabled = false;
  if (isCurrentPlan) {
    buttonLabel = 'Current Plan';
    buttonDisabled = true;
  } else if (currentPlan) {
    buttonLabel = TIER_ORDER[plan.tier] > TIER_ORDER[currentPlan] ? 'Upgrade' : 'Downgrade';
  }

  const yearlySavings = showSavings && interval === 'yearly'
    ? Math.round(((plan.price_monthly_cents * 12 - plan.price_yearly_cents) / (plan.price_monthly_cents * 12)) * 100)
    : 0;

  return (
    <div className={cn(
      'relative rounded-lg border p-6 flex flex-col',
      isRecommended && 'recommended border-primary ring-2 ring-primary',
      className,
    )}>
      {isRecommended && (
        <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary">Recommended</Badge>
      )}

      <h3 role="heading" className="text-lg font-bold">{plan.name}</h3>

      <div className="mt-2">
        <span className="text-3xl font-bold">${priceDollars}</span>
        <span className="text-muted-foreground">{period}</span>
      </div>

      {yearlySavings > 0 && (
        <Badge variant="secondary" className="mt-2 w-fit">Save {yearlySavings}%</Badge>
      )}

      {isCurrentPlan && (
        <Badge variant="outline" className="mt-2 w-fit">Current Plan</Badge>
      )}

      <ul role="list" className="mt-6 space-y-2 flex-1">
        {Object.entries(plan.limits).map(([key, value]) => {
          const formatter = LIMIT_LABELS[key];
          if (!formatter) return null;
          return (
            <li key={key} className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>{formatter(value as number | null)}</span>
            </li>
          );
        })}
        {Object.entries(plan.features).map(([key, enabled]) => (
          <li key={key} className="flex items-center gap-2 text-sm">
            {enabled ? (
              <Check className="h-4 w-4 text-emerald-400 shrink-0" />
            ) : (
              <X className="h-4 w-4 text-muted-foreground shrink-0" />
            )}
            <span className={!enabled ? 'text-muted-foreground' : ''}>
              {FEATURE_LABELS[key] || key.replace(/_/g, ' ')}
            </span>
          </li>
        ))}
      </ul>

      <Button
        className="mt-6 w-full"
        disabled={buttonDisabled || isLoading}
        aria-busy={isLoading || undefined}
        onClick={() => onSelect?.(plan.id, interval)}
      >
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : buttonLabel}
      </Button>
    </div>
  );
}
