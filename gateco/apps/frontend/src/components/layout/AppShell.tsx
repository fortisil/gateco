import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/lib/utils';

export function AppShell() {
  const { sidebarOpen } = useUIStore();
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.add('dark');
    return () => {
      document.documentElement.classList.remove('dark');
    };
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <div className={cn('transition-all duration-200', sidebarOpen ? 'ml-64' : 'ml-16')}>
        <TopNav />
        <main className="p-6">
          <ErrorBoundary key={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
