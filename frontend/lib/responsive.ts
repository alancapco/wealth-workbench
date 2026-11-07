// Responsive utilities and hooks for mobile/tablet/desktop detection
// Authority: U-014, REMEDIATION_02_Product_Design.md §7

import { useState, useEffect } from 'react';

// Breakpoint constants (px values)
export const MOBILE_MAX = 767;
export const TABLET_MIN = 768;
export const TABLET_MAX = 1023;
export const DESKTOP_MIN = 1024;

export type Breakpoint = 'mobile' | 'tablet' | 'desktop';

/**
 * Detects current breakpoint based on window width
 * mobile: <768px, tablet: 768-1023px, desktop: ≥1024px
 */
export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('desktop');

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      if (width < TABLET_MIN) {
        setBreakpoint('mobile');
      } else if (width <= TABLET_MAX) {
        setBreakpoint('tablet');
      } else {
        setBreakpoint('desktop');
      }
    };

    // Initial check
    updateBreakpoint();

    // Listen for resize
    window.addEventListener('resize', updateBreakpoint);
    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  return breakpoint;
}

/**
 * Boolean convenience wrapper for mobile detection
 */
export function useIsMobile(): boolean {
  const breakpoint = useBreakpoint();
  return breakpoint === 'mobile';
}

/**
 * Detects if device has touch capability
 */
export function useTouchDevice(): boolean {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    const checkTouch = () => {
      const hasTouchScreen = 
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0 ||
        (window.matchMedia && window.matchMedia('(pointer: coarse)').matches);
      setIsTouch(hasTouchScreen);
    };

    checkTouch();
  }, []);

  return isTouch;
}

/**
 * Get breakpoint as CSS media query string
 */
export function getBreakpointQuery(breakpoint: Breakpoint): string {
  switch (breakpoint) {
    case 'mobile':
      return `(max-width: ${MOBILE_MAX}px)`;
    case 'tablet':
      return `(min-width: ${TABLET_MIN}px) and (max-width: ${TABLET_MAX}px)`;
    case 'desktop':
      return `(min-width: ${DESKTOP_MIN}px)`;
  }
}
