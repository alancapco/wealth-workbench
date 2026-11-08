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
  value_local: number;
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
  rates_timestamp: string;
  base_currency: string;
}

const CURRENCY_COLORS: Record<string, string> = {
  HKD: 'bg-red-500',
  USD: 'bg-green-500',
  SGD: 'bg-blue-500',
  EUR: 'bg-purple-500',
  JPY: 'bg-orange-500',
  GBP: 'bg-indigo-500',
  CNY: 'bg-pink-500',
  AUD: 'bg-teal-500',
};

const CURRENCY_TEXT: Record<string, string> = {
  HKD: 'text-red-600',
  USD: 'text-green-600',
  SGD: 'text-blue-600',
  EUR: 'text-purple-600',
  JPY: 'text-orange-600',
  GBP: 'text-indigo-600',
  CNY: 'text-pink-600',
  AUD: 'text-teal-600',
};

const FALLBACK_DATA: CurrencyExposureResponse = {
  currencies: [
    { currency: 'HKD', value_local: 235600000, value_usd_millions: 30.1, allocation_pct: 66.6, holdings_count: 4, fx_rate: 7.84 },
    { currency: 'USD', value_local: 15100000, value_usd_millions: 15.1, allocation_pct: 33.4, holdings_count: 2, fx_rate: 1.00 },
  ],
  fx_rates: [
    { currency: 'HKD', rate: 7.84 },
    { currency: 'SGD', rate: 1.28 },
    { currency: 'EUR', rate: 0.90 },
    { currency: 'JPY', rate: 147.5 },
    { currency: 'GBP', rate: 0.76 },
  ],
  rates_timestamp: new Date().toISOString(),
  base_currency: 'USD',
};

function formatTimestamp(iso: string): string {
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
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    demoClientApi.list()
      .then((res) => {
        const list = res.data?.data ?? res.data;
        setClients(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        setOffline(true);
        setClients([{ id: 'demo-001', name: 'Kenneth Wong', aum_usd_millions: 45.2 }]);
      })
      .finally(() => setLoadingClients(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoadingData(true);
    demoClientApi.currencyExposure(selectedId)
      .then((res) => {
        const d = res.data?.data ?? res.data;
        setData(d);
      })
      .catch(() => {
        setOffline(true);
        setData(FALLBACK_DATA);
      })
      .finally(() => setLoadingData(false));
  }, [selectedId]);

  const maxUsd = data ? Math.max(...data.currencies.map((c) => c.value_usd_millions)) : 1;

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex items-center gap-4 shrink-0">
        <div>
          <h1 className="text-lg font-bold">Currency Exposure</h1>
          <p className="text-gray-400 text-sm">Live FX from FreeCurrencyAPI</p>
        </div>
        {offline && (
          <span className="ml-auto text-xs bg-yellow-900 text-yellow-300 px-3 py-1 rounded-full">
            Backend offline — showing sample data
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

        {selectedId && !loadingData && data && (
          <div className="space-y-6">
            {/* FX Rate banner */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-700">Live FX Rates (vs USD)</h2>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                    Live
                  </span>
                  <span className="text-xs text-gray-400">Rates as of {formatTimestamp(data.rates_timestamp)}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.fx_rates.map((r) => (
                  <div key={r.currency} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5">
                    <span className={`text-xs font-semibold ${CURRENCY_TEXT[r.currency] ?? 'text-gray-700'}`}>{r.currency}</span>
                    <span className="text-sm font-mono text-gray-800">{r.rate.toFixed(2)}</span>
                  </div>
                ))}
              </div>
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
                          {row.currency !== 'USD' ? row.value_local.toLocaleString() : `$${(row.value_local / 1_000_000).toFixed(1)}M`}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-gray-900">${row.value_usd_millions.toFixed(1)}M</td>
                        <td className="px-4 py-3 text-right text-gray-700">{row.allocation_pct.toFixed(1)}%</td>
                        <td className="px-4 py-3 text-right text-gray-500">{row.holdings_count}</td>
                        <td className="px-4 py-3 text-right font-mono text-gray-700">{row.fx_rate.toFixed(2)}</td>
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
                Rates powered by FreeCurrencyAPI · Updated hourly
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
