import * as React from 'react';
import { cn } from '@/lib/utils';
import { GoogleOAuthButton } from './GoogleOAuthButton';
import { GitHubOAuthButton } from './GitHubOAuthButton';

interface OAuthButtonsProps {
  className?: string;
  disabled?: boolean;
  isLoading?: boolean;
  initialError?: string;
}

const OAuthButtons: React.FC<OAuthButtonsProps> = ({
  className,
  disabled,
  isLoading,
  initialError,
}) => {
  const [error, setError] = React.useState<string | null>(initialError || null);
  const [activeProvider, setActiveProvider] = React.useState<string | null>(null);

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errorParam = params.get('error');
    const errorDescription = params.get('error_description');

    if (errorParam) {
      setError(errorDescription || errorParam);
    }
  }, []);

  const handleOAuthClick = (provider: string) => {
    setError(null);
    setActiveProvider(provider);
  };

  const handleError = (err: Error) => {
    setError(err.message);
    setActiveProvider(null);
  };

  return (
    <div className={cn('flex flex-col gap-4', className)}>
      {error && (
        <div
          role="alert"
          className="rounded-md bg-destructive/10 p-3 text-sm text-destructive"
        >
          {error}
        </div>
      )}

      <GoogleOAuthButton
        disabled={disabled || isLoading}
        isLoading={isLoading || activeProvider === 'google'}
        onClick={() => handleOAuthClick('google')}
        onError={handleError}
      />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>

      <GitHubOAuthButton
        disabled={disabled || isLoading}
        isLoading={isLoading || activeProvider === 'github'}
        onClick={() => handleOAuthClick('github')}
        onAuthError={handleError}
      />
    </div>
  );
};

export { OAuthButtons };
