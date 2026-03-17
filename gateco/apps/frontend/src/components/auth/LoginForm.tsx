import * as React from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { OAuthButtons } from './OAuthButtons';


interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface LoginFormProps {
  onSubmit: (data: LoginFormData) => Promise<void>;
  error?: string;
  isLoading?: boolean;
  onClearError?: () => void;
}

export function LoginForm({ onSubmit, error, isLoading, onClearError }: LoginFormProps) {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [rememberMe, setRememberMe] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [validationErrors, setValidationErrors] = React.useState<{ email?: string; password?: string }>({});
  const [blurredFields, setBlurredFields] = React.useState<Set<string>>(new Set());
  const [showForgotMessage, setShowForgotMessage] = React.useState(false);

  const submitting = isSubmitting || isLoading;

  const validateEmail = (value: string): string | undefined => {
    if (!value.trim()) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) return 'Please enter a valid email address';
    return undefined;
  };

  const validatePassword = (value: string): string | undefined => {
    if (!value) return 'Password is required';
    return undefined;
  };

  const handleBlur = (field: 'email' | 'password') => {
    setBlurredFields((prev) => new Set(prev).add(field));
    if (field === 'email') {
      const err = validateEmail(email);
      setValidationErrors((prev) => ({ ...prev, email: err }));
    }
  };

  const handleInputChange = (field: 'email' | 'password', value: string) => {
    if (field === 'email') {
      setEmail(value);
      if (blurredFields.has('email')) {
        setValidationErrors((prev) => ({ ...prev, email: validateEmail(value) }));
      }
    } else {
      setPassword(value);
      if (blurredFields.has('password')) {
        setValidationErrors((prev) => ({ ...prev, password: validatePassword(value) }));
      }
    }
    onClearError?.();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    const emailErr = validateEmail(email);
    const passwordErr = validatePassword(password);
    setValidationErrors({ email: emailErr, password: passwordErr });
    setBlurredFields(new Set(['email', 'password']));

    if (emailErr || passwordErr) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        email: email.trim().toLowerCase(),
        password,
        rememberMe,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      <h2 role="heading" className="text-2xl font-bold text-center text-foreground">
        Log in
      </h2>

      {error && (
        <div role="alert" aria-live="polite" className="alert-error rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <form role="form" onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <label htmlFor="login-email" className="text-sm font-medium text-foreground">
            Email
          </label>
          <Input
            id="login-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            disabled={submitting}
            placeholder="you@example.com"
          />
          {validationErrors.email && (
            <p className="text-sm text-destructive">{validationErrors.email}</p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="login-password" className="text-sm font-medium text-foreground">
            Password
          </label>
          <div className="relative">
            <Input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              disabled={submitting}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Toggle password visibility"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {validationErrors.password && (
            <p className="text-sm text-destructive">{validationErrors.password}</p>
          )}
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              role="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={submitting}
              className="rounded border-input"
              aria-label="Remember me"
            />
            Remember me
          </label>
          <button
            type="button"
            onClick={() => setShowForgotMessage((prev) => !prev)}
            className="text-sm text-primary-600 hover:text-primary-500 hover:underline"
          >
            Forgot password?
          </button>
        </div>

        {showForgotMessage && (
          <div className="flex items-start gap-2 rounded-md bg-muted p-3 text-sm text-muted-foreground">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <span>Contact your organization admin to reset your password.</span>
          </div>
        )}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" data-testid="loading-spinner" />
              Logging in...
            </>
          ) : (
            'Log in'
          )}
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
        </div>
      </div>

      <OAuthButtons disabled={submitting} isLoading={isLoading} />

      <p className="text-center text-sm text-muted-foreground">
        Don't have an account?{' '}
        <Link to="/signup" className="text-primary-600 hover:text-primary-500 hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
