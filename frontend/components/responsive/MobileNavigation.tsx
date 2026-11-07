// Mobile bottom navigation with collapsible menu
// Authority: U-014, REMEDIATION_02_Product_Design.md §7

import { useState } from 'react';
import Link from 'next/link';

interface NavItem {
  label: string;
  href: string;
  icon: string;
  active?: boolean;
}

const navigationItems: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: '📊' },
  { label: 'Clients', href: '/clients', icon: '👥' },
  { label: 'Calendar', href: '/calendar', icon: '📅' },
  { label: 'Profile', href: '/profile', icon: '👤' },
];

export default function MobileNavigation() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <nav className="mobile-nav-bottom bg-white border-t border-capco-gray-200 shadow-lg">
      <div className="flex items-center justify-around px-4 py-2">
        {navigationItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="touch-target flex flex-col items-center justify-center text-capco-gray-600 hover:text-capco-black transition-colors"
            aria-label={item.label}
          >
            <span className="text-2xl mb-1" role="img" aria-hidden="true">
              {item.icon}
            </span>
            <span className="text-xs font-medium">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
