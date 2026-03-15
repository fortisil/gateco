import { useAuthStore } from '@/store/authStore';
import { Badge } from '@/components/ui/badge';

export function OrganizationPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Organization</h1>
      <div className="rounded-lg border p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{user?.organization?.name}</h2>
          <Badge variant="outline" className="capitalize">{user?.organization?.plan}</Badge>
        </div>
        <div className="text-sm text-muted-foreground">
          <p>Slug: {user?.organization?.slug}</p>
          <p>Your role: <span className="capitalize">{user?.role}</span></p>
        </div>
      </div>
    </div>
  );
}
