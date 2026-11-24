'use client';

import { useState, useEffect } from 'react';
import { demoClientApi } from '@/lib/api';
import { DatePicker } from '@/components/ui/date-picker';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';

interface DemoClient {
  id: string;
  name: string;
  aum_usd_millions: number;
}

interface Goal {
  name: string;
  target_usd_millions: number;
  target_date?: Date;
}

interface ProjectionYear {
  year: number;
  age: number;
  projected_value_usd_millions: number | null;
  real_corpus_usd_millions: number | null;
  inflation_adjusted_target_usd_millions: number | null;
}

interface PlanResult {
  projected_corpus_usd_millions: number | null;
  target_corpus_usd_millions: number;
  probability_of_success: number | null;
  gap_usd_millions: number | null;
  projection: ProjectionYear[];
  recommendations: string[];
  summary: string;
  gap_analysis: string;
  disclaimer: string;
  inflation_pct: number | null;
  inflation_adjusted_target_usd_millions: number | null;
  real_return_pct: number | null;
  real_projected_corpus_usd_millions: number | null;
  real_terms_gap_usd_millions: number | null;
}

const DEFAULT_PARAMS = {
  current_age: 52,
  retirement_age: 65,
  monthly_contribution: 50000,
  target_retirement_corpus: 80,
  assumed_annual_return: 6.5,
  inflation: 2.5,
};

const fmt = (v: number | null | undefined, digits = 1) =>
  typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : '—';

const num = (v: unknown) =>
  typeof v === 'number' && Number.isFinite(v) ? v : null;

