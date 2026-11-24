'use client';

import { useState, useEffect } from 'react';
import { demoClientApi } from '@/lib/api';

interface DemoClient {
  id: string;
  name: string;
  aum_usd_millions: number;
}

interface CurrencyRow {
  currency: string;
  value_local: number | null;
  value_usd_millions: number;
  allocation_pct: number;
  holdings_count: number;
  fx_rate: number;
}

interface FxRate {
  currency: string;
  rate: number;
}

interface CurrencyExposureResponse {
  currencies: CurrencyRow[];
  fx_rates: FxRate[];
  rates_as_of: string;
  base_currency: string;
  rates_source?: string | null;
  rates_is_live?: boolean | null;
  rates_note?: string | null;
}

const fmt = (v: number | null | undefined, digits = 1) =>
  typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : '—';

// Monochrome scale only — keeps the existing Capco palette.
const CURRENCY_COLORS: Record<string, string> = {
  HKD: 'bg-black',
  USD: 'bg-gray-800',
  SGD: 'bg-gray-600',
  EUR: 'bg-gray-400',
  JPY: 'bg-gray-300',
  GBP: 'bg-gray-200',
  CNY: 'bg-gray-500',
  AUD: 'bg-gray-700',
};

const CURRENCY_TEXT: Record<string, string> = {
  HKD: 'text-black',
  USD: 'text-gray-800',
  SGD: 'text-gray-700',
  EUR: 'text-gray-600',
  JPY: 'text-gray-600',
  GBP: 'text-gray-500',
  CNY: 'text-gray-600',
  AUD: 'text-gray-700',
};

function formatTimestamp(iso: string): string {
  if (!iso) return 'date unavailable';
  // The currency endpoint reports an as-of date, not a full timestamp.
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-SG', { timeZone: 'Asia/Singapore', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' SGT';
  } catch {
    return iso;
  }
}

