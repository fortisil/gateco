/**
 * Status and Plan Color Tokens
 *
 * Status colors are informational only - never used decoratively.
 * Plan colors are exclusive to their respective plan badges.
 */

export const statusColors = {
  allow: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a', // Primary status-allow
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706', // Primary status-warning
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  deny: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626', // Primary status-deny
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6', // Primary status-info
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
} as const;

/**
 * Plan badge colors
 *
 * Constraints:
 * - Purple (#7C3AED) is EXCLUSIVE to Enterprise
 * - Plan colors never dominate the UI
 * - Used only for badges and subtle indicators
 */
export const planColors = {
  free: '#6B7280',      // Gray - neutral, non-promotional
  pro: '#2563EB',       // Blue - slight emphasis
  enterprise: '#7C3AED', // Purple - premium, restrained
} as const;

/**
 * Background colors for the app shell
 * Dark-first design (control plane aesthetic)
 */
export const backgroundColors = {
  primary: '#0F172A',   // App shell, global navigation
  surface: '#111827',   // Cards, tables, main surfaces
  panel: '#1F2937',     // Modals, drawers, nested panels
  canvas: '#FFFFFF',    // Marketing pages, auth, forms
} as const;

/**
 * Text colors
 */
export const textColors = {
  primary: '#F9FAFB',   // Primary content on dark backgrounds
  secondary: '#9CA3AF', // Descriptions, helper text
  muted: '#6B7280',     // Metadata, timestamps
  onLight: '#111827',   // Text on light backgrounds
} as const;

/**
 * Accent colors (Trust Blue)
 */
export const accentColors = {
  primary: '#2563EB',       // Primary CTA, links, focus states
  primaryMuted: '#1D4ED8',  // Hover / active states
} as const;

/**
 * Border colors
 */
export const borderColors = {
  subtle: '#1F2937',    // Card and table borders
  strong: '#374151',    // Emphasized boundaries
  divider: '#374151',   // Section separators
} as const;

/**
 * Interactive surface colors
 */
export const surfaceColors = {
  hover: '#1E293B',     // Hover states
  active: '#020617',    // Active / selected states
} as const;

export type StatusColors = typeof statusColors;
export type PlanColors = typeof planColors;
export type BackgroundColors = typeof backgroundColors;
export type TextColors = typeof textColors;
export type AccentColors = typeof accentColors;
export type BorderColors = typeof borderColors;
export type SurfaceColors = typeof surfaceColors;
