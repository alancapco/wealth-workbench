'use client';

import { useState, useEffect } from 'react';
import { demoClientApi } from '@/lib/api';

interface DemoClient {
  id: string;
  name: string;
  aum_usd_millions: number;
}

interface Goal {
  name: string;
  target_usd_millions: number;
  target_year: number;
}

interface ProjectionYear {
  year: number;
  age: number;
  projected_value_usd_millions: number;
  key_events: string;
}

interface PlanResult {
  projected_corpus_usd_millions: number;
  target_corpus_usd_millions: number;
  probability_of_success: number;
  gap_usd_millions: number | null;
  projection: ProjectionYear[];
  recommendations: string[];
  disclaimer: string;
}

const DEFAULT_PARAMS = {
  current_age: 52,
  retirement_age: 65,
  monthly_contribution: 50000,
  target_retirement_corpus: 80,
  assumed_annual_return: 6.5,
  inflation: 2.5,
};

function fallbackCalc(params: typeof DEFAULT_PARAMS, currentSavings: number): PlanResult {
  const years = params.retirement_age - params.current_age;
  const annualContribution = params.monthly_contribution * 12;
  const realReturn = (params.assumed_annual_return - params.inflation) / 100;
  let value = currentSavings;
  const projection: ProjectionYear[] = [];

  for (let i = 0; i <= years; i++) {
    const year = new Date().getFullYear() + i;
    const age = params.current_age + i;
    if (i > 0) value = value * (1 + realReturn) + annualContribution * Math.pow(1 + realReturn, 0.5);
    if (i % 5 === 0 || i === years) {
      projection.push({ year, age, projected_value_usd_millions: value, key_events: i === 0 ? 'Start' : i === years ? 'Retirement' : '' });
    }
  }

  const gap = value < params.target_retirement_corpus ? params.target_retirement_corpus - value : null;

  return {
    projected_corpus_usd_millions: value,
    target_corpus_usd_millions: params.target_retirement_corpus,
    probability_of_success: value >= params.target_retirement_corpus ? 85 : Math.round((value / params.target_retirement_corpus) * 70),
    gap_usd_millions: gap,
    projection,
    recommendations: [
      `Increase monthly contribution by $${Math.round(((params.target_retirement_corpus - value) / years / 12) || 0).toLocaleString()} to close the gap.`,
      `Consider increasing equity allocation to boost long-term returns toward ${params.assumed_annual_return + 1.5}% effective annual return.`,
      `Review portfolio annually and rebalance to maintain target asset allocation.`,
      `Account for inflation: at ${params.inflation}% inflation, $${params.target_retirement_corpus}M in today's dollars will need to grow significantly by retirement.`,
    ],
    disclaimer: 'AI-generated projection for demonstration purposes only. Not financial advice.',
  };
}

export default function FuturePlannerPage() {
  const [clients, setClients] = useState<DemoClient[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [currentSavings, setCurrentSavings] = useState(0);
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [goals, setGoals] = useState<Goal[]>([
    { name: '', target_usd_millions: 0, target_year: new Date().getFullYear() + 10 },
  ]);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
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
      });
  }, []);

  useEffect(() => {
    const client = clients.find((c) => c.id === selectedId);
    if (client) {
      setCurrentSavings(client.aum_usd_millions);
    }
  }, [selectedId, clients]);

  const updateGoal = (i: number, field: keyof Goal, value: string | number) => {
    setGoals((prev) => prev.map((g, idx) => idx === i ? { ...g, [field]: value } : g));
  };

  const addGoal = () => {
    if (goals.length < 3) setGoals([...goals, { name: '', target_usd_millions: 0, target_year: new Date().getFullYear() + 15 }]);
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
        monthly_contribution: params.monthly_contribution,
        target_retirement_corpus: params.target_retirement_corpus,
        assumed_annual_return: params.assumed_annual_return,
        inflation: params.inflation,
        goals: goals.filter((g) => g.name),
      });
      const data = res.data?.data ?? res.data;
      setResult(data);
    } catch {
      setError(true);
      setOffline(true);
      setResult(fallbackCalc(params, currentSavings));
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
          <span className="ml-auto text-xs bg-yellow-900 text-yellow-300 px-3 py-1 rounded-full">
            AI service unavailable — showing mathematical estimate
          </span>
        )}
      </header>

      <div className="flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto w-full">
        {/* Left panel: Inputs */}
        <div className="lg:w-96 shrink-0 bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className={numInput}
            >
              <option value="">— Select client —</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
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
                  <input
                    type="text"
                    value={g.name}
                    onChange={(e) => updateGoal(i, 'name', e.target.value)}
                    placeholder="Goal name"
                    className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-xs"
                  />
                  <input
                    type="number"
                    step="0.1"
                    value={g.target_usd_millions || ''}
                    onChange={(e) => updateGoal(i, 'target_usd_millions', +e.target.value)}
                    placeholder="$M"
                    className="w-16 border border-gray-300 rounded px-2 py-1.5 text-xs"
                  />
                  <input
                    type="number"
                    value={g.target_year || ''}
                    onChange={(e) => updateGoal(i, 'target_year', +e.target.value)}
                    placeholder="Year"
                    className="w-20 border border-gray-300 rounded px-2 py-1.5 text-xs"
                  />
                  {goals.length > 1 && (
                    <button onClick={() => removeGoal(i)} className="text-gray-400 hover:text-red-500 text-xs px-1">✕</button>
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

          {error && result && (
            <div className="mb-3 text-xs bg-yellow-100 text-yellow-800 px-3 py-2 rounded">
              AI service unavailable — showing mathematical estimate
            </div>
          )}

          {!loading && result && (
            <div className="space-y-4">
              {/* Summary card */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Projected Corpus at Retirement</p>
                    <p className={`text-3xl font-bold ${result.projected_corpus_usd_millions >= result.target_corpus_usd_millions ? 'text-green-600' : 'text-red-600'}`}>
                      ${result.projected_corpus_usd_millions.toFixed(1)}M
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Probability of Success</p>
                    <span className={`inline-block text-lg font-bold px-3 py-1 rounded-full ${
                      result.probability_of_success >= 75 ? 'bg-green-100 text-green-700' :
                      result.probability_of_success >= 50 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {result.probability_of_success}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Gap Analysis */}
              {result.gap_usd_millions != null && result.gap_usd_millions > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                  <p className="text-sm text-orange-800">
                    <span className="font-semibold">⚠ Gap Analysis:</span> You are on track to fall short by ${result.gap_usd_millions.toFixed(1)}M. Consider increasing contributions or adjusting retirement age.
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
                      <th className="text-left px-4 py-2 text-xs font-semibold text-gray-500 uppercase">Key Events</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {result.projection.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-gray-700">{row.year}</td>
                        <td className="px-4 py-2 text-gray-600">{row.age}</td>
                        <td className="px-4 py-2 text-right font-semibold text-gray-900">${row.projected_value_usd_millions.toFixed(1)}M</td>
                        <td className="px-4 py-2 text-gray-500 text-xs">{row.key_events}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Recommendations */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">Recommendations</h2>
                <ol className="list-decimal list-inside space-y-1.5">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="text-sm text-gray-600">{rec}</li>
                  ))}
                </ol>
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