export default function CurrencyPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [data, setData] = useState<CurrencyExposureResponse | null>(null);
  const [loadingClients, setLoadingClients] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [dataError, setDataError] = useState(false);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    demoClientApi.list()
      .then((res) => {
        const raw = res.data?.data ?? res.data;
        const list = Array.isArray(raw) ? raw : raw?.clients ?? [];
        setClients(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        setOffline(true);
        setClients([]);
      })
      .finally(() => setLoadingClients(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoadingData(true);
    setDataError(false);
    demoClientApi.currencyExposure(selectedId)
      .then((res) => {
        const d: any = res.data?.data ?? res.data;
        // The live endpoint returns currency_breakdown + a rates_used map; the
        // screen's view model uses a flat currency list and a rate array.
        setData({
          currencies: (Array.isArray(d?.currency_breakdown) ? d.currency_breakdown : []).map((r: any) => ({
            currency: r.currency,
            value_local: r.value_in_currency_millions ?? null,
            value_usd_millions: Number(r.value_usd_millions) || 0,
            allocation_pct: Number(r.allocation_pct) || 0,
            holdings_count: Number(r.holdings_count) || 0,
            fx_rate: Number(r.fx_rate) || 1,
          })),
          fx_rates: Object.entries(d?.rates_used ?? {}).map(([currency, rate]) => ({
            currency,
            rate: Number(rate),
          })),
          // A static fallback has no dated market snapshot, so do not fall back
          // to the report date and present it as a rate timestamp.
          rates_as_of: d?.rates_as_of ?? (d?.rates_is_live === false ? '' : d?.as_of_date ?? ''),
          base_currency: d?.base_currency ?? 'USD',
          rates_source: d?.rates_source ?? d?.rate_source ?? d?.source ?? null,
          rates_is_live: typeof d?.rates_is_live === 'boolean' ? d.rates_is_live : (d?.is_live ?? null),
          rates_note: d?.rates_note ?? null,
        });
      })
      .catch(() => {
        setOffline(true);
        setDataError(true);
        setData(null);
      })
      .finally(() => setLoadingData(false));
  }, [selectedId]);

  const maxUsd = data?.currencies.length
    ? Math.max(...data.currencies.map((c) => c.value_usd_millions), 1)
    : 1;

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex items-center gap-4 shrink-0">
        <div>
          <h1 className="text-lg font-bold">Currency Exposure</h1>
          <p className="text-gray-400 text-sm">Currency split for the selected client</p>
        </div>
        {offline && (
          <span className="ml-auto text-xs bg-gray-800 text-white px-3 py-1 rounded-full">
            Backend unavailable — no data displayed
          </span>
        )}
      </header>

      <div className="p-6 max-w-5xl mx-auto w-full">
        {/* Client selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Client</label>
          {loadingClients ? (
            <div className="w-6 h-6 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          ) : (
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full max-w-xs border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-black"
            >
              <option value="">— Choose a client —</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name} (${c.aum_usd_millions.toFixed(1)}M)</option>
              ))}
            </select>
          )}
        </div>

        {!selectedId && (
          <div className="text-gray-400 text-center mt-16">Select a client to view currency exposure</div>
        )}

        {selectedId && loadingData && (
          <div className="flex justify-center mt-16">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          </div>
        )}

        {selectedId && !loadingData && dataError && (
          <div className="border border-gray-300 bg-white rounded-xl p-4 text-sm text-gray-700">
            Currency exposure could not be loaded. Verify the backend is running, then select the client again.
          </div>
        )}

        {selectedId && !loadingData && !dataError && data && data.currencies.length === 0 && (
          <div className="border border-gray-200 bg-white rounded-xl p-4 text-sm text-gray-600">
            No currency exposure data is recorded for this client.
          </div>
        )}

        {selectedId && !loadingData && data && data.currencies.length > 0 && (
          <div className="space-y-6">
            {/* FX Rate banner */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-700">FX Rates (vs {data.base_currency})</h2>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  {data.rates_is_live === true && (
                    <span className="flex items-center gap-1 text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full font-medium">
                      <span className="w-1.5 h-1.5 bg-gray-800 rounded-full" />
                      Live
                    </span>
                  )}
                  {data.rates_is_live === false && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
                      Static reference rates
                    </span>
                  )}
                  <span className="text-xs text-gray-400">
                    {data.rates_is_live === false
                      ? 'No dated market snapshot'
                      : `Rates as of ${formatTimestamp(data.rates_as_of)}`}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.fx_rates.map((r) => (
                  <div key={r.currency} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
                    <span className={`text-xs font-semibold ${CURRENCY_TEXT[r.currency] ?? 'text-gray-700'}`}>{r.currency}</span>
                    <span className="text-sm font-mono text-gray-800">{fmt(r.rate, 2)}</span>
                  </div>
                ))}
              </div>
              {data.rates_note && (
                <p className="mt-3 text-xs text-gray-500">{data.rates_note}</p>
              )}
            </div>

            {/* Currency breakdown table */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <h2 className="text-sm font-semibold text-gray-700">Currency Breakdown</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Currency</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Value (Local)</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Value (USD M)</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Allocation %</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Holdings</th>
                      <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">FX Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.currencies.map((row) => (
                      <tr key={row.currency} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`w-3 h-3 rounded-sm ${CURRENCY_COLORS[row.currency] ?? 'bg-gray-400'}`} />
                            <span className="font-semibold text-gray-900">{row.currency}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700 font-mono text-xs">
                          {row.value_local === null ? '—' : `${fmt(row.value_local, 1)}M`}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-gray-900">${fmt(row.value_usd_millions, 1)}M</td>
                        <td className="px-4 py-3 text-right text-gray-700">{fmt(row.allocation_pct, 1)}%</td>
                        <td className="px-4 py-3 text-right text-gray-500">{row.holdings_count}</td>
                        <td className="px-4 py-3 text-right font-mono text-gray-700">{fmt(row.fx_rate, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Visual bar chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Allocation by Currency</h2>
              <div className="space-y-3">
                {data.currencies.map((row) => (
                  <div key={row.currency} className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-gray-600 w-10 shrink-0">{row.currency}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${CURRENCY_COLORS[row.currency] ?? 'bg-gray-400'} transition-all duration-500`}
                        style={{ width: `${(row.value_usd_millions / maxUsd) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-16 text-right shrink-0">
                      ${row.value_usd_millions.toFixed(1)}M ({row.allocation_pct.toFixed(1)}%)
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-4">
                {data.rates_source ? `Rate source: ${data.rates_source}` : 'FX rates'} ·{' '}
                {data.rates_is_live === false
                  ? 'static reference rates, no dated snapshot'
                  : `as of ${formatTimestamp(data.rates_as_of)}`} · base {data.base_currency}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
