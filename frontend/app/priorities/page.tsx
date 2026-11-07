'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface PriorityEvaluation {
  client_id: string;
  client_name: string;
  rank: number;
  score: number;
  reason: string;
  snoozed_until?: string | null;
  pinned?: boolean;
  dismissed?: boolean;
}

export default function PrioritiesPage() {
  const [loading, setLoading] = useState(true);
  const [priorities, setPriorities] = useState<PriorityEvaluation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPriorities();
  }, []);

  const loadPriorities = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<PriorityEvaluation[]>('/priorities/evaluations');
      setPriorities(response.data.slice(0, 10));
    } catch (err: any) {
      console.error('Error loading priorities:', err);
      setError(err.message || 'Failed to load priorities');
    } finally {
      setLoading(false);
    }
  };

  const handleSnooze = async (clientId: string) => {
    try {
      await apiClient.post(`/priorities/${clientId}/snooze`, {
        until: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      });
      await loadPriorities();
    } catch (err: any) {
      console.error('Error snoozing priority:', err);
      alert('Failed to snooze priority');
    }
  };

  const handleDismiss = async (clientId: string) => {
    try {
      await apiClient.post(`/priorities/${clientId}/dismiss`);
      await loadPriorities();
    } catch (err: any) {
      console.error('Error dismissing priority:', err);
      alert('Failed to dismiss priority');
    }
  };

  const handlePin = async (clientId: string) => {
    try {
      await apiClient.post(`/priorities/${clientId}/pin`);
      await loadPriorities();
    } catch (err: any) {
      console.error('Error pinning priority:', err);
      alert('Failed to pin priority');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading priorities...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Priority Clients</h1>
          <p className="text-gray-600">Top 10 clients ranked by AI evaluation</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-300 rounded p-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadPriorities}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Priority List */}
        {priorities.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500">No priority evaluations available</p>
          </div>
        ) : (
          <div className="space-y-4">
            {priorities.map((priority) => (
              <div
                key={priority.client_id}
                className={`bg-white border rounded-lg p-6 transition-all ${
                  priority.pinned
                    ? 'border-yellow-400 shadow-lg'
                    : priority.dismissed
                    ? 'border-gray-200 opacity-60'
                    : 'border-gray-200 hover:border-gray-400 hover:shadow-md'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Rank Badge */}
                  <div
                    className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                      priority.rank <= 3
                        ? 'bg-orange-500 text-white'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    {priority.rank}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <Link
                          href={`/clients/${priority.client_id}`}
                          className="text-xl font-semibold text-gray-900 hover:text-blue-600"
                        >
                          {priority.client_name}
                        </Link>
                        {priority.pinned && (
                          <span className="ml-2 text-yellow-500" title="Pinned">
                            📌
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        Score: {priority.score.toFixed(2)}
                      </div>
                    </div>

                    <p className="text-gray-700 mb-4">{priority.reason}</p>

                    {priority.snoozed_until && (
                      <div className="mb-3 text-sm text-orange-600">
                        Snoozed until {new Date(priority.snoozed_until).toLocaleString()}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/clients/${priority.client_id}`}
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
                      >
                        View Client
                      </Link>
                      <button
                        onClick={() => handleSnooze(priority.client_id)}
                        className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded hover:bg-gray-300 transition-colors"
                        disabled={priority.dismissed}
                      >
                        Snooze 24h
                      </button>
                      <button
                        onClick={() => handlePin(priority.client_id)}
                        className="px-4 py-2 bg-yellow-100 text-yellow-800 text-sm font-medium rounded hover:bg-yellow-200 transition-colors"
                        disabled={priority.dismissed}
                      >
                        {priority.pinned ? 'Unpin' : 'Pin'}
                      </button>
                      <button
                        onClick={() => handleDismiss(priority.client_id)}
                        className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded hover:bg-red-200 transition-colors"
                        disabled={priority.dismissed}
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
