// Tablet adaptive sidebar with collapsed/expanded states
// Authority: U-014, REMEDIATION_02_Product_Design.md §7

import { useState } from 'react';
import Link from 'next/link';

interface SidebarItem {
  label: string;
  href: string;
  icon: string;
}

const sidebarItems: SidebarItem[] = [
  { label: 'Dashboard', href: '/', icon: '📊' },
  { label: 'Clients', href: '/clients', icon: '👥' },
  { label: 'Calendar', href: '/calendar', icon: '📅' },
  { label: 'Priorities', href: '/priorities', icon: '⭐' },
  { label: 'Workflows', href: '/workflows', icon: '🔄' },
  { label: 'Admin', href: '/admin', icon: '⚙️' },
];

export default function TabletSidebar() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <aside
      className={`tablet-sidebar bg-white border-r border-capco-gray-200 ${
        isExpanded ? 'expanded' : ''
      }`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="flex flex-col h-full py-4">
        {/* Logo/Brand */}
        <div className="px-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl" role="img" aria-label="RM Workbench">
              💼
            </span>
            {isExpanded && (
              <span className="font-semibold text-capco-black whitespace-nowrap">
                RM Workbench
              </span>
            )}
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 space-y-1">
          {sidebarItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-4 py-3 text-capco-gray-600 hover:bg-capco-gray-100 hover:text-capco-black transition-colors"
              title={!isExpanded ? item.label : undefined}
            >
              <span className="text-xl" role="img" aria-hidden="true">
                {item.icon}
              </span>
              {isExpanded && (
                <span className="font-medium whitespace-nowrap">{item.label}</span>
              )}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
