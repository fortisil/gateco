import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { updateMe } from '@/api/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

type Tab = 'profile' | 'organization';

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [name, setName] = useState(user?.name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const isDirty = name !== (user?.name || '');

  async function handleSave() {
    if (!isDirty || isSaving) return;
    setIsSaving(true);
    setSaveError('');
    setSaveSuccess(false);
    try {
      const updated = await updateMe({ name: name.trim() });
      setUser(updated);
      setSaveSuccess(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save changes');
    } finally {
      setIsSaving(false);
    }
  }

  function handleNameChange(value: string) {
    setName(value);
    setSaveSuccess(false);
  }

  const tabs: { value: Tab; label: string }[] = [
    { value: 'profile', label: 'Profile' },
    { value: 'organization', label: 'Organization' },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Tab bar */}
      <div className="flex gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === tab.value
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile tab */}
      {activeTab === 'profile' && (
        <div className="rounded-lg border p-6 space-y-4">
          <h2 className="text-lg font-semibold">Profile</h2>
          <div className="flex items-center gap-4 pb-4 border-b">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl font-semibold">
              {(user?.name || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold">{user?.name}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <Badge variant="outline" className="mt-1 capitalize">{user?.role?.replace('_', ' ')}</Badge>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Display Name</label>
            <Input value={name} onChange={(e) => handleNameChange(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Email</label>
            <Input value={user?.email || ''} disabled />
            <p className="text-xs text-muted-foreground">Contact your organization admin to change your email.</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Role</label>
            <Input value={user?.role?.replace('_', ' ') || ''} disabled className="capitalize" />
          </div>
          {saveError && (
            <p className="text-sm text-destructive bg-destructive/10 rounded-md p-2">{saveError}</p>
          )}
          {saveSuccess && (
            <p className="text-sm text-emerald-600 bg-emerald-50 dark:bg-emerald-900/10 rounded-md p-2">Changes saved successfully.</p>
          )}
          <Button onClick={handleSave} disabled={!isDirty || isSaving}>
            {isSaving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      )}

      {/* Organization tab */}
      {activeTab === 'organization' && (
        <div className="space-y-4">
          <div className="rounded-lg border p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Organization Details</h2>
              <Badge variant="outline" className="capitalize">{user?.organization?.plan} plan</Badge>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Organization Name</label>
                <Input value={user?.organization?.name || ''} disabled />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Slug</label>
                <Input value={user?.organization?.slug || ''} disabled className="font-mono" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Organization ID</label>
              <Input value={user?.organization?.id || ''} disabled className="font-mono text-xs" />
            </div>
          </div>

          <div className="rounded-lg border p-6 space-y-4">
            <h2 className="text-lg font-semibold">Your Membership</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground text-xs">Your Role</p>
                <p className="font-medium capitalize">{user?.role?.replace('_', ' ')}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Member Since</p>
                <p className="font-medium">{user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : '—'}</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border p-6 space-y-3">
            <h2 className="text-lg font-semibold">Plan</h2>
            <p className="text-sm text-muted-foreground">
              Your organization is on the <span className="font-medium capitalize text-foreground">{user?.organization?.plan}</span> plan.
            </p>
            <Button variant="outline" onClick={() => window.location.href = '/usage-billing'}>
              Manage Plan & Billing
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
