/**
 * Tailwind CSS preset with design tokens
 *
 * This preset provides a complete design system for Gateco.
 * Import in tailwind.config.ts: presets: [require('@gateco/design-tokens/tailwind')]
 */

import { colors } from './colors.js';
import { typography } from './typography.js';
import {
  statusColors,
  planColors,
  backgroundColors,
  textColors,
  accentColors,
  borderColors,
  surfaceColors,
} from './status-colors.js';
import { spacing, sizing, containers, breakpoints } from './spacing.js';
import { shadows, elevation, rings } from './shadows.js';
import { duration, easing, keyframes, animations, transitions } from './animation.js';
import { radius, componentRadius } from './radius.js';

export const preset = {
  theme: {
    extend: {
      // Colors
      colors: {
        ...colors,
        // Status colors (semantic)
        status: {
          allow: statusColors.allow,
          warning: statusColors.warning,
          deny: statusColors.deny,
          info: statusColors.info,
        },
        // Plan colors (badge)
        plan: planColors,
        // Background colors
        bg: backgroundColors,
        // Text colors
        text: textColors,
        // Accent colors
        accent: accentColors,
        // Border colors
        border: borderColors,
        // Surface colors
        surface: surfaceColors,
      },

      // Typography
      fontFamily: typography.fontFamily,
      fontSize: typography.fontSize,

      // Spacing
      spacing,

      // Border Radius
      borderRadius: radius,

      // Shadows
      boxShadow: {
        ...shadows,
        // Elevation aliases
        'elevation-surface': elevation.surface,
        'elevation-raised': elevation.raised,
        'elevation-overlay': elevation.overlay,
        'elevation-modal': elevation.modal,
        'elevation-popover': elevation.popover,
        // Ring shadows
        ring: rings.DEFAULT,
        'ring-offset': rings.offset,
        'ring-error': rings.error,
      },

      // Animation
      transitionDuration: {
        instant: duration.instant,
        fast: duration.fast,
        normal: duration.normal,
        slow: duration.slow,
        slower: duration.slower,
      },
      transitionTimingFunction: {
        DEFAULT: easing.easeInOut,
        linear: easing.linear,
        in: easing.easeIn,
        out: easing.easeOut,
        'in-out': easing.easeInOut,
        bounce: easing.bounce,
        spring: easing.spring,
      },
      keyframes,
      animation: animations,

      // Container max-widths
      maxWidth: containers,

      // Screen breakpoints
      screens: breakpoints,

      // Component sizes
      width: {
        'sidebar-collapsed': sizing.sidebar.collapsed,
        'sidebar-expanded': sizing.sidebar.expanded,
        'modal-sm': sizing.modal.sm,
        'modal-md': sizing.modal.md,
        'modal-lg': sizing.modal.lg,
        'modal-xl': sizing.modal.xl,
      },
      height: {
        header: sizing.header,
        'input-sm': sizing.input.sm,
        'input-md': sizing.input.md,
        'input-lg': sizing.input.lg,
        'button-sm': sizing.button.sm,
        'button-md': sizing.button.md,
        'button-lg': sizing.button.lg,
      },
    },
  },
  plugins: [],
};

export default preset;

// Re-export component radius for programmatic use
export { componentRadius };
