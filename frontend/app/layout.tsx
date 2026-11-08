'use client';

import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  Target,
  Workflow,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const inter = Inter({ subsets: ['latin'] });

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/clients', label: 'Clients', icon: Users },
  { href: '/priorities', label: 'Priorities', icon: Target },
  { href: '/workflows', label: 'Workflows', icon: Workflow },
  { href: '/admin', label: 'Admin', icon: Settings },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen bg-gray-50">

          {/* Desktop Sidebar */}
          <aside
            className={`hidden md:flex flex-col bg-slate-900 text-white fixed h-screen transition-all duration-200 z-40 ${
              collapsed ? 'w-16' : 'w-64'
            }`}
          >
            {/* Logo / App name */}
            <div className={`flex items-center border-b border-slate-700 h-14 ${collapsed ? 'justify-center px-0' : 'px-4'}`}>
              {!collapsed && (
                <span className="text-lg font-bold truncate">RM Workbench</span>
              )}
              {collapsed && (
                <span className="text-lg font-bold">RM</span>
              )}
            </div>

            {/* Nav items */}
            <nav className="flex-1 py-4 space-y-1 px-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    } ${collapsed ? 'justify-center' : ''}`}
                  >
                    <Icon size={20} className="shrink-0" />
                    {!collapsed && (
                      <span className="text-sm font-medium">{item.label}</span>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Collapse toggle button */}
            <div className="border-t border-slate-700 p-2">
              <button
                onClick={() => setCollapsed(!collapsed)}
                className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors ${
                  collapsed ? 'justify-center' : ''
                }`}
                title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {collapsed ? (
                  <ChevronRight size={18} />
                ) : (
                  <>
                    <ChevronLeft size={18} />
                    <span className="text-sm">Collapse</span>
                  </>
                )}
              </button>
            </div>
          </aside>

          {/* Mobile top nav */}
          <nav className="md:hidden fixed top-0 w-full bg-slate-900 text-white z-50 h-14">
            <div className="flex items-center justify-between px-4 h-full">
              <Link href="/dashboard" className="text-base font-bold">RM Workbench</Link>
              <div className="flex items-center gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname?.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={item.label}
                      className={`p-2 rounded-lg transition-colors ${
                        isActive ? 'text-blue-400' : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      <Icon size={20} />
                    </Link>
                  );
                })}
              </div>
            </div>
          </nav>

          {/* Main content — offset by sidebar width */}
          <main
            className={`flex-1 pt-14 md:pt-0 transition-all duration-200 ${
              collapsed ? 'md:ml-16' : 'md:ml-64'
            }`}
          >
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
