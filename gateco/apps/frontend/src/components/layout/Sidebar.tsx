import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, KeyRound, Database, ArrowRightLeft, FileText,
  Shield, FlaskConical, ClipboardList, BarChart3, Settings,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useAuthStore } from '@/store/authStore';
import { cn } from '@/lib/utils';
import { PlanBadge } from '@/components/billing/PlanBadge';
import type { PlanTier } from '@/types/billing';

const primaryNavItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/identity-providers', label: 'Identity Providers', icon: KeyRound },
  { to: '/connectors', label: 'Vector DB Connectors', icon: Database },
  { to: '/pipelines', label: 'Ingestion Pipelines', icon: ArrowRightLeft },
  { to: '/data-catalog', label: 'Data Catalog', icon: FileText },
  { to: '/policy-studio', label: 'Policy Studio', icon: Shield },
  { to: '/access-simulator', label: 'Access Simulator', icon: FlaskConical },
  { to: '/audit-log', label: 'Audit Logs', icon: ClipboardList },
  { to: '/usage-billing', label: 'Usage & Billing', icon: BarChart3 },
];

const secondaryNavItems = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

function NavItem({ to, label, icon: Icon, sidebarOpen }: { to: string; label: string; icon: React.ComponentType<{ className?: string }>; sidebarOpen: boolean }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-4 py-2 text-sm transition-colors',
          isActive
            ? 'bg-primary/10 text-primary font-medium'
            : 'text-muted-foreground hover:bg-accent hover:text-foreground',
          !sidebarOpen && 'justify-center px-0'
        )
      }
      title={!sidebarOpen ? label : undefined}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {sidebarOpen && <span>{label}</span>}
    </NavLink>
  );
}

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const user = useAuthStore((s) => s.user);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full bg-card border-r z-30 transition-all duration-200 flex flex-col',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      <div className="flex items-center gap-3 px-4 h-14 border-b">
        {sidebarOpen && (
          <>
            <span className="font-bold text-lg text-primary">gateco</span>
            <PlanBadge tier={(user?.organization?.plan || 'free') as PlanTier} className="text-xs" />
          </>
        )}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className={cn('p-1 rounded-md hover:bg-accent text-muted-foreground', !sidebarOpen && 'mx-auto')}
          aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
      </div>

      {sidebarOpen && user?.organization && (
        <div className="px-4 py-3 border-b">
          <p className="text-sm font-medium truncate">{user.organization.name}</p>
        </div>
      )}

      <nav className="flex-1 py-2 overflow-y-auto">
        {primaryNavItems.map((item) => (
          <NavItem key={item.to} {...item} sidebarOpen={sidebarOpen} />
        ))}
      </nav>

      <div className="border-t py-2">
        {secondaryNavItems.map((item) => (
          <NavItem key={item.to} {...item} sidebarOpen={sidebarOpen} />
        ))}
      </div>
    </aside>
  );
}
