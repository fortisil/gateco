import { useState } from 'react';
import { usePlans, useUsage, useInvoices, useCheckout, useBillingPortal, useSubscription } from '@/hooks/useBilling';
import { PlanCard } from '@/components/billing/PlanCard';
import { UsageMeter } from '@/components/billing/UsageMeter';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import type { PlanTier } from '@/types/billing';

export function UsageBillingPage() {
  const user = useAuthStore((s) => s.user);
  const currentTier = (user?.organization?.plan as PlanTier) || 'free';
  const [interval, setInterval] = useState<'monthly' | 'yearly'>('monthly');
  const { data: plansData, isLoading: plansLoading } = usePlans();
  const { data: usageData, isLoading: usageLoading } = useUsage();
  const { data: invoicesData } = useInvoices();
  const { isActive: hasActiveSubscription } = useSubscription();
  const checkout = useCheckout();
  const billingPortal = useBillingPortal();

  const handleSelectPlan = async (planId: string, interval: 'monthly' | 'yearly') => {
    const result = await checkout.mutateAsync({ plan_id: planId, billing_period: interval });
    window.location.href = result.checkout_url;
  };

  const handleManageBilling = async () => {
    const result = await billingPortal.mutateAsync({});
    window.location.href = result.portal_url;
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Usage & Billing</h1>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Current Usage</h2>
        {usageLoading ? (
          <div className="space-y-3"><Skeleton className="h-8 w-full" /><Skeleton className="h-8 w-full" /></div>
        ) : usageData ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border p-4">
              <UsageMeter used={usageData.secured_retrievals.used} limit={usageData.secured_retrievals.limit} label="Secured Retrievals" />
            </div>
            <div className="rounded-lg border p-4">
              <UsageMeter used={usageData.connectors.used} limit={usageData.connectors.limit} label="Connectors" />
            </div>
          </div>
        ) : null}
      </div>

      {hasActiveSubscription && (
        <div>
          <Button variant="outline" onClick={handleManageBilling} disabled={billingPortal.isPending}>
            Manage Subscription
          </Button>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Plans</h2>
          <div className="flex gap-2">
            <Button variant={interval === 'monthly' ? 'default' : 'outline'} size="sm" onClick={() => setInterval('monthly')}>Monthly</Button>
            <Button variant={interval === 'yearly' ? 'default' : 'outline'} size="sm" onClick={() => setInterval('yearly')}>Yearly</Button>
          </div>
        </div>
        {plansLoading ? (
          <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-64" />)}</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {plansData?.plans?.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                interval={interval}
                isCurrentPlan={plan.tier === currentTier}
                currentPlan={currentTier}
                isRecommended={plan.tier === 'pro'}
                isLoading={checkout.isPending}
                onSelect={handleSelectPlan}
                showSavings
              />
            ))}
          </div>
        )}
      </div>

      {invoicesData?.data && invoicesData.data.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Invoices</h2>
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="p-3 text-left">Date</th><th className="p-3 text-left">Amount</th><th className="p-3 text-left">Status</th><th className="p-3 text-right">PDF</th></tr></thead>
              <tbody>
                {invoicesData.data.map((inv) => (
                  <tr key={inv.id} className="border-b last:border-0">
                    <td className="p-3">{new Date(inv.created_at).toLocaleDateString()}</td>
                    <td className="p-3">${(inv.amount_cents / 100).toFixed(2)}</td>
                    <td className="p-3"><Badge variant="outline" className="capitalize">{inv.status}</Badge></td>
                    <td className="p-3 text-right"><a href={inv.pdf_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Download</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
