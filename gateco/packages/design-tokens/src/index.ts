/**
 * Design tokens for Gateco
 *
 * This package exports all design tokens for consistent styling
 * across the Gateco frontend application and marketing website.
 */

// Core colors
export * from './colors.js';

// Status and semantic colors
export * from './status-colors.js';

// Typography
export * from './typography.js';

// Spacing and sizing
export * from './spacing.js';

// Shadows and elevation
export * from './shadows.js';

// Animation and motion
export * from './animation.js';

// Border radius
export * from './radius.js';

// Tailwind preset (for use in tailwind.config.ts)
export { preset as tailwindPreset, componentRadius } from './tailwind-preset.js';
