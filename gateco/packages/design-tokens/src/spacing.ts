/**
 * Spacing and Sizing Tokens
 *
 * Tailwind-compatible spacing scale for consistent layout.
 */

export const spacing = {
  px: '1px',
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  1.5: '0.375rem',  // 6px
  2: '0.5rem',      // 8px
  2.5: '0.625rem',  // 10px
  3: '0.75rem',     // 12px
  3.5: '0.875rem',  // 14px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  7: '1.75rem',     // 28px
  8: '2rem',        // 32px
  9: '2.25rem',     // 36px
  10: '2.5rem',     // 40px
  11: '2.75rem',    // 44px
  12: '3rem',       // 48px
  14: '3.5rem',     // 56px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
  28: '7rem',       // 112px
  32: '8rem',       // 128px
  36: '9rem',       // 144px
  40: '10rem',      // 160px
  44: '11rem',      // 176px
  48: '12rem',      // 192px
  52: '13rem',      // 208px
  56: '14rem',      // 224px
  60: '15rem',      // 240px
  64: '16rem',      // 256px
  72: '18rem',      // 288px
  80: '20rem',      // 320px
  96: '24rem',      // 384px
} as const;

/**
 * Component-specific sizing
 */
export const sizing = {
  // Input and button heights
  input: {
    sm: '2rem',     // 32px
    md: '2.5rem',   // 40px
    lg: '3rem',     // 48px
  },
  button: {
    sm: '2rem',     // 32px
    md: '2.5rem',   // 40px
    lg: '3rem',     // 48px
  },
  // Icon sizes
  icon: {
    xs: '0.75rem',  // 12px
    sm: '1rem',     // 16px
    md: '1.25rem',  // 20px
    lg: '1.5rem',   // 24px
    xl: '2rem',     // 32px
  },
  // Avatar sizes
  avatar: {
    xs: '1.5rem',   // 24px
    sm: '2rem',     // 32px
    md: '2.5rem',   // 40px
    lg: '3rem',     // 48px
    xl: '4rem',     // 64px
  },
  // Sidebar widths
  sidebar: {
    collapsed: '4rem',   // 64px
    expanded: '15rem',   // 240px
  },
  // Header height
  header: '4rem',        // 64px
  // Modal widths
  modal: {
    sm: '25rem',    // 400px
    md: '31.25rem', // 500px
    lg: '37.5rem',  // 600px
    xl: '50rem',    // 800px
  },
} as const;

/**
 * Container max-widths
 */
export const containers = {
  sm: '40rem',      // 640px
  md: '48rem',      // 768px
  lg: '64rem',      // 1024px
  xl: '80rem',      // 1280px
  '2xl': '96rem',   // 1536px
} as const;

/**
 * Breakpoints for responsive design
 */
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

export type Spacing = typeof spacing;
export type Sizing = typeof sizing;
export type Containers = typeof containers;
export type Breakpoints = typeof breakpoints;
