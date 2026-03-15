import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/pages/auth/LoginPage';
import { SignupPage } from '@/pages/auth/SignupPage';
import { OAuthCallbackPage } from '@/pages/auth/OAuthCallbackPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { IdentityProvidersPage } from '@/pages/identity-providers/IdentityProvidersPage';
import { ConnectorsPage } from '@/pages/connectors/ConnectorsPage';
import { PipelinesPage } from '@/pages/pipelines/PipelinesPage';
import { DataCatalogPage } from '@/pages/data-catalog/DataCatalogPage';
import { DataCatalogDetailPage } from '@/pages/data-catalog/DataCatalogDetailPage';
import { PolicyStudioPage } from '@/pages/policy-studio/PolicyStudioPage';
import { AccessSimulatorPage } from '@/pages/access-simulator/AccessSimulatorPage';
import { AuditLogPage } from '@/pages/audit-log/AuditLogPage';
import { UsageBillingPage } from '@/pages/usage-billing/UsageBillingPage';
import { SettingsPage } from '@/pages/settings/SettingsPage';
import { SecuredRetrievalsPage } from '@/pages/secured-retrievals/SecuredRetrievalsPage';

export function Router() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />

        {/* Protected routes with AppShell layout */}
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/identity-providers" element={<IdentityProvidersPage />} />
          <Route path="/connectors" element={<ConnectorsPage />} />
          <Route path="/pipelines" element={<PipelinesPage />} />
          <Route path="/data-catalog" element={<DataCatalogPage />} />
          <Route path="/data-catalog/:id" element={<DataCatalogDetailPage />} />
          <Route path="/policy-studio" element={<PolicyStudioPage />} />
          <Route path="/access-simulator" element={<AccessSimulatorPage />} />
          <Route path="/secured-retrievals" element={<SecuredRetrievalsPage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
          <Route path="/usage-billing" element={<UsageBillingPage />} />
          <Route path="/organization" element={<Navigate to="/settings" replace />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
