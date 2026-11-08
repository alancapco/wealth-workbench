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
  color: string;
}

interface PeerAllocationRow {
  asset_class: string;
  allocation_pct: number;
  color: string;
}

interface InvestorsLikeMeResponse {
  client_allocation: AllocationRow[];
  peer_allocation: PeerAllocationRow[];
  peer_count: number;
  peer_profile: string;
  comparison_notes: string[];
  insufficient_peers: boolean;
}

const ASSET_CLASS_COLORS: Record<string, string> = {
  Equities: 'bg-blue-500',
  'Fixed Income': 'bg-green-500',
  Alternatives: 'bg-purple-500',
  Cash: 'bg-gray-400',
  'Real Estate': 'bg-orange-500',
};

const FALLBACK_DATA: InvestorsLikeMeResponse = {
  client_allocation: [
    { asset_class: 'Equities', allocation_pct: 45, color: '#3b82f6' },
    { asset_class: 'Fixed Income', allocation_pct: 35, color: '#22c55e' },
    { asset_class: 'Alternatives', allocation_pct: 12, color: '#a855f7' },
    { asset_class: 'Cash', allocation_pct: 8, color: '#9ca3af' },
  ],
  peer_allocation: [
    { asset_class: 'Equities', allocation_pct: 40, color: '#3b82f6' },
    { asset_class: 'Fixed Income', allocation_pct: 38, color: '#22c55e' },
    { asset_class: 'Alternatives', allocation_pct: 15, color: '#a855f7' },
    { asset_class: 'Cash', allocation_pct: 7, color: '#9ca3af' },
  ],
  peer_count: 4,
  peer_profile: 'Based on clients with Moderate risk, $35M–$55M AUM range, in APAC region',
  comparison_notes: [
    'Your equity allocation is 5% above the peer average — slightly higher growth exposure.',
    'Fixed income allocation is in line with peers; consider slightly increasing for defensive positioning.',
    'Alternative investments are below peers — room to diversify for uncorrelated returns.',
  ],
  insufficient_peers: false,
};

const RISK_COLORS: Record<string, string> = {
  Conservative: 'bg-blue-100 text-blue-800',
  Moderate: 'bg-yellow-100 text-yellow-800',
  'Moderate-Aggressive': 'bg-orange-100 text-orange-800',
  Aggressive: 'bg-red-100 text-red-800',
};

export default function InvestorsLikeMePage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedClient, setSelectedClient] = useState<DemoClient | null>(null);
  const [data, setData] = useState<InvestorsLikeMeResponse | null>(null);
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
        setClients([{ id: 'demo-001', name: 'Kenneth Wong', aum_usd_millions: 45.2, risk_profile: 'Moderate' }]);
      })
      .finally(() => setLoadingClients(false));
  }, []);

  const handleSelect = (clientId: string) => {
    const client = clients.find((c) => c.id === clientId) ?? null;
    setSelectedClient(client);
    if (!client) { setData(null); return; }
    setLoadingData(true);
    demoClientApi.investorsLikeMe(client.id)
      .then((res) => {
        const d = res.data?.data ?? res.data;
        setData(d);
      })
      .catch(() => {
        setOffline(true);
        setData(FALLBACK_DATA);
      })
      .finally(() => setLoadingData(false));
  };

  const allAssetClasses = data
    ? Array.from(new Set([...data.client_allocation.map((r) => r.asset_class), ...data.peer_allocation.map((r) => r.asset_class)]))
    : [];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex items-center gap-4 shrink-0">
        <div>
          <h1 className="text-lg font-bold">Investors Like Me</h1>
          <p className="text-gray-400 text-sm">Peer Allocation Benchmark</p>
        </div>
        {offline && (
          <span className="ml-auto text-xs bg-yellow-900 text-yellow-300 px-3 py-1 rounded-full">
            Backend offline — showing sample data
          </span>
        )}
      </header>

      <div className="p-6 max-w-5xl mx-auto w-full">
        <p className="text-sm text-gray-600 mb-4">
          Compare your client&apos;s portfolio allocation against anonymized peers with similar risk profiles and wealth levels.
        </p>

        {/* Client selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Client</label>
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
                <option key={c.id} value={c.id}>{c.name} (${c.aum_usd_millions.toFixed(1)}M)</option>
              ))}
            </select>
          )}
        </div>

        {!selectedClient && (
          <div className="text-gray-400 text-center mt-16">Select a client to see peer comparison</div>
        )}

        {selectedClient && loadingData && (
          <div className="flex justify-center mt-16">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
          </div>
        )}

        {selectedClient && !loadingData && data && (
          <div className="space-y-5">
            {/* Client info card */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-4">
              <div>
                <p className="font-semibold text-gray-900">{selectedClient.name}</p>
                <p className="text-sm text-gray-500">${selectedClient.aum_usd_millions.toFixed(1)}M AUM</p>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${RISK_COLORS[selectedClient.risk_profile] ?? 'bg-gray-100 text-gray-700'}`}>
                {selectedClient.risk_profile}
              </span>
            </div>

            {/* Insufficient peers warning */}
            {data.insufficient_peers && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="text-sm text-yellow-800 font-medium">Insufficient peer data for reliable comparison</p>
              </div>
            )}

            {/* Side-by-side comparison */}
            {!data.insufficient_peers && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Allocation Comparison</h2>
                <div className="grid grid-cols-2 gap-8">
                  {/* Your allocation */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Your Allocation</h3>
                    <div className="space-y-3">
                      {allAssetClasses.map((cls) => {
                        const mine = data.client_allocation.find((r) => r.asset_class === cls);
                        const peer = data.peer_allocation.find((r) => r.asset_class === cls);
                        const myPct = mine?.allocation_pct ?? 0;
                        const peerPct = peer?.allocation_pct ?? 0;
                        const delta = myPct - peerPct;

                        return (
                          <div key={cls}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-700">{cls}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-gray-900">{myPct.toFixed(1)}%</span>
                                {delta !== 0 && (
                                  <span className={`text-xs font-medium ${delta > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {delta > 0 ? '↑' : '↓'} {Math.abs(delta).toFixed(1)}%
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${ASSET_CLASS_COLORS[cls] ?? 'bg-gray-500'}`}
                                style={{ width: `${myPct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Peers avg */}
                  <div>
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Peers Avg. (N={data.peer_count} similar clients)
                    </h3>
                    <div className="space-y-3">
                      {allAssetClasses.map((cls) => {
                        const peer = data.peer_allocation.find((r) => r.asset_class === cls);
                        const peerPct = peer?.allocation_pct ?? 0;

                        return (
                          <div key={cls}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-gray-700">{cls}</span>
                              <span className="text-xs font-semibold text-gray-900">{peerPct.toFixed(1)}%</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                              <div
                                className={`h-full rounded-full opacity-60 ${ASSET_CLASS_COLORS[cls] ?? 'bg-gray-500'}`}
                                style={{ width: `${peerPct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Comparison notes */}
            {data.comparison_notes.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Comparison Notes</h2>
                <ul className="space-y-1.5">
                  {data.comparison_notes.map((note, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="text-gray-400 mt-0.5">•</span>
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Peer profile */}
            <p className="text-xs text-gray-400 px-1">{data.peer_profile}</p>
          </div>
        )}
      </div>
    </div>
  );
}
