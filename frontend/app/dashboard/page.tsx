'use client';

import React, { useEffect, useState } from 'react';
import { dashboardApi, marketApi } from '@/lib/api';
import AllocationChart from '@/components/AllocationChart';
import PerformanceChart from '@/components/PerformanceChart';
import BriefModal from '@/components/BriefModal';
import FamilyGraphModal from '@/components/FamilyGraphModal';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [briefModalOpen, setBriefModalOpen] = useState(false);
  const [familyGraphOpen, setFamilyGraphOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<{ id: string; name: string } | null>(null);

  useEffect(() => {
    loadDashboard();

    // Update clock every second
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [myDayRes, allocationRes, performanceRes] = await Promise.all([
        dashboardApi.getMyDay(),
        dashboardApi.getAllocation(),
        dashboardApi.getPerformanceTrend(),
      ]);

      setDashboardData({
        myDay: myDayRes.data,
        allocation: allocationRes.data,
        performance: performanceRes.data,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-SG', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'Asia/Singapore'
    }) + ' SGT';
  };

  const formatNewsTime = (value?: string) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString('en-SG', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Singapore',
    }) + ' SGT';
  };

  const handleOpenBrief = (clientId: string, clientName: string = 'Kenneth Wong') => {
    setSelectedClient({ id: clientId, name: clientName });
    setBriefModalOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  const kpis = dashboardData?.myDay?.kpis || {};
  const allocation = dashboardData?.allocation || {};
  const performance = dashboardData?.performance || {};
  const rankedClients = dashboardData?.myDay?.ranked_clients || [];
  const marketNews = dashboardData?.myDay?.market_news || [];

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Black header bar within content area */}
      <div className="h-16 bg-black w-full">
        <div className="max-w-[1920px] mx-auto h-full px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img
              src="/capco-logo.png"
              alt="Capco"
              className="h-9 w-auto"
            />
            <span className="text-white text-sm uppercase pl-4 border-l border-gray-600">
              Wealth Workbench
            </span>
          </div>

          <div className="flex flex-col items-center">
            <div className="px-4 py-1 bg-green-600 text-white text-xs font-semibold uppercase rounded">
              ● LIVE MARKET DATA · {formatTime(currentTime)}
            </div>
            <div className="text-xs text-gray-400 mt-2 flex items-center gap-3">
              <div className="flex items-center gap-2 bg-white px-3 py-1 rounded">
                <span className="text-green-600 font-bold">1</span>
                <span className="text-black font-semibold">Rank Clients</span>
              </div>
              <span className="text-gray-600">→</span>
              <div className="flex items-center gap-2 px-3 py-1 rounded">
                <span className="text-gray-400 font-bold">2</span>
                <span className="text-gray-500">Generate Brief</span>
              </div>
              <span className="text-gray-600">→</span>
              <div className="flex items-center gap-2 px-3 py-1 rounded">
                <span className="text-gray-400 font-bold">3</span>
                <span className="text-gray-500">Meeting & Capture</span>
              </div>
              <span className="text-gray-600">→</span>
              <div className="flex items-center gap-2 px-3 py-1 rounded">
                <span className="text-gray-400 font-bold">4</span>
                <span className="text-gray-500">Review & Approve</span>
              </div>
              <span className="ml-4 text-gray-500">Workflow ID: 8f21a4b2</span>
            </div>
          </div>

          <div className="text-right">
            <div className="text-white text-sm font-medium">Sarah Chen</div>
            <div className="text-gray-400 text-xs uppercase">Relationship Manager</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pb-12 px-8 max-w-[1920px] mx-auto">
        <div className="pt-12 pb-6">
          <h1 className="text-4xl font-light mb-2">Good Morning, Sarah</h1>
          <p className="text-lg text-gray-500">
            Tuesday, 16 March 2026 · {formatTime(currentTime)}
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded p-6 hover:border-gray-400 hover:shadow-lg transition-all">
            <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2">
              Total AUM Under Management
            </h3>
            <div className="text-3xl font-light mb-1">
              ${(kpis.total_aum / 1e6).toFixed(1)}M
            </div>
            <div className="text-sm text-gray-600">Across {kpis.total_clients} clients</div>
            <div className="text-sm text-green-700 font-medium mt-2">
              ↑ $12.3M this month (+2.9%)
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-6 hover:border-gray-400 hover:shadow-lg transition-all">
            <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2">
              Today's Meetings
            </h3>
            <div className="text-3xl font-light mb-1">{kpis.meetings_today}</div>
            <div className="text-sm text-gray-600">Next at 10:00 AM</div>
            <div className="text-sm text-gray-700 mt-2">Kenneth Wong · Rebalancing</div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-6 hover:border-gray-400 hover:shadow-lg transition-all">
            <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2">
              Open Actions
            </h3>
            <div className="text-3xl font-light mb-1">{kpis.open_actions}</div>
            <div className="text-sm text-gray-600">Requiring attention</div>
            <div className="text-sm text-red-700 font-medium mt-2">
              {kpis.actions_overdue || 0} overdue
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-6 hover:border-gray-400 hover:shadow-lg transition-all">
            <h3 className="text-xs uppercase text-gray-500 font-semibold mb-2">
              Portfolio Performance
            </h3>
            <div className="text-3xl font-light mb-1">+{kpis.ytd_performance}%</div>
            <div className="text-sm text-gray-600">YTD weighted average</div>
            <div className="text-sm text-green-700 font-medium mt-2">
              ↑ Benchmark +1.2%
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded p-6">
            <h2 className="text-lg font-semibold mb-4 pb-3 border-b border-gray-200">
              Book Allocation Overview
            </h2>
            <AllocationChart data={allocation} />
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-black rounded"></div>
                  <span>Equities</span>
                </div>
                <span className="font-semibold">{allocation.equities}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-600 rounded"></div>
                  <span>Fixed Income</span>
                </div>
                <span className="font-semibold">{allocation.fixed_income}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-300 rounded"></div>
                  <span>Cash</span>
                </div>
                <span className="font-semibold">{allocation.cash}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-6">
            <h2 className="text-lg font-semibold mb-4 pb-3 border-b border-gray-200">
              YTD Performance Trend
            </h2>
            <PerformanceChart data={performance} />
          </div>
        </div>

        {/* Schedule and News */}
        <div className="grid grid-cols-[2fr_1fr] gap-6 mb-8">
          <div className="bg-white border border-gray-200 rounded p-6">
            <h2 className="text-lg font-semibold mb-4 pb-3 border-b border-gray-200">
              Today's Schedule
            </h2>

            <div className="bg-orange-50 -mx-6 px-6 py-4 border-b border-gray-100">
              <div className="flex gap-4">
                <div className="font-semibold min-w-[80px]">10:00 AM</div>
                <div className="flex-1">
                  <div className="font-semibold mb-1">Kenneth Wong · HKD 45.2M AUM</div>
                  <div className="text-sm text-gray-600 mb-3">
                    Rebalancing discussion — Portfolio drifted 6% from target (HSBC +2.3% market event)
                  </div>
                  <button
                    onClick={() => handleOpenBrief(rankedClients[0]?.client_id || 'demo', rankedClients[0]?.name || 'Kenneth Wong')}
                    className="px-4 py-2 bg-black text-white text-xs uppercase font-medium rounded hover:bg-gray-800 transition-colors"
                  >
                    Open Brief & Prepare
                  </button>
                </div>
              </div>
            </div>

            <div className="py-4 border-b border-gray-100 flex gap-4">
              <div className="font-semibold min-w-[80px]">1:00 PM</div>
              <div className="flex-1">
                <div className="font-semibold mb-1">Ahmad Rahman · SGD 32.8M AUM</div>
                <div className="text-sm text-gray-600 mb-2">
                  Annual review — Faith-based investing focus, zakat calculation
                </div>
                <button
                  onClick={() => handleOpenBrief(rankedClients[1]?.client_id || 'demo', rankedClients[1]?.name || 'Ahmad Rahman')}
                  className="px-4 py-2 bg-black text-white text-xs uppercase font-medium rounded hover:bg-gray-800 transition-colors"
                >
                  Open Brief & Shariah Report
                </button>
              </div>
            </div>

            <div className="py-4 flex gap-4">
              <div className="font-semibold min-w-[80px]">3:30 PM</div>
              <div className="flex-1">
                <div className="font-semibold mb-1">Tan Family Office · SGD 120.5M AUM (7 entities)</div>
                <div className="text-sm text-gray-600 mb-2">
                  Quarterly family review — 4 members attending, consolidated reporting
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleOpenBrief(rankedClients[2]?.client_id || 'demo', rankedClients[2]?.name || 'Tan Family Office')}
                    className="px-4 py-2 bg-black text-white text-xs uppercase font-medium rounded hover:bg-gray-800 transition-colors"
                  >
                    Open Consolidated Brief
                  </button>
                  <button
                    onClick={() => setFamilyGraphOpen(true)}
                    className="px-4 py-2 border border-gray-400 text-gray-700 text-xs uppercase font-medium rounded hover:bg-gray-50 transition-colors"
                  >
                    View Family Graph
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded p-6">
            <h2 className="text-lg font-semibold mb-4 pb-3 border-b border-gray-200">
              Market News
            </h2>

            <div className="space-y-4">
              {marketNews.length === 0 && (
                <div className="text-sm text-gray-500">No market news available.</div>
              )}
              {marketNews.slice(0, 4).map((news: any) => (
                <div key={news.id || news.url} className="pb-3 border-b border-gray-100 last:border-0">
                  <div className="font-semibold text-sm mb-1">
                    {news.url ? (
                      <a href={news.url} target="_blank" rel="noreferrer" className="hover:underline">
                        {news.title}
                      </a>
                    ) : (
                      news.title
                    )}
                  </div>
                  {news.content && (
                    <div className="text-xs text-gray-500">{news.content}</div>
                  )}
                  <div className="mt-2">
                    <span className="inline-block px-2 py-1 bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded">
                      {news.source || 'Tiger Broker'}
                      {news.symbol ? ` · ${news.symbol}` : ''}
                      {news.timestamp ? ` · ${formatNewsTime(news.timestamp)}` : ''}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Priority Actions */}
        <div className="bg-white border border-gray-200 rounded p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4 pb-3 border-b border-gray-200">
            Priority Actions for Today
          </h2>

          <div className="space-y-3">
            <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded hover:bg-orange-100 cursor-pointer transition-all">
              <div className="font-semibold mb-1">1. Prepare rebalancing brief for Kenneth Wong</div>
              <div className="text-sm text-gray-700">
                Portfolio drift 6% due to HSBC +2.3% move · High confidence opportunity · Due before 10:00 AM
              </div>
            </div>

            <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded hover:bg-orange-100 cursor-pointer transition-all">
              <div className="font-semibold mb-1">2. Complete annual zakat calculation for Ahmad Rahman</div>
              <div className="text-sm text-gray-700">
                Shariah-compliant documentation required for 1:00 PM meeting
              </div>
            </div>

            <div className="bg-red-50 border-l-4 border-red-700 p-4 rounded hover:bg-red-100 cursor-pointer transition-all">
              <div className="font-semibold mb-1">3. Review overdue suitability profiles (2 clients)</div>
              <div className="text-sm text-gray-700">
                Li Wei (expired 10 Mar) · Chen Family (expired 08 Mar) · Blocking new trades
              </div>
            </div>

            <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded hover:bg-orange-100 cursor-pointer transition-all">
              <div className="font-semibold mb-1">4. Consolidate Tan Family reports across 7 entities</div>
              <div className="text-sm text-gray-700">
                Patriarch + 3 family members attending 3:30 PM review · Generation 2 & 3 views needed
              </div>
            </div>
          </div>
        </div>

        {/* Book Stats */}
        <div className="grid grid-cols-5 gap-8 bg-white border border-gray-200 rounded p-6 mb-8">
          <div className="text-center">
            <div className="text-xs uppercase text-gray-500 mb-2">Clients</div>
            <div className="text-2xl font-light">45</div>
          </div>
          <div className="text-center">
            <div className="text-xs uppercase text-gray-500 mb-2">Family Offices</div>
            <div className="text-2xl font-light">8</div>
          </div>
          <div className="text-center">
            <div className="text-xs uppercase text-gray-500 mb-2">Avg. AUM</div>
            <div className="text-2xl font-light">$9.5M</div>
          </div>
          <div className="text-center">
            <div className="text-xs uppercase text-gray-500 mb-2">Meetings (MTD)</div>
            <div className="text-2xl font-light">18</div>
          </div>
          <div className="text-center">
            <div className="text-xs uppercase text-gray-500 mb-2">Net New (YTD)</div>
            <div className="text-2xl font-light text-green-700">+$38M</div>
          </div>
        </div>

        {/* Black footer bar */}
        <div className="h-12 bg-black -mx-8 px-8 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-white text-xs uppercase font-medium">System Ready</span>
            <span className="px-3 py-1 bg-gray-900 text-white text-xs font-semibold uppercase rounded">
              SYNTHETIC DEMO DATA
            </span>
          </div>
          <div className="text-gray-500 text-xs">
            Demo environment • All data synthetic • Not for production use
          </div>
        </div>
      </div>

      {/* Brief Modal */}
      <BriefModal
        isOpen={briefModalOpen}
        onClose={() => setBriefModalOpen(false)}
        clientId={selectedClient?.id || ''}
        clientName={selectedClient?.name || ''}
      />

      {/* Family Graph Modal */}
      <FamilyGraphModal
        isOpen={familyGraphOpen}
        onClose={() => setFamilyGraphOpen(false)}
        clientName="Tan Family Office"
      />
    </div>
  );
}
