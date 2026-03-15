/**
 * Color palette
 */

export const colors = {
  primary: {
    50: '#e8eefd',
    100: '#d0defb',
    200: '#a2bcf6',
    300: '#6a94f1',
    400: '#316cec',
    500: '#1554e0',
    600: '#1146bb',
    700: '#0e3895',
    800: '#0a2a70',
    900: '#061a46',
  },
  secondary: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },
} as const;

export type ColorScale = typeof colors.primary;
export type Colors = typeof colors;
