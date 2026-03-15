import * as React from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface SignupFormData {
  name: string;
  email: string;
  password: string;
  organization_name: string;
}

interface SignupFormProps {
  onSubmit: (data: SignupFormData) => Promise<void>;
  error?: string;
}

function getPasswordStrength(password: string): { label: string; score: number } {
  if (!password) return { label: '', score: 0 };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { label: 'Weak', score: 1 };
  if (score <= 2) return { label: 'Fair', score: 2 };
  if (score <= 3) return { label: 'Good', score: 3 };
  return { label: 'Strong', score: 4 };
}

export function SignupForm({ onSubmit, error }: SignupFormProps) {
  const [name, setName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [orgName, setOrgName] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const strength = getPasswordStrength(password);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) newErrors.name = 'Name is required';
    if (!email.trim()) newErrors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) newErrors.email = 'Invalid email address';
    if (!password) newErrors.password = 'Password is required';
    else if (password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (password !== confirmPassword) newErrors.confirmPassword = "Passwords don't match";
    if (!orgName.trim()) newErrors.organization = 'Organization name is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting || !validate()) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        organization_name: orgName.trim(),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      <h2 className="text-2xl font-bold text-center">Create your account</h2>

      {error && (
        <div role="alert" className="alert-error rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <label htmlFor="signup-name" className="text-sm font-medium">Name</label>
          <Input id="signup-name" value={name} onChange={(e) => setName(e.target.value)} disabled={isSubmitting} />
          {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-email" className="text-sm font-medium">Email</label>
          <Input id="signup-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={isSubmitting} />
          {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-password" className="text-sm font-medium">Password</label>
          <Input id="signup-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={isSubmitting} />
          {password && (
            <div data-testid="password-strength" className="text-sm">
              <span className={strength.score <= 1 ? 'text-red-400' : strength.score <= 2 ? 'text-amber-400' : 'text-emerald-400'}>
                {strength.label}
              </span>
            </div>
          )}
          {errors.password && <p className="text-sm text-destructive">{errors.password}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-confirm-password" className="text-sm font-medium">Confirm password</label>
          <Input id="signup-confirm-password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={isSubmitting} />
          {errors.confirmPassword && <p className="text-sm text-destructive">{errors.confirmPassword}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-org" className="text-sm font-medium">Organization name</label>
          <Input id="signup-org" value={orgName} onChange={(e) => setOrgName(e.target.value)} disabled={isSubmitting} />
          {errors.organization && <p className="text-sm text-destructive">{errors.organization}</p>}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating account...
            </>
          ) : (
            'Sign up'
          )}
        </Button>
      </form>
    </div>
  );
}
