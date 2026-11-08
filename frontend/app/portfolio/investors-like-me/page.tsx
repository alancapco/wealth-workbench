'use client';

import { useState, useEffect } from 'react';
import { demoClientApi } from '@/lib/api';

interface DemoClient {
  id: string;
  name: string;
  aum_usd_millions: number;
  risk_profile: string;
}

interface AllocationRow {
  asset_class: string;
  allocation_pct: number;
}

interface ApiResponse {
  client_id: string;
  client_name: string;
  your_allocation: AllocationRow[];
  peer_avg_allocation: AllocationRow[];
  peer_count: number;
  comparison_notes: string[];
}

const ASSET_COLORS: Record<string, string> = {
  Equities: '#3b82f6',
  'Fixed Income': '#22c55e',
  Alternatives: '#a855f7',
  Cash: '#94a3b8',
  'Real Estate': '#f97316',
};

const RISK_BADGE: Record<string, string> = {
  Conservative: 'bg-blue-100 text-blue-800',
  Moderate: 'bg-amber-100 text-amber-800',
  Balanced: 'bg-emerald-100 text-emerald-800',
  Aggressive: 'bg-red-100 text-red-800',
};

export default function InvestorsLikeMePage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<DemoClient | null>(null);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loadingClients, setLoadingClients] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    demoClientApi
      .list()
      .then((res) => {
        const raw = res.data?.data ?? res.data;
        const list = raw?.clients ?? raw;
        setClients(Array.isArray(list) ? list : []);
      })
      .catch(() => {
        setOffline(true);
        setClients([
          { id: 'demo-001', name: 'Kenneth Wong', aum_usd_millions: 45.2, risk_profile: 'Moderate' },
          { id: 'demo-002', name: 'Ahmad Rahman', aum_usd_millions: 32.8, risk_profile: 'Conservative' },
          { id: 'demo-003', name: 'Tan Family Office', aum_usd_millions: 120.5, risk_profile: 'Balanced' },
        ]);
      })
      .finally(() => setLoadingClients(false));
  }, []);

  const handleSelect = (clientId: string) => {
    const client = clients.find((c) => c.id === clientId) ?? null;
    setSelectedClient(client);
    if (!client) {
      setData(null);
      return;
    }
    setLoadingData(true);
    demoClientApi
      .investorsLikeMe(client.id)
      .then((res) => {
        const d = res.data?.data ?? res.data;
        setData(d);
      })
      .catch(() => {
        setOffline(true);
        setData(null);
      })
      .finally(() => setLoadingData(false));
  };

  // Build unified asset class list from both sides
  const allClasses: string[] = data
    ? Array.from(
        new Set([
          ...data.your_allocation.map((r) => r.asset_class),
          ...data.peer_avg_allocation.map((r) => r.asset_class),
        ]),
      )
    : [];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Black header */}
      <header className="bg-black text-white px-6 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold">Investors Like Me</h1>
          <p className="text-gray-400 text-sm">Peer Allocation Benchmark</p>
        </div>
        {offline && (
          <span className="text-xs bg-yellow-900 text-yellow-300 px-3 py-1 rounded-full">
            Backend offline — showing sample data
          </span>
        )}
      </header>

      <div className="p-6 max-w-4xl mx-auto w-full">
        <p className="text-sm text-gray-600 mb-5">
          Compare your client&apos;s portfolio allocation against anonymized peers with similar risk
          profiles and wealth levels.
        </p>

        {/* Client selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Select Client</label>
          {loadingClients ? (
            <div className="w-6 h-6 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          ) : (
            <select
              value={selectedClient?.id ?? ''}
              onChange={(e) => handleSelect(e.target.value)}
              className="w-full max-w-xs border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-black"
            >
              <option value="">— Choose a client —</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (${c.aum_usd_millions.toFixed(1)}M)
                </option>
              ))}
            </select>
          )}
        </div>

        {!selectedClient && (
          <div className="text-gray-400 text-center mt-20">Select a client to see peer comparison</div>
        )}

        {selectedClient && loadingData && (
          <div className="flex justify-center mt-20">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          </div>
        )}

        {selectedClient && !loadingData && data && (
          <div className="space-y-5">
            {/* Client info card */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
              <div>
                <p className="font-semibold text-gray-900">{data.client_name}</p>
                <p className="text-sm text-gray-500">
                  ${selectedClient.aum_usd_millions.toFixed(1)}M AUM
                </p>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded font-medium ${
                  RISK_BADGE[selectedClient.risk_profile] ?? 'bg-gray-100 text-gray-700'
                }`}
              >
                {selectedClient.risk_profile}
              </span>
              <span className="ml-auto text-xs text-gray-400">
                Compared against {data.peer_count} similar {data.peer_count === 1 ? 'peer' : 'peers'}
              </span>
            </div>

            {/* Side-by-side comparison */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Allocation Comparison</h2>
              <div className="grid grid-cols-2 gap-8">
                {/* Your allocation */}
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
                    Your Allocation
                  </h3>
                  <div className="space-y-3.5">
                    {allClasses.map((cls) => {
                      const mine = data.your_allocation.find((r) => r.asset_class === cls);
                      const peer = data.peer_avg_allocation.find((r) => r.asset_class === cls);
                      const myPct = mine?.allocation_pct ?? 0;
                      const peerPct = peer?.allocation_pct ?? 0;
                      const delta = myPct - peerPct;

                      return (
                        <div key={cls}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-700">{cls}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-gray-900">
                                {myPct.toFixed(1)}%
                              </span>
                              {delta !== 0 && (
                                <span
                                  className={`text-xs font-medium ${
                                    delta > 0 ? 'text-green-600' : 'text-red-600'
                                  }`}
                                >
                                  {delta > 0 ? '↑' : '↓'} {Math.abs(delta).toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.max(myPct, 2)}%`,
                                backgroundColor: ASSET_COLORS[cls] ?? '#6b7280',
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Peers average */}
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
                    Peers Avg. (N={data.peer_count})
                  </h3>
                  <div className="space-y-3.5">
                    {allClasses.map((cls) => {
                      const peer = data.peer_avg_allocation.find((r) => r.asset_class === cls);
                      const peerPct = peer?.allocation_pct ?? 0;

                      return (
                        <div key={cls}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-700">{cls}</span>
                            <span className="text-xs font-semibold text-gray-900">
                              {peerPct.toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                            <div
                              className="h-full rounded-full opacity-50 transition-all duration-500"
                              style={{
                                width: `${Math.max(peerPct, 2)}%`,
                                backgroundColor: ASSET_COLORS[cls] ?? '#6b7280',
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Comparison notes */}
            {data.comparison_notes.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Key Differences</h2>
                <ul className="space-y-2">
                  {data.comparison_notes.map((note, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-gray-400 mt-0.5">•</span>
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disclaimer */}
            <p className="text-xs text-gray-400 px-1">
              Peer data is anonymized and aggregated. No individual client holdings are exposed.
              Comparison based on risk profile and AUM range (&plusmn;50%).
            </p>
          </div>
        )}

        {selectedClient && !loadingData && !data && offline && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
            Backend offline. Start the backend with <code className="bg-yellow-100 px-1 rounded">cd backend && uv run uvicorn app.main:app --port 8000</code> to see live data.
          </div>
        )}
      </div>
    </div>
  );
}
