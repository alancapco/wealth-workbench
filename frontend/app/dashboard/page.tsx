'use client';

/**
 * My Day — flagship workspace.
 * Layout follows the Wealth/ reference screenshots: greeting + date strip,
 * KPI row, two-column priority/propensity grid, insights, performance overview.
 * Every value is fetched from the live API; empty sources render an honest
 * empty state instead of sample content.
 */
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useApp } from '@/lib/app-context';
import { endpoints } from '@/lib/endpoints';
import type { DateRange } from 'react-day-picker';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import { Label } from '@/components/ui/label';
import {
  PageShell, Card, StatCard, ViewAll, Loading, ErrorState, EmptyState,
  DataTable, Button, SectionLabel,
} from '@/components/ui/WorkbenchUI';
import { Grid } from '@/components/ui/LiveFeature';
import { money, pct } from '@/lib/format';

function useLive<T>(loader: () => Promise<{ data: T }>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const reload = () => {
    setLoading(true);
    loader()
      .then((r) => { setData(r.data); setError(null); })
      .catch((e) => { setError(e); setData(null); })
      .finally(() => setLoading(false));
  };
  useEffect(reload, []); // eslint-disable-line react-hooks/exhaustive-deps
  return { data, error, loading, reload };
}

/**
 * Node's ICU and the browser's ICU disagree on en-GB date punctuation
 * ("Monday, 9 November 2026" vs "Monday 9 November 2026"), which crashes
 * hydration. Build the label from plain UTC getters instead — deterministic
 * on both sides. Asia/Singapore is UTC+8 with no DST.
 */
