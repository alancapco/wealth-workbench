// Responsive shell wrapper - integrates mobile navigation and gate guard
// Authority: U-014

'use client';

import { ReactNode } from 'react';
import { useBreakpoint } from '@/lib/responsive';
import MobileNavigation from '@/components/responsive/MobileNavigation';
import TabletSidebar from '@/components/responsive/TabletSidebar';
import MobileGateGuard from '@/components/responsive/MobileGateGuard';

interface ResponsiveShellProps {
  children: ReactNode;
}

export default function ResponsiveShell({ children }: ResponsiveShellProps) {
  const breakpoint = useBreakpoint();

  return (
    <MobileGateGuard>
      <div className="min-h-screen">
        {/* Desktop layout with sidebar */}
        {breakpoint === 'desktop' && (
          <div className="desktop-layout">
            <aside className="desktop-sidebar bg-white">
              <div className="p-4">
                <h2 className="text-xl font-semibold mb-4">RM Workbench</h2>
                {/* Desktop navigation would go here */}
              </div>
            </aside>
            <main className="desktop-content">{children}</main>
          </div>
        )}

        {/* Tablet layout with collapsible sidebar */}
        {breakpoint === 'tablet' && (
          <div className="desktop-layout">
            <TabletSidebar />
            <main className="desktop-content">{children}</main>
          </div>
        )}

        {/* Mobile layout with bottom navigation */}
        {breakpoint === 'mobile' && (
          <>
            <main className="pb-20">{children}</main>
            <MobileNavigation />
          </>
        )}
      </div>
    </MobileGateGuard>
  );
}
