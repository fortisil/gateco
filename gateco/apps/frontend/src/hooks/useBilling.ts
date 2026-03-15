import { useQuery, useMutation } from '@tanstack/react-query';
import * as billingApi from '@/api/billing';
import { queryKeys } from '@/api/queryKeys';
import type { CheckoutRequest, BillingPortalRequest } from '@/types/billing';

export function usePlans() {
  return useQuery({
    queryKey: queryKeys.billing.plans,
    queryFn: billingApi.getPlans,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCurrentPlan() {
  const { data, isLoading } = usePlans();
  // In a real app, this would come from the user's org plan
  // For now, we derive from the plans list + auth store
  return {
    plan: data?.plans?.[0] ?? null,
    entitlements: data?.plans?.[0]?.features ?? null,
    isLoading,
  };
}

export function useUsage() {
  const query = useQuery({
    queryKey: queryKeys.billing.usage,
    queryFn: billingApi.getUsage,
    staleTime: 60 * 1000,
  });

  const getUsagePercentage = (key: 'secured_retrievals'): number => {
    if (!query.data) return 0;
    const metric = query.data[key];
    if (!metric.limit || metric.limit === 0) return 0;
    return (metric.used / metric.limit) * 100;
  };

  return { ...query, getUsagePercentage };
}

export function useInvoices(params?: { page?: number; perPage?: number }) {
  return useQuery({
    queryKey: queryKeys.billing.invoices(params),
    queryFn: () => billingApi.getInvoices(params),
  });
}

export function useCheckout() {
  return useMutation({
    mutationFn: (data: CheckoutRequest) => billingApi.startCheckout(data),
  });
}

export function useBillingPortal() {
  return useMutation({
    mutationFn: (data?: BillingPortalRequest) => billingApi.createBillingPortal(data),
  });
}

export function useSubscription() {
  const query = useQuery({
    queryKey: queryKeys.billing.subscription,
    queryFn: billingApi.getSubscription,
  });

  return {
    ...query,
    isActive: query.data?.status === 'active',
  };
}
