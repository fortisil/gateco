/**
 * Tests for OAuth authentication buttons.
 *
 * Tests the Google and GitHub OAuth button components including
 * click handling, loading states, and accessibility.
 */

import { render, screen, fireEvent, waitFor } from '../../utils/test-utils';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { OAuthButtons } from '@/components/auth/OAuthButtons';
import { GoogleOAuthButton } from '@/components/auth/GoogleOAuthButton';
import { GitHubOAuthButton } from '@/components/auth/GitHubOAuthButton';

// Mock window.location for redirect testing
const mockLocation = {
  href: '',
  assign: vi.fn(),
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('OAuthButtons', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
  });

  describe('Rendering', () => {
    it('renders both Google and GitHub buttons', () => {
      render(<OAuthButtons />);

      expect(
        screen.getByRole('button', { name: /continue with google/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /continue with github/i })
      ).toBeInTheDocument();
    });

    it('renders divider text between buttons', () => {
      render(<OAuthButtons />);

      expect(screen.getByText(/or continue with/i)).toBeInTheDocument();
    });

    it('applies custom className when provided', () => {
      const { container } = render(<OAuthButtons className="custom-class" />);

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Disabled State', () => {
    it('disables all buttons when disabled prop is true', () => {
      render(<OAuthButtons disabled />);

      expect(
        screen.getByRole('button', { name: /continue with google/i })
      ).toBeDisabled();
      expect(
        screen.getByRole('button', { name: /continue with github/i })
      ).toBeDisabled();
    });

    it('disables buttons during loading', () => {
      render(<OAuthButtons isLoading />);

      expect(
        screen.getByRole('button', { name: /continue with google/i })
      ).toBeDisabled();
      expect(
        screen.getByRole('button', { name: /continue with github/i })
      ).toBeDisabled();
    });
  });
});

describe('GoogleOAuthButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
  });

  describe('Rendering', () => {
    it('renders Google button with icon', () => {
      render(<GoogleOAuthButton />);

      const button = screen.getByRole('button', { name: /continue with google/i });
      expect(button).toBeInTheDocument();

      // Check for Google icon (SVG)
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders custom text when provided', () => {
      render(<GoogleOAuthButton>Sign in with Google</GoogleOAuthButton>);

      expect(
        screen.getByRole('button', { name: /sign in with google/i })
      ).toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      render(<GoogleOAuthButton onClick={handleClick} />);

      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('initiates OAuth flow on click', async () => {
      render(<GoogleOAuthButton />);

      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

      await waitFor(() => {
        // Should redirect to Google OAuth or call API
        expect(mockLocation.href).toContain('google') ||
          expect(mockLocation.assign).toHaveBeenCalled();
      });
    });

    it('does not trigger when disabled', () => {
      const handleClick = vi.fn();
      render(<GoogleOAuthButton onClick={handleClick} disabled />);

      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      render(<GoogleOAuthButton isLoading />);

      expect(screen.getByRole('button')).toBeDisabled();
      // Check for spinner element
      expect(screen.getByRole('status') || screen.getByTestId('spinner')).toBeInTheDocument();
    });

    it('hides icon when loading', () => {
      render(<GoogleOAuthButton isLoading />);

      const button = screen.getByRole('button');
      // Google icon should be hidden or replaced with spinner
      expect(button.querySelector('[data-testid="google-icon"]')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible name', () => {
      render(<GoogleOAuthButton />);

      expect(
        screen.getByRole('button', { name: /google/i })
      ).toBeInTheDocument();
    });

    it('is keyboard focusable', () => {
      render(<GoogleOAuthButton />);

      const button = screen.getByRole('button');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('can be activated with Enter key', () => {
      const handleClick = vi.fn();
      render(<GoogleOAuthButton onClick={handleClick} />);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleClick).toHaveBeenCalled();
    });

    it('can be activated with Space key', () => {
      const handleClick = vi.fn();
      render(<GoogleOAuthButton onClick={handleClick} />);

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: ' ' });

      expect(handleClick).toHaveBeenCalled();
    });
  });
});

describe('GitHubOAuthButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
  });

  describe('Rendering', () => {
    it('renders GitHub button with icon', () => {
      render(<GitHubOAuthButton />);

      const button = screen.getByRole('button', { name: /continue with github/i });
      expect(button).toBeInTheDocument();

      // Check for GitHub icon (SVG)
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('renders custom text when provided', () => {
      render(<GitHubOAuthButton>Sign in with GitHub</GitHubOAuthButton>);

      expect(
        screen.getByRole('button', { name: /sign in with github/i })
      ).toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      render(<GitHubOAuthButton onClick={handleClick} />);

      fireEvent.click(screen.getByRole('button', { name: /continue with github/i }));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('initiates OAuth flow on click', async () => {
      render(<GitHubOAuthButton />);

      fireEvent.click(screen.getByRole('button', { name: /continue with github/i }));

      await waitFor(() => {
        // Should redirect to GitHub OAuth or call API
        expect(mockLocation.href).toContain('github') ||
          expect(mockLocation.assign).toHaveBeenCalled();
      });
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      render(<GitHubOAuthButton isLoading />);

      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it.skip('calls onError when OAuth fails', async () => {
      // TODO: This test requires implementing an API-based OAuth flow
      // rather than direct redirect. Currently the component redirects
      // via window.location.href which doesn't throw errors that can be caught.
      const handleError = vi.fn();

      render(<GitHubOAuthButton onAuthError={handleError} />);

      fireEvent.click(screen.getByRole('button', { name: /continue with github/i }));

      await waitFor(() => {
        expect(handleError).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('has accessible name', () => {
      render(<GitHubOAuthButton />);

      expect(
        screen.getByRole('button', { name: /github/i })
      ).toBeInTheDocument();
    });

    it('announces loading state to screen readers', () => {
      render(<GitHubOAuthButton isLoading />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
    });
  });
});

describe('OAuth Error Display', () => {
  it('displays error message when OAuth fails', async () => {
    // Mock failed OAuth callback
    const searchParams = new URLSearchParams({
      error: 'access_denied',
      error_description: 'User denied access',
    });
    window.location.search = `?${searchParams.toString()}`;

    render(<OAuthButtons />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/user denied access/i)).toBeInTheDocument();
    });
  });

  it('clears error on retry', async () => {
    // Set up error state
    render(<OAuthButtons initialError="Previous error" />);

    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Click OAuth button to retry
    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }));

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
