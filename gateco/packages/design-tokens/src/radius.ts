/**
 * Border Radius Tokens
 *
 * Consistent rounding for a cohesive visual language.
 */

export const radius = {
  none: '0',
  sm: '0.125rem',     // 2px
  DEFAULT: '0.25rem', // 4px
  md: '0.375rem',     // 6px
  lg: '0.5rem',       // 8px
  xl: '0.75rem',      // 12px
  '2xl': '1rem',      // 16px
  '3xl': '1.5rem',    // 24px
  full: '9999px',
} as const;

/**
 * Semantic component radius
 *
 * Use these for consistent component rounding:
 */
export const componentRadius = {
  // Form elements
  button: radius.md,      // 6px
  input: radius.md,       // 6px
  select: radius.md,      // 6px
  checkbox: radius.sm,    // 2px
  switch: radius.full,    // pill shape

  // Containers
  card: radius.lg,        // 8px
  modal: radius.xl,       // 12px
  drawer: radius.xl,      // 12px (on visible edge)
  popover: radius.lg,     // 8px
  dropdown: radius.lg,    // 8px

  // Indicators
  badge: radius.full,     // pill shape
  avatar: radius.full,    // circle
  tag: radius.md,         // 6px
  tooltip: radius.md,     // 6px

  // Feedback
  alert: radius.lg,       // 8px
  toast: radius.lg,       // 8px
  progress: radius.full,  // pill shape
} as const;

export type Radius = typeof radius;
export type ComponentRadius = typeof componentRadius;
