import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import HomePage from '@/app/page';

describe('HomePage', () => {
  it('renders the title', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Gateco');
  });

  it('renders the call-to-action buttons', () => {
    render(<HomePage />);
    // Multiple "Get started" links exist (header + hero + final CTA), verify at least one is present
    const getStartedLinks = screen.getAllByRole('link', { name: /get started/i });
    expect(getStartedLinks.length).toBeGreaterThan(0);
    // Multiple "Learn more" links exist, verify at least one is present
    const learnMoreLinks = screen.getAllByRole('link', { name: /learn more/i });
    expect(learnMoreLinks.length).toBeGreaterThan(0);
  });
});
