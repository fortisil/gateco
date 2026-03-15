/**
 * Shadow and Elevation Tokens
 *
 * Shadows provide visual hierarchy and depth.
 */

export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
} as const;

/**
 * Dark mode shadows (for dark backgrounds)
 * Higher opacity for visibility on dark surfaces.
 */
export const shadowsDark = {
  none: 'none',
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.3)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.4), 0 8px 10px -6px rgb(0 0 0 / 0.3)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.5)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.2)',
} as const;

/**
 * Semantic elevation levels
 *
 * Use these for consistent component elevation:
 * - surface: Base level (cards on page)
 * - raised: Slightly raised (hover states)
 * - overlay: Dropdowns, tooltips
 * - modal: Modals, drawers
 * - popover: Popovers, command palettes
 */
export const elevation = {
  surface: shadows.none,
  raised: shadows.sm,
  overlay: shadows.md,
  modal: shadows.lg,
  popover: shadows.xl,
} as const;

/**
 * Ring (focus outline) shadows
 */
export const rings = {
  // Default focus ring
  DEFAULT: '0 0 0 2px var(--ring-color, #2563eb)',
  // With offset
  offset: '0 0 0 2px var(--ring-offset-color, #fff), 0 0 0 4px var(--ring-color, #2563eb)',
  // Error state
  error: '0 0 0 2px var(--ring-color, #dc2626)',
} as const;

export type Shadows = typeof shadows;
export type ShadowsDark = typeof shadowsDark;
export type Elevation = typeof elevation;
export type Rings = typeof rings;
