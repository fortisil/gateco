/**
 * Animation and Motion Tokens
 *
 * Consistent motion for a cohesive user experience.
 * Always respect prefers-reduced-motion.
 */

/**
 * Duration values
 */
export const duration = {
  instant: '0ms',
  fast: '100ms',
  normal: '200ms',
  slow: '300ms',
  slower: '500ms',
} as const;

/**
 * Easing functions
 */
export const easing = {
  linear: 'linear',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  // Custom easings for specific interactions
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
} as const;

/**
 * Pre-defined keyframe animations
 */
export const keyframes = {
  fadeIn: {
    from: { opacity: '0' },
    to: { opacity: '1' },
  },
  fadeOut: {
    from: { opacity: '1' },
    to: { opacity: '0' },
  },
  slideUp: {
    from: { opacity: '0', transform: 'translateY(8px)' },
    to: { opacity: '1', transform: 'translateY(0)' },
  },
  slideDown: {
    from: { opacity: '0', transform: 'translateY(-8px)' },
    to: { opacity: '1', transform: 'translateY(0)' },
  },
  slideLeft: {
    from: { opacity: '0', transform: 'translateX(8px)' },
    to: { opacity: '1', transform: 'translateX(0)' },
  },
  slideRight: {
    from: { opacity: '0', transform: 'translateX(-8px)' },
    to: { opacity: '1', transform: 'translateX(0)' },
  },
  scaleIn: {
    from: { opacity: '0', transform: 'scale(0.95)' },
    to: { opacity: '1', transform: 'scale(1)' },
  },
  scaleOut: {
    from: { opacity: '1', transform: 'scale(1)' },
    to: { opacity: '0', transform: 'scale(0.95)' },
  },
  pulse: {
    '0%, 100%': { opacity: '1' },
    '50%': { opacity: '0.5' },
  },
  spin: {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(360deg)' },
  },
  shimmer: {
    '0%': { backgroundPosition: '-200% 0' },
    '100%': { backgroundPosition: '200% 0' },
  },
  // Accordion animations
  accordionDown: {
    from: { height: '0' },
    to: { height: 'var(--radix-accordion-content-height)' },
  },
  accordionUp: {
    from: { height: 'var(--radix-accordion-content-height)' },
    to: { height: '0' },
  },
} as const;

/**
 * Complete animation definitions
 * Combines keyframes with duration and easing.
 */
export const animations = {
  // Entrance
  fadeIn: `fadeIn ${duration.normal} ${easing.easeOut}`,
  slideUp: `slideUp ${duration.normal} ${easing.easeOut}`,
  slideDown: `slideDown ${duration.normal} ${easing.easeOut}`,
  slideLeft: `slideLeft ${duration.normal} ${easing.easeOut}`,
  slideRight: `slideRight ${duration.normal} ${easing.easeOut}`,
  scaleIn: `scaleIn ${duration.fast} ${easing.easeOut}`,

  // Exit
  fadeOut: `fadeOut ${duration.fast} ${easing.easeIn}`,
  scaleOut: `scaleOut ${duration.fast} ${easing.easeIn}`,

  // Looping
  pulse: `pulse 2s ${easing.easeInOut} infinite`,
  spin: `spin 1s ${easing.linear} infinite`,
  shimmer: `shimmer 2s ${easing.linear} infinite`,

  // Accordion
  accordionDown: `accordionDown ${duration.slow} ${easing.easeOut}`,
  accordionUp: `accordionUp ${duration.slow} ${easing.easeOut}`,
} as const;

/**
 * Transition presets for common use cases
 */
export const transitions = {
  // Default transition for most interactive elements
  DEFAULT: `all ${duration.normal} ${easing.easeInOut}`,
  // Fast transition for hover states
  fast: `all ${duration.fast} ${easing.easeOut}`,
  // Slow transition for complex animations
  slow: `all ${duration.slow} ${easing.easeInOut}`,
  // Specific property transitions
  colors: `color, background-color, border-color, text-decoration-color, fill, stroke ${duration.normal} ${easing.easeInOut}`,
  opacity: `opacity ${duration.normal} ${easing.easeInOut}`,
  transform: `transform ${duration.normal} ${easing.easeOut}`,
  shadow: `box-shadow ${duration.normal} ${easing.easeInOut}`,
} as const;

/**
 * Reduced motion settings
 * Use when prefers-reduced-motion: reduce is active.
 */
export const reducedMotion = {
  duration: duration.instant,
  animation: 'none',
  transition: 'none',
} as const;

export type Duration = typeof duration;
export type Easing = typeof easing;
export type Keyframes = typeof keyframes;
export type Animations = typeof animations;
export type Transitions = typeof transitions;