export default function FuturePlannerPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [currentSavings, setCurrentSavings] = useState(0);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [goals, setGoals] = useState<Goal[]>([
    { name: '', target_usd_millions: 0, target_date: new Date(new Date().getFullYear() + 10, 0, 1) },
  ]);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [loadingClients, setLoadingClients] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
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
    const client = clients.find((c) => c.id === selectedId);
    if (client) {
      setCurrentSavings(client.aum_usd_millions);
    }
  }, [selectedId, clients]);

  const updateGoal = (i: number, field: keyof Goal, value: Goal[keyof Goal]) => {
    setGoals((prev) => prev.map((g, idx) => idx === i ? { ...g, [field]: value } : g));
  };

  const addGoal = () => {
    if (goals.length < 3) setGoals([...goals, { name: '', target_usd_millions: 0, target_date: new Date(new Date().getFullYear() + 15, 0, 1) }]);
  };

  const removeGoal = (i: number) => {
    setGoals((prev) => prev.filter((_, idx) => idx !== i));
  };

  const generatePlan = async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(false);
    setResult(null);

    try {
      const res = await demoClientApi.futurePlanner(selectedId, {
        current_age: params.current_age,
        retirement_age: params.retirement_age,
        current_savings_usd_millions: currentSavings,
        monthly_contribution_usd: params.monthly_contribution,
        target_retirement_corpus_usd_millions: params.target_retirement_corpus,
        assumed_annual_return_pct: params.assumed_annual_return,
        inflation_pct: params.inflation,
        goals: goals.filter((g) => g.name).map((g) => ({
          name: g.name,
          target_amount_usd_millions: g.target_usd_millions,
          target_year: g.target_date?.getFullYear() || new Date().getFullYear() + 10,
        })),
      });
      const payload: any = res.data?.data ?? res.data;
      const report: any = payload?.report ?? {};
      const projected = num(report.projected_corpus_usd_millions);
      setResult({
        projected_corpus_usd_millions: projected,
        target_corpus_usd_millions: params.target_retirement_corpus,
        probability_of_success: num(report.probability_of_success_pct),
        gap_usd_millions: projected === null
          ? null
          : Math.round((params.target_retirement_corpus - projected) * 100) / 100,
        projection: (Array.isArray(report.year_by_year) ? report.year_by_year : []).map((r: any) => ({
          year: r.year,
          age: r.age,
          projected_value_usd_millions: num(r.corpus_usd_millions),
          real_corpus_usd_millions: num(r.real_corpus_usd_millions),
          inflation_adjusted_target_usd_millions: num(r.inflation_adjusted_target_usd_millions),
        })),
        recommendations: Array.isArray(report.recommendations) ? report.recommendations : [],
        summary: report.summary || '',
        gap_analysis: report.gap_analysis || '',
        // The deterministic fallback labels itself; surface that plainly.
        disclaimer: [payload?.disclaimer, report._note].filter(Boolean).join(' '),
        inflation_pct: num(report.inflation_pct),
        inflation_adjusted_target_usd_millions: num(report.inflation_adjusted_target_usd_millions),
        real_return_pct: num(report.real_return_pct),
        real_projected_corpus_usd_millions: num(report.real_projected_corpus_usd_millions),
        real_terms_gap_usd_millions: num(report.real_terms_gap_usd_millions),
      });
    } catch {
      setError(true);
      setOffline(true);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const numInput = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black";

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 flex items-center gap-4 shrink-0">
        <div>
          <h1 className="text-lg font-bold">Future Planner</h1>
          <p className="text-gray-400 text-sm">AI-Powered Goal Simulation</p>
        </div>
        {offline && (
          <span className="ml-auto text-xs bg-gray-800 text-white px-3 py-1 rounded-full">
            Backend unavailable — no projection displayed
          </span>
        )}
      </header>

      <div className="flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto w-full">
        {/* Left panel: Inputs */}
        <div className="lg:w-96 shrink-0 bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
            {loadingClients ? (
              <div className="w-6 h-6 border-2 border-gray-300 border-t-black rounded-full animate-spin" />
            ) : (
              <Select value={selectedId || undefined} onValueChange={setSelectedId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a client" />
                </SelectTrigger>
                <SelectContent>
                  {clients.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {!loadingClients && clients.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">
                No portfolio clients loaded. Verify the backend is running and refresh the page.
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Current Age</label>
              <input type="number" value={params.current_age} onChange={(e) => setParams({ ...params, current_age: +e.target.value })} className={numInput} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Retirement Age</label>
              <input type="number" value={params.retirement_age} onChange={(e) => setParams({ ...params, retirement_age: +e.target.value })} className={numInput} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Current Savings (USD M)</label>
            <input type="number" step="0.1" value={currentSavings || ''} onChange={(e) => setCurrentSavings(+e.target.value)} className={numInput} placeholder="Auto-filled from client AUM" />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Monthly Contribution (USD)</label>
            <input type="number" value={params.monthly_contribution} onChange={(e) => setParams({ ...params, monthly_contribution: +e.target.value })} className={numInput} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Target Corpus (USD M)</label>
              <input type="number" step="0.1" value={params.target_retirement_corpus} onChange={(e) => setParams({ ...params, target_retirement_corpus: +e.target.value })} className={numInput} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Annual Return %</label>
              <input type="number" step="0.1" value={params.assumed_annual_return} onChange={(e) => setParams({ ...params, assumed_annual_return: +e.target.value })} className={numInput} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Inflation %</label>
            <input type="number" step="0.1" value={params.inflation} onChange={(e) => setParams({ ...params, inflation: +e.target.value })} className={numInput} />
          </div>

          {/* Goals */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Goals (optional)</label>
              {goals.length < 3 && (
                <button onClick={addGoal} className="text-xs text-black underline hover:font-medium">+ Add goal</button>
              )}
            </div>
            <div className="space-y-2">
              {goals.map((g, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <Input
                    value={g.name}
                    onChange={(e) => updateGoal(i, 'name', e.target.value)}
                    placeholder="Goal name"
                    className="flex-1"
                  />
                  <Input
                    type="number"
                    step="0.1"
                    value={g.target_usd_millions || ''}
                    onChange={(e) => updateGoal(i, 'target_usd_millions', +e.target.value)}
                    placeholder="USD m"
                    className="w-24"
                  />
                  <div className="w-44">
                    <DatePicker
                      value={g.target_date}
                      onChange={(d) => updateGoal(i, 'target_date', d)}
                      placeholder="Target date"
                    />
                  </div>
                  {goals.length > 1 && (
                    <button onClick={() => removeGoal(i)} className="text-gray-400 hover:text-black text-xs px-1">✕</button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={generatePlan}
            disabled={!selectedId || loading}
            className="w-full bg-black text-white py-2.5 rounded-lg font-medium text-sm hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Generating...' : 'Generate Plan'}
          </button>
        </div>

        {/* Right panel: Results */}
        <div className="flex-1">
          {!selectedId && !result && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-lg">Select a client and click Generate Plan</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-64">
              <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin mb-3" />
              <p className="text-sm text-gray-500">Generating plan with AI...</p>
            </div>
          )}

          {error && !result && !loading && (
            <div className="mb-3 text-xs bg-gray-100 border border-gray-300 text-gray-800 px-3 py-2 rounded">
              Projection request failed — no data displayed. Verify the backend is running and retry.
            </div>
          )}

          {!loading && result && (
            <div className="space-y-4">
              {/* Summary card */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Projected Corpus at Retirement</p>
                    <p className={`text-3xl font-bold ${(result.projected_corpus_usd_millions ?? 0) >= result.target_corpus_usd_millions ? 'text-black' : 'text-gray-600'}`}>
                      ${fmt(result.projected_corpus_usd_millions)}M
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Probability of Success</p>
                    <span className={`inline-block text-lg font-bold px-3 py-1 rounded-full ${
                      (result.probability_of_success ?? 0) >= 75 ? 'bg-black text-white' :
                      (result.probability_of_success ?? 0) >= 50 ? 'bg-gray-300 text-gray-900' :
                      'bg-gray-100 text-gray-600'
                    }`}
                    >
                      {fmt(result.probability_of_success, 0)}%
                    </span>
                    <p className="text-[10px] text-gray-400 mt-1">vs inflation-adjusted target</p>
                  </div>
                </div>
                {result.summary && (
                  <p className="text-xs text-gray-600 mt-3 leading-relaxed">{result.summary}</p>
                )}
              </div>

              {/* Inflation-adjusted view */}
              {result.inflation_pct != null && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <h2 className="text-sm font-semibold text-gray-700 mb-3">Inflation-adjusted view</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Inflation</p>
                      <p className="text-lg font-semibold text-gray-900">{fmt(result.inflation_pct)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Real return</p>
                      <p className="text-lg font-semibold text-gray-900">{fmt(result.real_return_pct)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Target at retirement</p>
                      <p className="text-lg font-semibold text-gray-900">${fmt(result.inflation_adjusted_target_usd_millions)}M</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Corpus in today&apos;s dollars</p>
                      <p className="text-lg font-semibold text-gray-900">${fmt(result.real_projected_corpus_usd_millions)}M</p>
                    </div>
                  </div>
                  {result.real_terms_gap_usd_millions != null && (
                    <p className="text-xs text-gray-500 mt-3">
                      {result.real_terms_gap_usd_millions >= 0
                        ? `USD ${fmt(result.real_terms_gap_usd_millions)}M above target in real terms.`
                        : `USD ${fmt(Math.abs(result.real_terms_gap_usd_millions))}M short of target in real terms.`}
                    </p>
                  )}
                </div>
              )}

              {/* Gap Analysis */}
              {(result.gap_analysis || (result.gap_usd_millions != null && result.gap_usd_millions > 0)) && (
                <div className="bg-gray-50 border border-gray-300 rounded-xl p-4">
                  <p className="text-sm text-gray-800">
                    <span className="font-semibold">Gap Analysis:</span>{' '}
                    {result.gap_analysis || `Projected shortfall of $${fmt(result.gap_usd_millions)}M against the target.`}
                  </p>
                </div>
              )}

              {/* Year-by-year table */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h2 className="text-sm font-semibold text-gray-700">Projection Milestones</h2>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Year</th>
                      <th className="text-left px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Age</th>
                      <th className="text-right px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Projected Value (USD M)</th>
                      <th className="text-right px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Real Value (USD M)</th>
                      <th className="text-right px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Inflation-adjusted Target (USD M)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {result.projection.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                          No projection milestones were returned.
                        </td>
                      </tr>
                    ) : result.projection.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-gray-700">{row.year}</td>
                        <td className="px-4 py-2 text-gray-600">{row.age}</td>
                        <td className="px-4 py-2 text-right font-semibold text-gray-900">${fmt(row.projected_value_usd_millions)}M</td>
                        <td className="px-4 py-2 text-right text-gray-700">${fmt(row.real_corpus_usd_millions)}M</td>
                        <td className="px-4 py-2 text-right text-gray-500">${fmt(row.inflation_adjusted_target_usd_millions)}M</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Recommendations</h2>
                {result.recommendations.length === 0 ? (
                  <p className="text-sm text-gray-500">No recommendations were returned.</p>
                ) : (
                  <ol className="list-decimal list-inside space-y-1.5">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="text-sm text-gray-600">{rec}</li>
                    ))}
                  </ol>
                )}
              </div>

              {/* Disclaimer */}
              <p className="text-xs text-gray-400 px-1">{result.disclaimer}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
