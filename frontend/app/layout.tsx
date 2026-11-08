'use client';
import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const inter = Inter({ subsets: ['latin'] });

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/clients', label: 'Clients', icon: '👥' },
  { href: '/priorities', label: 'Priorities', icon: '🎯' },
  { href: '/workflows', label: 'Workflows', icon: '⚙️' },
  { href: '/admin', label: 'Admin', icon: '🔧' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen bg-gray-50">
          {/* Sidebar - hidden on mobile */}
          <aside className="hidden md:flex w-64 flex-col bg-slate-900 text-white fixed h-screen">
            <div className="p-4 border-b border-slate-700">
              <h1 className="text-xl font-bold">RM Workbench</h1>
            </div>
            <nav className="flex-1 p-4 space-y-2">
              {navItems.map((item) => {
                const isActive = pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </aside>

          {/* Mobile top nav */}
          <nav className="md:hidden fixed top-0 w-full bg-slate-900 text-white z-50">
            <div className="flex items-center justify-between px-4 py-3">
              <Link href="/dashboard" className="text-lg font-bold">RM Workbench</Link>
              <div className="flex gap-4 text-sm">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`hover:text-blue-400 ${pathname?.startsWith(item.href) ? 'text-blue-400' : ''}`}
                  >
                    {item.icon}
                  </Link>
                ))}
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main className="flex-1 md:ml-64 pt-14 md:pt-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
