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
  TrendingUp,
  DollarSign,
  BarChart2,
  Users2,
} from 'lucide-react';

const inter = Inter({ subsets: ['latin'] });

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/clients', label: 'Clients', icon: Users },
  { href: '/priorities', label: 'Priorities', icon: Target },
  { href: '/workflows', label: 'Workflows', icon: Workflow },
  { href: '/admin', label: 'Admin', icon: Settings },
];

const portfolioNavItems = [
  { href: '/portfolio', label: 'Portfolio Hub', icon: TrendingUp },
  { href: '/portfolio/currency', label: 'Currency Exposure', icon: DollarSign },
  { href: '/portfolio/future-planner', label: 'Future Planner', icon: BarChart2 },
  { href: '/portfolio/investors-like-me', label: 'Investors Like Me', icon: Users2 },
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
            className={`hidden md:flex flex-col bg-black text-white fixed h-screen transition-all duration-200 z-40 ${
              collapsed ? 'w-16' : 'w-64'
            }`}
          >
            {/* Logo / App name */}
            <div className={`flex items-center border-b border-gray-800 h-14 ${collapsed ? 'justify-center px-0' : 'px-4'}`}>
              {!collapsed && (
                <span className="text-lg font-bold truncate">RM Workbench</span>
              )}
              {collapsed && (
                <span className="text-lg font-bold">RM</span>
              )}
            </div>

            {/* Nav items */}
            <nav className="flex-1 py-4 px-2 overflow-y-auto">
              <div className="space-y-1">
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
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-400 hover:bg-gray-900 hover:text-white'
                      } ${collapsed ? 'justify-center' : ''}`}
                    >
                      <Icon size={20} className="shrink-0" />
                      {!collapsed && (
                        <span className="text-sm font-medium">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>

              {/* Portfolio & Analytics section */}
              {!collapsed && (
                <div className="mt-6 mb-1 px-3">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Portfolio &amp; Analytics
                  </span>
                </div>
              )}
              {collapsed && <div className="mt-4 border-t border-gray-800 mb-2" />}
              <div className="space-y-1">
                {portfolioNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                        isActive
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-400 hover:bg-gray-900 hover:text-white'
                      } ${collapsed ? 'justify-center' : ''}`}
                    >
                      <Icon size={20} className="shrink-0" />
                      {!collapsed && (
                        <span className="text-sm font-medium">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </nav>

            {/* Collapse toggle button */}
            <div className="border-t border-gray-800 p-2">
              <button
                onClick={() => setCollapsed(!collapsed)}
                className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-gray-500 hover:bg-gray-900 hover:text-white transition-colors ${
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
          <nav className="md:hidden fixed top-0 w-full bg-black text-white z-50 h-14">
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
                        isActive ? 'text-white bg-gray-800' : 'text-gray-400 hover:text-white'
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
