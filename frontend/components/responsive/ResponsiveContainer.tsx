// Main responsive container with breakpoint detection
// Authority: U-014

import { ReactNode } from 'react';
import { useBreakpoint } from '@/lib/responsive';

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * Main container that detects breakpoint and provides context
 * Breakpoints: desktop ≥1024px, tablet 768-1023px, mobile <768px
 */
export default function ResponsiveContainer({ children, className = '' }: ResponsiveContainerProps) {
  const breakpoint = useBreakpoint();

  return (
    <div 
      className={`responsive-container ${className}`}
      data-breakpoint={breakpoint}
    >
      {children}
    </div>
  );
}
