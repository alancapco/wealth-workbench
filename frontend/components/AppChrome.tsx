'use client';

/**
 * Application chrome: a two-level navigation (group rail + section panel),
 * a global top bar with client search, and the content frame.
 *
 * The narrow icon rail follows the layout language in the Wealth/ reference
 * screenshots; the second level keeps every feature visible without the
 * previous flat, undifferentiated sidebar.
 */
import React, { ReactNode, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard, Users, CalendarDays, Workflow, PieChart, Settings2,
  PanelLeftClose, PanelLeftOpen, Search, Menu, X, ChevronRight,
  CircleUserRound, Activity,
  type LucideIcon,
} from 'lucide-react';
import { NAV_GROUPS, groupForPath, itemForPath, NavGroup } from '@/lib/navigation';
import { useApp } from '@/lib/app-context';

const GROUP_ICONS: Record<string, LucideIcon> = {
  day: LayoutDashboard,
  book: Users,
  journey: Workflow,
  studio: CalendarDays,
  market: PieChart,
  inspector: Settings2,
};

const RAIL_W = 56;
const PANEL_W = 240;

export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname() || '/dashboard';
  const router = useRouter();
  const app = useApp();
  const activeGroup = groupForPath(pathname);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [searchFocus, setSearchFocus] = useState(false);

  // The rail follows the current page unless the user explicitly picked a group.
  const shownGroup: NavGroup =
    NAV_GROUPS.find((g) => g.id === (selectedGroupId || activeGroup.id)) || activeGroup;

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return app.clients
      .filter((c) =>
        [c.name, c.external_id, c.email, c.region, c.client_type]
          .filter(Boolean)
          .some((v: unknown) => String(v).toLowerCase().includes(q)),
      )
      .slice(0, 6);
  }, [query, app.clients]);

  const offset = panelOpen ? RAIL_W + PANEL_W : RAIL_W;

  const navList = (group: NavGroup, onNavigate?: () => void) => (
    <nav className="space-y-0.5">
      {group.items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            title={item.description}
            className={`group block px-3 py-2 rounded border-l-2 transition-colors ${
              isActive
                ? 'border-black bg-gray-100 text-black'
                : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-black'
            }`}
          >
            <div className={`text-[13px] leading-tight ${isActive ? 'font-semibold' : 'font-medium'}`}>
              {item.label}
            </div>
            <div className="text-[10px] leading-snug text-gray-400 mt-0.5 line-clamp-2">
              {item.description}
            </div>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* ---------------- Level 1: group rail ---------------- */}
      <aside
        className="hidden md:flex flex-col fixed inset-y-0 left-0 bg-black z-50"
        style={{ width: RAIL_W }}
      >
        <Link
          href="/dashboard"
          className="h-14 flex items-center justify-center border-b border-gray-800 shrink-0"
          title="WM Workbench — My Day"
        >
          <span className="text-white font-bold text-[15px] tracking-tight">WM</span>
        </Link>

        <div className="flex-1 py-3 overflow-y-auto">
          {NAV_GROUPS.map((g) => {
            const Icon = GROUP_ICONS[g.id] || LayoutDashboard;
            const isActive = shownGroup.id === g.id;
            return (
              <button
                key={g.id}
                onClick={() => {
                  setSelectedGroupId(g.id);
                  setPanelOpen(true);
                }}
                title={g.label}
                aria-label={g.label}
                className={`w-full h-11 flex items-center justify-center relative transition-colors ${
                  isActive ? 'text-white bg-gray-800' : 'text-gray-500 hover:text-white hover:bg-gray-900'
                }`}
              >
                {isActive && <span className="absolute left-0 top-2 bottom-2 w-0.5 bg-white" />}
                <Icon size={19} />
              </button>
            );
          })}
        </div>

        <div className="py-2 border-t border-gray-800 flex flex-col items-center gap-1">
          <button
            onClick={() => setPanelOpen((v) => !v)}
            title={panelOpen ? 'Hide section panel' : 'Show section panel'}
            className="w-10 h-9 flex items-center justify-center text-gray-500 hover:text-white rounded"
          >
            {panelOpen ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
          </button>
        </div>
      </aside>

      {/* ---------------- Level 2: section panel ---------------- */}
      {panelOpen && (
        <aside
          className="hidden md:flex flex-col fixed inset-y-0 bg-white border-r border-gray-200 z-40"
          style={{ left: RAIL_W, width: PANEL_W }}
        >
          <div className="h-14 px-4 flex flex-col justify-center border-b border-gray-200 shrink-0">
            <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-400">
              Section
            </div>
            <div className="text-[13px] font-semibold text-black truncate">{shownGroup.label}</div>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-4">{navList(shownGroup)}</div>

          <div className="px-4 py-3 border-t border-gray-200 shrink-0">
            <div className="flex items-center gap-2">
              <Activity size={13} className={app.error ? 'text-gray-400' : 'text-black'} />
              <span className="text-[10px] font-medium text-gray-600">
                {app.error ? 'Backend unavailable' : 'Connected to live data'}
              </span>
            </div>
            <div className="text-[10px] text-gray-400 mt-1 truncate">
              {app.clients.length} clients · {app.demoClients.length} demo clients ·{' '}
              {app.workflows.length} workflows
            </div>
          </div>
        </aside>
      )}

      {/* ---------------- Top bar ---------------- */}
      <header
        className="fixed top-0 right-0 h-14 bg-white border-b border-gray-200 z-30 flex items-center gap-3 px-4 md:px-6"
        style={{ left: 0 }}
      >
        <div className="hidden md:block" style={{ width: Math.max(0, offset - 24) }} />
        <button
          className="md:hidden p-2 -ml-2 text-gray-700"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>

        <div className="hidden lg:flex items-center gap-1.5 text-xs text-gray-500 min-w-0">
          <span className="truncate">{activeGroup.label}</span>
          <ChevronRight size={13} className="text-gray-300 shrink-0" />
          <span className="font-medium text-black truncate">
            {itemForPath(pathname)?.label || 'Detail'}
          </span>
        </div>

        <div className="flex-1" />

        {/* Global client search — results come from the live client book */}
        <div className="relative w-full max-w-[300px] hidden sm:block">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setSearchFocus(true)}
            onBlur={() => setTimeout(() => setSearchFocus(false), 150)}
            placeholder="Search clients…"
            className="w-full h-8 pl-8 pr-3 text-xs border border-gray-200 rounded bg-gray-50 outline-none focus:border-black focus:bg-white"
          />
          {searchFocus && query.trim() && (
            <div className="absolute top-9 left-0 right-0 bg-white border border-gray-200 rounded shadow-lg py-1 max-h-72 overflow-y-auto">
              {results.length === 0 ? (
                <div className="px-3 py-2 text-xs text-gray-400">No matching clients</div>
              ) : (
                results.map((c) => (
                  <button
                    key={c.id}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => {
                      app.setClientId(c.id);
                      setQuery('');
                      setSearchFocus(false);
                      router.push(`/clients/${c.id}`);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50"
                  >
                    <div className="text-xs font-medium text-black">{c.name}</div>
                    <div className="text-[10px] text-gray-400">
                      {[c.client_type, c.region].filter(Boolean).join(' · ') || 'Client'}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        {/* Shared live client context */}
        <div className="hidden xl:flex items-center gap-2 min-w-0">
          <span className="text-[10px] text-gray-400 uppercase tracking-wide">Client</span>
          <select
            value={app.clientId}
            onChange={(e) => app.setClientId(e.target.value)}
            className="max-w-[170px] h-8 px-2 text-xs border border-gray-200 rounded bg-white outline-none focus:border-black truncate"
            aria-label="Active client"
          >
            {app.clientOptions.length === 0 && <option value="">No clients loaded</option>}
            {app.clientOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <Link
          href="/admin/session"
          className="flex items-center gap-2 pl-3 border-l border-gray-200 shrink-0"
          title={app.session?.subject || 'Session'}
        >
          <CircleUserRound size={18} className="text-gray-600" />
          <div className="hidden 2xl:block leading-tight">
            <div className="text-[11px] font-medium text-black truncate max-w-[130px]">
              {app.session?.display_name || 'Loading…'}
            </div>
            <div className="text-[9px] text-gray-400">
              {app.session?.environment?.kind || '—'}
            </div>
          </div>
        </Link>
      </header>

      {/* ---------------- Mobile drawer ---------------- */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-[60]">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-[300px] bg-white overflow-y-auto">
            <div className="h-14 px-4 flex items-center justify-between border-b border-gray-200">
              <span className="font-semibold text-black">WM Workbench</span>
              <button onClick={() => setMobileOpen(false)} aria-label="Close navigation">
                <X size={18} />
              </button>
            </div>
            <div className="p-4">
              {NAV_GROUPS.map((g) => (
                <div key={g.id} className="mb-5">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-400 mb-2">
                    {g.label}
                  </div>
                  <div className="space-y-0.5">{navList(g, () => setMobileOpen(false))}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ---------------- Content ---------------- */}
      <main
        className="min-h-screen bg-gray-50 pt-14 transition-[padding] duration-200"
        style={{ paddingLeft: undefined }}
      >
        <div className="hidden md:block" style={{ width: 0 }} />
        <div
          className="hidden md:block fixed top-14 bottom-0 bg-gray-50 pointer-events-none -z-10"
          style={{ left: RAIL_W, right: 0 }}
        />
        <div className="md:pl-0" style={{ ['--chrome-offset' as any]: `${offset}px` }}>
          <div className="md:ml-[var(--chrome-offset)]">{children}</div>
        </div>
      </main>
    </>
  );
}
