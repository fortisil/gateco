import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [error, setError] = useState<string>();
  const [testLoading, setTestLoading] = useState(false);

  const redirect = searchParams.get('redirect') || '/dashboard';

  const handleSubmit = async (data: { email: string; password: string; rememberMe?: boolean }) => {
    try {
      await login(data);
      navigate(redirect, { replace: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Invalid email or password');
    }
  };

  const handleTestLogin = async () => {
    setTestLoading(true);
    setError(undefined);
    try {
      await login({ email: 'admin@acmecorp.com', password: 'password123' });
      navigate(redirect, { replace: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Test login failed');
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="text-3xl font-bold text-primary-600">gateco</Link>
        </div>
        <div className="rounded-lg border border-border bg-card p-8 shadow-sm">
          <LoginForm onSubmit={handleSubmit} error={error} onClearError={() => setError(undefined)} />
        </div>
        <div className="mt-4">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleTestLogin}
            disabled={testLoading}
          >
            {testLoading ? 'Signing in...' : 'Login as Test User'}
          </Button>
          <p className="text-xs text-center text-muted-foreground mt-2">
            admin@acmecorp.com &middot; Pro plan &middot; Org Admin
          </p>
        </div>
      </div>
    </div>
  );
}
