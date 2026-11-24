'use client';

import { useState, useEffect } from 'react';
import { Moon, Circle } from 'lucide-react';
import { demoClientApi } from '@/lib/api';

interface DemoClient {
  id: string;
  name: string;
  aum_usd_millions: number;
  risk_profile: string;
  shariah_compliant: boolean;
}

interface Holding {
  asset_name: string;
  ticker: string | null;
  asset_class: string;
  currency: string;
  value_usd_millions: number | null;
  allocation_pct: number | null;
  gain_loss_pct: number | null;
  shariah_compliant: boolean;
}

const ASSET_CLASSES = ['All', 'Equities', 'Fixed Income', 'Alternatives', 'Cash', 'Real Estate'];

const fmt = (v: number | null, digits = 1) =>
  typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : '—';

// Monochrome risk styling — no additional colours are introduced.
const RISK_COLORS: Record<string, string> = {
  Conservative: 'bg-gray-100 text-gray-700',
  Moderate: 'bg-gray-200 text-gray-800',
  'Moderate-Aggressive': 'bg-gray-700 text-white',
  Aggressive: 'bg-black text-white',
};

export default function PortfolioPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<DemoClient | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [totalUsd, setTotalUsd] = useState(0);
  const [loadingClients, setLoadingClients] = useState(true);
  const [loadingHoldings, setLoadingHoldings] = useState(false);
  const [holdingsError, setHoldingsError] = useState(false);
  const [offline, setOffline] = useState(false);
  const [activeFilter, setActiveFilter] = useState('All');

  useEffect(() => {
    demoClientApi.list()
      .then((res) => {
        // /demo-clients wraps its list in { data: { clients } }; keep the
        // normalisation tolerant of either an envelope or a bare array.
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
    if (!selectedClient) return;
    setLoadingHoldings(true);
    setHoldingsError(false);
    // The detail endpoint is the only one that returns per-holding rows; the
    // asset-class endpoint returns aggregates, so it cannot fill this table.
    demoClientApi.get(selectedClient.id)
      .then((res) => {
        const detail: any = res.data?.data ?? res.data;
        const raw: any[] = Array.isArray(detail?.portfolio_holdings) ? detail.portfolio_holdings : [];
        const rows: Holding[] = raw.map((h) => ({
          asset_name: h.asset_name ?? '—',
          ticker: h.ticker ?? null,
          asset_class: h.asset_class ?? 'Other',
          currency: h.currency ?? 'USD',
          value_usd_millions: h.value_usd_millions ?? null,
          allocation_pct: h.allocation_pct ?? null,
          gain_loss_pct: h.unrealized_gain_pct ?? null,
          shariah_compliant: Boolean(h.is_shariah_compliant),
        }));
        setHoldings(rows);
        setTotalUsd(rows.reduce((s, h) => s + (h.value_usd_millions ?? 0), 0));
      })
      .catch(() => {
        setOffline(true);
        setHoldingsError(true);
        setHoldings([]);
        setTotalUsd(0);
      })
      .finally(() => setLoadingHoldings(false));
  }, [selectedClient]);

  const filtered = activeFilter === 'All'
    ? holdings
    : holdings.filter((h) => h.asset_class === activeFilter);

  const totalFiltered = filtered.reduce((s, h) => s + (h.value_usd_millions ?? 0), 0);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex items-center gap-4 shrink-0">
        <div>
          <h1 className="text-lg font-bold">Holdings in One Place</h1>
          <p className="text-gray-400 text-sm">RM Portfolio View</p>
        </div>
        {offline && (
          <span className="ml-auto text-xs bg-gray-800 text-white px-3 py-1 rounded-full">
            Backend unavailable — no data displayed
          </span>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 bg-white border-r border-gray-200 overflow-y-auto shrink-0">
          <div className="p-4 border-b border-gray-100">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Clients ({clients.length})</h2>
          </div>
          {loadingClients ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
            </div>
          ) : clients.length === 0 ? (
            <div className="p-4 text-xs text-gray-500">
              No portfolio clients loaded. Verify the backend is running and refresh the page.
            </div>
          ) : (
            <ul className="divide-y divide-gray-100">
              {clients.map((client) => (
                <li key={client.id}>
                  <button
                    onClick={() => { setSelectedClient(client); setActiveFilter('All'); }}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                      selectedClient?.id === client.id ? 'bg-gray-900 text-white hover:bg-gray-900' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-sm font-medium truncate ${selectedClient?.id === client.id ? 'text-white' : 'text-gray-900'}`}>
                        {client.name}
                      </span>
                      {client.shariah_compliant && (
                        <Moon size={14} className={selectedClient?.id === client.id ? 'text-gray-300' : 'text-gray-600'} />
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs ${selectedClient?.id === client.id ? 'text-gray-300' : 'text-gray-500'}`}>
                        ${client.aum_usd_millions.toFixed(1)}M
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        selectedClient?.id === client.id
                          ? 'bg-gray-700 text-gray-200'
                          : (RISK_COLORS[client.risk_profile] ?? 'bg-gray-100 text-gray-700')
                      }`}>
                        {client.risk_profile}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Main Panel */}
        <main className="flex-1 overflow-auto p-6">
          {!selectedClient ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Circle size={48} className="mb-4 opacity-30" />
              <p className="text-lg">Select a client to view their holdings</p>
            </div>
          ) : loadingHoldings ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
            </div>
          ) : holdingsError ? (
            <div className="border border-gray-300 bg-white rounded p-5 text-sm text-gray-700">
              Holdings could not be loaded. Verify the backend is running, then select the client again.
            </div>
          ) : holdings.length === 0 ? (
            <div className="border border-gray-200 bg-white rounded p-5 text-sm text-gray-600">
              No holdings are recorded for this client.
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedClient.name}</h2>
                  <p className="text-sm text-gray-500">
                    Total AUM: <span className="font-semibold text-gray-700">${totalUsd.toFixed(1)}M USD</span>
                    {' · '}{holdings.length} holdings
                  </p>
                </div>
                {selectedClient.shariah_compliant && (
                  <span className="flex items-center gap-1 text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full font-medium">
                    <Moon size={12} /> Shariah Portfolio
                  </span>
                )}
              </div>

              {/* Filter tabs */}
              <div className="flex gap-2 mb-4 flex-wrap">
                {ASSET_CLASSES.map((cls) => (
                  <button
                    key={cls}
                    onClick={() => setActiveFilter(cls)}
                    className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
                      activeFilter === cls
                        ? 'bg-black text-white'
                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    {cls}
                    {cls === 'All' ? ` (${holdings.length})` : ` (${holdings.filter(h => h.asset_class === cls).length})`}
                  </button>
                ))}
              </div>

              {/* Table */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {filtered.length === 0 ? (
                  <div className="p-6 text-center text-sm text-gray-500">
                    No holdings in {activeFilter} for this client.
                  </div>
                ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Asset Name</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Ticker</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Asset Class</th>
                        <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Currency</th>
                        <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Value (USD M)</th>
                        <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Alloc %</th>
                        <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Gain/Loss %</th>
                        <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Shariah</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filtered.map((h, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{h.asset_name}</td>
                          <td className="px-4 py-3 text-gray-500 font-mono text-xs">{h.ticker || '—'}</td>
                          <td className="px-4 py-3">
                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">{h.asset_class}</span>
                          </td>
                          <td className="px-4 py-3 text-gray-500">{h.currency}</td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            {h.value_usd_millions === null ? '—' : `$${fmt(h.value_usd_millions, 2)}M`}
                          </td>
                          <td className="px-4 py-3 text-right text-gray-700">
                            {h.allocation_pct === null ? '—' : `${fmt(h.allocation_pct)}%`}
                          </td>
                          <td className={`px-4 py-3 text-right font-semibold ${(h.gain_loss_pct ?? 0) >= 0 ? 'text-gray-900' : 'text-gray-500'}`}>
                            {h.gain_loss_pct === null ? '—' : `${h.gain_loss_pct > 0 ? '+' : ''}${fmt(h.gain_loss_pct)}%`}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {h.shariah_compliant ? (
                              <Moon size={14} className="text-gray-600 mx-auto" />
                            ) : (
                              <span className="text-gray-300">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      {/* Total row */}
                      <tr className="bg-gray-50 font-semibold border-t-2 border-gray-300">
                        <td className="px-4 py-3 text-gray-900" colSpan={4}>Total ({filtered.length} holdings)</td>
                        <td className="px-4 py-3 text-right text-gray-900">${totalFiltered.toFixed(2)}M</td>
                        <td className="px-4 py-3" colSpan={3} />
                      </tr>
                    </tbody>
                  </table>
                </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
