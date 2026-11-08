'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { DEFAULT_SESSION } from '@/lib/session';

interface DecisionGate {
  gate_id: string;
  name: string;
  description: string;
  enabled: boolean;
  config?: Record<string, any>;
}

export default function AdminDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [gates, setGates] = useState<DecisionGate[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGates();
  }, []);

  const loadGates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ gates: any[] }>(`/admin/config/gates?tenant_id=${DEFAULT_SESSION.tenant_id}`);
      const gatesData = response.data as { gates: any[] };
      const mappedGates = (gatesData.gates || []).map(g => ({
        gate_id: g.key,
        name: g.key.replace(/_/g, ' ').replace(/^DEC-/i, 'DEC-'),
        description: `Decision gate ${g.key}`,
        enabled: g.enabled,
      }));
      setGates(mappedGates);
    } catch (err: any) {
      console.error('Error loading gates:', err);
      setError(err.message || 'Failed to load decision gates');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleGate = async (gateId: string, currentState: boolean) => {
    try {
      await apiClient.patch(`/admin/config/gates/${gateId}`, {
        enabled: !currentState,
      });
      await loadGates();
    } catch (err: any) {
      console.error('Error toggling gate:', err);
      alert('Failed to toggle gate');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading admin dashboard...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">System configuration and management</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-300 rounded p-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadGates}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link
            href="/admin/audit"
            className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-400 hover:shadow-lg transition-all"
          >
            <div className="text-2xl mb-2">📋</div>
            <h3 className="text-lg font-semibold mb-1">Audit Logs</h3>
            <p className="text-sm text-gray-600">View system audit trail</p>
          </Link>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-2xl mb-2">⚙️</div>
            <h3 className="text-lg font-semibold mb-1">Configuration</h3>
            <p className="text-sm text-gray-600">Manage system settings</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-2xl mb-2">👥</div>
            <h3 className="text-lg font-semibold mb-1">Users</h3>
            <p className="text-sm text-gray-600">User management</p>
          </div>
        </div>

        {/* Decision Gates */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-6">Decision Gates</h2>

          {gates.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No decision gates configured</div>
          ) : (
            <div className="space-y-4">
              {gates.map((gate) => (
                <div
                  key={gate.gate_id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-400 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold">{gate.name}</h3>
                        <span className="text-sm text-gray-500 font-mono">{gate.gate_id}</span>
                      </div>
                      <p className="text-gray-600 mb-3">{gate.description}</p>
                      {gate.config && Object.keys(gate.config).length > 0 && (
                        <details className="text-sm">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                            View Configuration
                          </summary>
                          <pre className="mt-2 p-3 bg-gray-50 rounded overflow-auto text-xs font-mono">
                            {JSON.stringify(gate.config, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>

                    <button
                      onClick={() => handleToggleGate(gate.gate_id, gate.enabled)}
                      className={`ml-4 px-4 py-2 rounded font-medium transition-colors ${
                        gate.enabled
                          ? 'bg-green-100 text-green-800 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                      }`}
                    >
                      {gate.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-sm text-gray-600 mb-2">System Status</h3>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="font-semibold">Operational</span>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-sm text-gray-600 mb-2">Active Workflows</h3>
            <div className="text-2xl font-semibold">-</div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-sm text-gray-600 mb-2">Total Users</h3>
            <div className="text-2xl font-semibold">-</div>
          </div>
        </div>
      </div>
    </div>
  );
}