const SGT_OFFSET_MS = 8 * 60 * 60 * 1000;
const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const pad = (n: number) => String(n).padStart(2, '0');
const NEWS_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function formatNewsTime(value?: string) {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  return `${d.getUTCDate()} ${NEWS_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}
function sgtParts(date: Date) {
  const d = new Date(date.getTime() + SGT_OFFSET_MS);
  return {
    weekday: WEEKDAYS[d.getUTCDay()],
    day: d.getUTCDate(),
    month: MONTHS[d.getUTCMonth()],
    year: d.getUTCFullYear(),
    hour: d.getUTCHours(),
    minute: d.getUTCMinutes(),
  };
}

export default function DashboardPage() {
  const app = useApp();
  const [clock, setClock] = useState<Date>(new Date());
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const kpis = useLive<any>(() => endpoints.dashboard.kpis());
  const myDay = useLive<any>(() => endpoints.dashboard.myDay());
  const allocation = useLive<any>(() => endpoints.dashboard.allocation());
  const performance = useLive<any>(() => endpoints.dashboard.performance());
  const news = useLive<any>(() => endpoints.market.news(8));
  const bookStats = useLive<any>(() => endpoints.dashboard.bookStats());
  const [activityRange, setActivityRange] = useState<DateRange | undefined>();

  const ranked: any[] = myDay.data?.ranked_clients || [];
  const actions: any[] = myDay.data?.priority_actions || [];
  const newsItems: any[] = Array.isArray(news.data?.news) ? news.data.news : [];
  const breakdown: any[] = allocation.data?.breakdown || [];
  const perfLabels: string[] = performance.data?.labels || [];
  const perfValues: number[] = performance.data?.datasets?.[0]?.data || [];

  const t = sgtParts(clock);
  const dateLabel = `${t.weekday}, ${t.day} ${t.month} ${t.year}`;
  const timeLabel = `${pad(t.hour)}:${pad(t.minute)}`;
  const greeting = t.hour < 12 ? 'Good morning' : t.hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <PageShell wide>
      {/* Greeting strip */}
      <div className="mb-6">
        <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-500 mb-1.5">
          Workspace · My Day
        </div>
        <h1 suppressHydrationWarning className="text-[26px] leading-tight font-semibold tracking-tight text-black">
          {greeting}, {app.session?.display_name || 'there'}.
        </h1>
        <p suppressHydrationWarning className="mt-1.5 text-sm text-gray-500">
          {dateLabel} · {timeLabel} SGT
          {app.session?.environment?.kind
            ? ` · ${String(app.session.environment.kind).replace(/_/g, ' ').toLowerCase()} environment`
            : ''}
        </p>
      </div>

      {app.error && (
        <div className="mb-5"><ErrorState error={new Error(app.error)} onRetry={app.refresh} /></div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-5">
        {kpis.loading ? (
          <div className="col-span-full"><Card><Loading label="Loading live KPIs…" /></Card></div>
        ) : kpis.error ? (
          <div className="col-span-full"><ErrorState error={kpis.error} onRetry={kpis.reload} /></div>
        ) : (
          <>
        <StatCard label="Book AUM" value={money(kpis.data?.total_aum)} sub={`${kpis.data?.client_count ?? '—'} clients in the journey`} href="/journey" />
        <StatCard label="Meetings today" value={kpis.data?.meetings_today ?? '—'} sub="Recorded on the journey" href="/journey/discover" />
        <StatCard label="Open pipeline" value={kpis.data?.open_actions ?? '—'} sub={money(kpis.data?.pipeline_forecast_usd) + ' weighted'} href="/journey/pipeline" />
        <StatCard label="Holdings" value={kpis.data?.holdings_count ?? '—'} sub={money(kpis.data?.holdings_value_usd)} href="/portfolio" />
        <StatCard label="Weighted unrealised gain" value={pct(kpis.data?.ytd_performance)} sub="From the same holdings" href="/portfolio" />
          </>
        )}
      </div>

      {/* Priorities + propensity */}
      <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-5 mb-5">
        <Card
          title="Today's priorities"
          subtitle="From the wealth journey: who to contact and why"
          action={<ViewAll href="/journey" />}
          bodyClassName="p-0"
        >
          {myDay.loading ? <div className="p-5"><Loading /></div> : myDay.error ? (
            <div className="p-5"><ErrorState error={myDay.error} onRetry={myDay.reload} /></div>
          ) : actions.length === 0 ? (
            <EmptyState
              title="No priority actions"
              detail="Run a priority evaluation to populate today's list."
              action={<Link href="/journey"><Button variant="primary">Open the journey</Button></Link>}
            />
          ) : (
            <div className="divide-y divide-gray-100">
              {actions.map((a: any, i: number) => (
                <div key={i} className="px-5 py-3.5 flex items-start gap-4">
                  <div className="w-7 h-7 shrink-0 rounded-full bg-gray-100 flex items-center justify-center text-xs font-semibold text-black">
                    {a.priority ?? i + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-black">{a.title}</div>
                    <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{a.description || 'No description returned'}</div>
                  </div>
                  {a.client_id && (
                    <Link href={`/journey?client=${a.client_id}`} className="text-xs text-gray-600 hover:text-black shrink-0">
                      Open →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          title="Top propensity clients"
          subtitle="Same ranking as Engage"
          action={<ViewAll href="/journey" />}
          bodyClassName="p-0"
        >
          {myDay.loading ? <div className="p-5"><Loading /></div> : ranked.length === 0 ? (
            <EmptyState title="No ranked clients" detail="The ranking service has no scored clients yet." />
          ) : (
            <div className="divide-y divide-gray-100">
              {ranked.slice(0, 6).map((c: any, i: number) => (
                <Link key={c.client_id || i} href={`/journey?client=${c.client_id}`} className="px-5 py-3 flex items-center gap-3 hover:bg-gray-50">
                  <div className="w-8 h-8 shrink-0 rounded-full border border-gray-300 flex items-center justify-center text-xs font-semibold text-black">
                    {Math.round(c.total_score ?? 0)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-black truncate">{c.name}</div>
                    <div className="text-[11px] text-gray-400 truncate">
                      {money(c.aum)} · rank {c.rank ?? i + 1}
                    </div>
                  </div>
                  <span className="text-gray-300">›</span>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="mb-5">
        <Card
          title="What happened in the journey"
          subtitle="Latest stage events. Ahmad Rahman and Tan Family Office are separate clients."
          action={<ViewAll href="/journey/service" label="Service" />}
        >
          {myDay.loading ? <Loading /> : (myDay.data?.journey?.recent || []).length === 0 ? (
            <EmptyState title="No journey events yet" detail="Open Engage and work a client. Activity shows up here." />
          ) : (
            <div className="space-y-3">
              <div className="max-w-sm space-y-1.5">
                <Label>Activity period</Label>
                <DateRangePicker value={activityRange} onChange={setActivityRange} />
              </div>
              <ul className="space-y-2 text-sm">
                {(myDay.data.journey.recent as any[]).filter((event) => {
                  if (!activityRange?.from || !event.occurred_at) return true;
                  const when = new Date(event.occurred_at);
                  const start = new Date(activityRange.from);
                  start.setHours(0, 0, 0, 0);
                  if (when < start) return false;
                  if (!activityRange.to) return true;
                  const end = new Date(activityRange.to);
                  end.setHours(23, 59, 59, 999);
                  return when <= end;
                }).map((event, i) => (
                  <li key={i} className="border-b border-gray-100 pb-2">
                    <span className="font-medium">{event.stage}</span>
                    {' · '}{event.event}
                    {event.client_name ? ` · ${event.client_name}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      </div>

      {/* Insights */}
      <div className="mb-5">
        <Card
          title="Today's insights"
          subtitle="Live market news feed"
          action={<ViewAll href="/market" label="Market data" />}
        >
          {news.loading ? <Loading /> : news.error ? (
            <ErrorState error={news.error} onRetry={news.reload} />
          ) : newsItems.length === 0 ? (
            <EmptyState
              title="No news items available"
              detail="The market news provider returned an empty feed. Configure a provider in the environment to populate this panel."
            />
          ) : (
            <ul className="space-y-3">
              {newsItems.map((n: any, i: number) => {
                const summary = n.content || n.summary;
                const when = formatNewsTime(n.timestamp);
                const title = n.title || n.headline || 'Untitled';
                return (
                  <li key={n.id || i} className="text-xs text-gray-700 border-b border-gray-100 pb-2 last:border-0">
                    {n.url ? (
                      <a href={n.url} target="_blank" rel="noopener noreferrer" className="font-medium text-black hover:underline">
                        {title}
                      </a>
                    ) : (
                      <span className="font-medium text-black">{title}</span>
                    )}
                    {(n.source || when) && (
                      <span className="block text-[11px] text-gray-400 mt-0.5">
                        {[n.source, when].filter(Boolean).join(' · ')}
                      </span>
                    )}
                    {summary && <span className="block text-gray-500 mt-0.5 line-clamp-2">{summary}</span>}
                  </li>
                );
              })}
            </ul>
          )}
        </Card>
      </div>

      {/* Performance overview */}
      <SectionLabel>Performance overview</SectionLabel>
      <Grid>
        <Card
          title="Asset allocation"
          subtitle={allocation.data?.source || 'Live holdings'}
          action={<ViewAll href="/portfolio" />}
          bodyClassName="p-0"
        >
          {allocation.loading ? <div className="p-5"><Loading /></div> : allocation.error ? (
            <div className="p-5"><ErrorState error={allocation.error} onRetry={allocation.reload} /></div>
          ) : (
            <div className="p-5">
              <div className="flex flex-wrap gap-2 mb-4">
                {breakdown.map((b: any) => (
                  <div key={b.asset_class} className="border border-gray-200 rounded px-3 py-2 min-w-[120px]">
                    <div className="text-[10px] uppercase tracking-wide text-gray-500">{b.asset_class}</div>
                    <div className="text-lg font-semibold text-black tabular-nums">{b.percentage}%</div>
                    <div className="text-[10px] text-gray-400">{money(b.value)}</div>
                  </div>
                ))}
              </div>
              <div className="w-full h-3 flex overflow-hidden rounded bg-gray-100 border border-gray-200">
                {breakdown.map((b: any, i: number) => (
                  <div
                    key={b.asset_class}
                    title={`${b.asset_class}: ${b.percentage}%`}
                    style={{ width: `${b.percentage}%`, background: ['#0A0A0A', '#3A3A3A', '#666666', '#999999', '#CCCCCC', '#E5E5E5'][i % 6] }}
                  />
                ))}
              </div>
            </div>
          )}
        </Card>

        <Card
          title="Return by asset class"
          subtitle={performance.data?.note || 'Weighted unrealised gain from live holdings'}
          action={<ViewAll href="/portfolio" />}
        >
          {performance.loading ? <Loading /> : performance.error ? (
            <ErrorState error={performance.error} onRetry={performance.reload} />
          ) : perfLabels.length === 0 ? (
            <EmptyState title="No return data" detail="No holdings with an unrealised gain value are stored." />
          ) : (
            <div className="space-y-3">
              {perfLabels.map((label, i) => {
                const v = perfValues[i] ?? 0;
                const max = Math.max(...perfValues.map((x) => Math.abs(x)), 1);
                return (
                  <div key={label} className="flex items-center gap-3">
                    <span className="w-28 shrink-0 text-xs text-gray-600 truncate">{label}</span>
                    <div className="flex-1 h-2 bg-gray-100 rounded overflow-hidden">
                      <div className="h-full bg-black" style={{ width: `${Math.abs(v) / max * 100}%` }} />
                    </div>
                    <span className="w-14 text-right text-xs tabular-nums text-black">{pct(v)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </Grid>

      <div className="mt-5">
        <Card title="Book statistics" subtitle="Derived from the live book — null values are shown as unavailable, never estimated">
          {bookStats.loading ? <Loading /> : bookStats.error ? (
            <ErrorState error={bookStats.error} onRetry={bookStats.reload} />
          ) : (
            <DataTable
              columns={[
                { key: 'metric', label: 'Metric' },
                { key: 'value', label: 'Value', align: 'right' },
              ]}
              rows={[
                { metric: 'Total clients', value: bookStats.data?.total_clients ?? '—' },
                { metric: 'Family offices', value: bookStats.data?.family_offices ?? '—' },
                { metric: 'Average AUM', value: money(bookStats.data?.avg_aum) },
                { metric: 'Meetings month to date', value: bookStats.data?.meetings_mtd ?? '—' },
                { metric: 'Net new assets YTD', value: bookStats.data?.net_new_assets_ytd == null ? 'Not available (no cash-flow ledger)' : money(bookStats.data.net_new_assets_ytd) },
                { metric: 'Data as of', value: bookStats.data?.as_of ?? '—' },
              ]}
            />
          )}
        </Card>
      </div>
    </PageShell>
  );
}
