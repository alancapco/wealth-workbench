'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface Client {
  client_id: string;
  name: string;
  aum?: number;
  risk_profile?: string;
  segment?: string;
  last_contact?: string;
}

export default function ClientsPage() {
  const [loading, setLoading] = useState(true);
  const [clients, setClients] = useState<Client[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ clients: Client[], count: number }>('/clients');
      const clientsData = response.data as { clients: Client[], count: number };
      setClients(clientsData.clients || []);
    } catch (err: any) {
      console.error('Error loading clients:', err);
      setError(err.message || 'Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const filteredClients = clients.filter((client) =>
    client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    client.client_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading clients...</span>
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
          <h1 className="text-3xl font-bold mb-2">Clients</h1>
          <p className="text-gray-600">Manage your client relationships</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-300 rounded p-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadClients}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Search and Filter */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <input
            type="text"
            placeholder="Search clients by name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Client List */}
        {filteredClients.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500">
              {searchQuery ? 'No clients found matching your search' : 'No clients available'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClients.map((client) => (
              <Link
                key={client.client_id}
                href={`/clients/${client.client_id}`}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-400 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{client.name}</h3>
                    <p className="text-sm text-gray-500">{client.client_id}</p>
                  </div>
                  {client.segment && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                      {client.segment}
                    </span>
                  )}
                </div>

                {client.aum !== undefined && (
                  <div className="mb-2">
                    <span className="text-sm text-gray-600">AUM: </span>
                    <span className="font-semibold">
                      ${(client.aum / 1_000_000).toFixed(1)}M
                    </span>
                  </div>
                )}

                {client.risk_profile && (
                  <div className="mb-2">
                    <span className="text-sm text-gray-600">Risk Profile: </span>
                    <span className="font-medium">{client.risk_profile}</span>
                  </div>
                )}

                {client.last_contact && (
                  <div className="text-sm text-gray-500 mt-4 pt-4 border-t border-gray-100">
                    Last contact: {new Date(client.last_contact).toLocaleDateString()}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
