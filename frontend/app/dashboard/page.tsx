'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface CalendarEvent {
  id: string;
  client_id: string;
  client_name: string;
  start_time: string;
  title: string;
  description?: string;
}

interface PriorityEvaluation {
  client_id: string;
  client_name: string;
  rank: number;
  score: number;
  reason: string;
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [priorities, setPriorities] = useState<PriorityEvaluation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [eventsRes, prioritiesRes] = await Promise.allSettled([
        apiClient.get<{ items: CalendarEvent[] }>('/calendar/events'),
        apiClient.get<{ clients: PriorityEvaluation[], status: string }>('/priorities/evaluations'),
      ]);

      if (eventsRes.status === 'fulfilled') {
        const evData = eventsRes.value.data as any;
        setEvents(Array.isArray(evData) ? evData : (evData?.items || []));
      }

      if (prioritiesRes.status === 'fulfilled') {
        const priData = prioritiesRes.value.data as { clients: PriorityEvaluation[], status: string };
        setPriorities((priData?.clients || []).slice(0, 10));
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading dashboard...</span>
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
          <h1 className="text-3xl font-bold mb-2">My Day</h1>
          <p className="text-gray-600">Today's schedule and priority clients</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-300 rounded p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Today's Calendar */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Today's Schedule</h2>
            {events.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No events scheduled for today
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{event.title}</div>
                        <div className="text-sm text-gray-600 mt-1">
                          {new Date(event.start_time).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                        {event.description && (
                          <div className="text-sm text-gray-700 mt-2">{event.description}</div>
                        )}
                      </div>
                      <Link
                        href={`/clients/${event.client_id}`}
                        className="ml-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View Client →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top 10 Priority Clients */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Top 10 Priority Clients</h2>
            {priorities.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No priority evaluations available
              </div>
            ) : (
              <div className="space-y-2">
                {priorities.map((priority) => (
                  <Link
                    key={priority.client_id}
                    href={`/clients/${priority.client_id}`}
                    className="block border border-gray-200 rounded p-3 hover:border-gray-400 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold">
                        {priority.rank}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900">{priority.client_name}</div>
                        <div className="text-sm text-gray-600 mt-1">{priority.reason}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          Score: {priority.score.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              href="/clients"
              className="p-4 border border-gray-300 rounded hover:border-gray-500 hover:shadow-md transition-all text-center"
            >
              <div className="text-2xl mb-2">👥</div>
              <div className="font-medium">View Clients</div>
            </Link>
            <Link
              href="/priorities"
              className="p-4 border border-gray-300 rounded hover:border-gray-500 hover:shadow-md transition-all text-center"
            >
              <div className="text-2xl mb-2">⭐</div>
              <div className="font-medium">Priorities</div>
            </Link>
            <Link
              href="/workflows"
              className="p-4 border border-gray-300 rounded hover:border-gray-500 hover:shadow-md transition-all text-center"
            >
              <div className="text-2xl mb-2">🔄</div>
              <div className="font-medium">Workflows</div>
            </Link>
            <Link
              href="/admin"
              className="p-4 border border-gray-300 rounded hover:border-gray-500 hover:shadow-md transition-all text-center"
            >
              <div className="text-2xl mb-2">⚙️</div>
              <div className="font-medium">Admin</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
