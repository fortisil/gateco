import * as React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface GitHubOAuthButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onClick'> {
  isLoading?: boolean;
  /**
   * Callback invoked when OAuth authentication fails.
   * Named 'onAuthError' (not 'onError') to avoid conflict with native HTML button onError event handler.
   */
  onAuthError?: (error: Error) => void;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
}

const GitHubIcon = () => (
  <svg
    className="h-5 w-5"
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
    />
  </svg>
);

const Spinner = () => (
  <svg
    className="h-5 w-5 animate-spin"
    viewBox="0 0 24 24"
    fill="none"
    role="status"
    data-testid="spinner"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

const GitHubOAuthButton = React.forwardRef<HTMLButtonElement, GitHubOAuthButtonProps>(
  ({ className, children, isLoading, disabled, onClick, onAuthError, ...props }, ref) => {
    const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
      if (onClick) {
        onClick(e);
      }

      if (!e.defaultPrevented) {
        try {
          window.location.href = '/api/auth/github';
        } catch (error) {
          onAuthError?.(error as Error);
        }
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === 'Enter' || e.key === ' ') {
        onClick?.(e as unknown as React.MouseEvent<HTMLButtonElement>);
      }
    };

    return (
      <Button
        ref={ref}
        variant="outline"
        className={cn('w-full gap-2', className)}
        disabled={disabled || isLoading}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading ? (
          <Spinner />
        ) : (
          <span data-testid="github-icon">
            <GitHubIcon />
          </span>
        )}
        {children || 'Continue with GitHub'}
      </Button>
    );
  }
);
GitHubOAuthButton.displayName = 'GitHubOAuthButton';

export { GitHubOAuthButton };