'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { DEFAULT_SESSION } from '@/lib/session';

interface ClientDetail {
  client_id: string;
  name: string;
  aum?: number;
  risk_profile?: string;
  segment?: string;
  email?: string;
  phone?: string;
  address?: string;
  last_contact?: string;
}

interface Interaction {
  id: string;
  type: string;
  date: string;
  summary: string;
}

interface Workflow {
  workflow_id: string;
  workflow_type: string;
  stage: string;
  created_at: string;
  status: string;
}

interface FamilyMember {
  client_id: string;
  name: string;
  relationship: string;
}

export default function ClientDetailPage() {
  const params = useParams();
  const clientId = params?.clientId as string;

  const [loading, setLoading] = useState(true);
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (clientId) {
      loadClientDetail();
    }
  }, [clientId]);

  const loadClientDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      const [clientRes, workflowsRes] = await Promise.allSettled([
        apiClient.get<ClientDetail>(`/clients/${clientId}`),
        apiClient.get<{ items: Workflow[], total: number }>(`/workflows?book_id=${DEFAULT_SESSION.book_id}&client_id=${clientId}`),
      ]);

      if (clientRes.status === 'fulfilled') {
        setClient(clientRes.value.data as ClientDetail);
      } else {
        setError('Failed to load client details');
      }

      if (workflowsRes.status === 'fulfilled') {
        const wfData = workflowsRes.value.data as { items: Workflow[], total: number };
        setWorkflows(wfData.items || []);
      }

      // Mock data for interactions and family (until APIs are available)
      setInteractions([
        {
          id: '1',
          type: 'Meeting',
          date: new Date().toISOString(),
          summary: 'Portfolio review and rebalancing discussion',
        },
      ]);
    } catch (err: any) {
      console.error('Error loading client detail:', err);
      setError(err.message || 'Failed to load client details');
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
              <span className="text-sm text-gray-600">Loading client details...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-4">
            <Link href="/clients" className="text-blue-600 hover:text-blue-800">
              ← Back to Clients
            </Link>
          </div>
          <div className="bg-red-50 border border-red-300 rounded p-6">
            <p className="text-red-700">{error || 'Client not found'}</p>
            <button
              onClick={loadClientDetail}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link href="/clients" className="text-blue-600 hover:text-blue-800">
            ← Back to Clients
          </Link>
        </div>

        {/* Client Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">{client.name}</h1>
              <p className="text-gray-600">{client.client_id}</p>
            </div>
            {client.segment && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
                {client.segment}
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-6">
            {client.aum !== undefined && (
              <div>
                <div className="text-sm text-gray-600">AUM</div>
                <div className="text-xl font-semibold">
                  ${(client.aum / 1_000_000).toFixed(1)}M
                </div>
              </div>
            )}
            {client.risk_profile && (
              <div>
                <div className="text-sm text-gray-600">Risk Profile</div>
                <div className="text-xl font-semibold">{client.risk_profile}</div>
              </div>
            )}
            {client.email && (
              <div>
                <div className="text-sm text-gray-600">Email</div>
                <div className="text-sm font-medium">{client.email}</div>
              </div>
            )}
            {client.phone && (
              <div>
                <div className="text-sm text-gray-600">Phone</div>
                <div className="text-sm font-medium">{client.phone}</div>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Interactions */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Interactions</h2>
            {interactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No interactions recorded</div>
            ) : (
              <div className="space-y-3">
                {interactions.map((interaction) => (
                  <div key={interaction.id} className="border-l-4 border-blue-500 bg-blue-50 p-3 rounded">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-semibold">{interaction.type}</div>
                        <div className="text-sm text-gray-600 mt-1">{interaction.summary}</div>
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(interaction.date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Workflows */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Active Workflows</h2>
            {workflows.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No active workflows</div>
            ) : (
              <div className="space-y-3">
                {workflows.map((workflow) => (
                  <Link
                    key={workflow.workflow_id}
                    href={`/workflows/${workflow.workflow_id}`}
                    className="block border border-gray-200 rounded p-3 hover:border-gray-400 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-semibold">{workflow.workflow_type}</div>
                        <div className="text-sm text-gray-600 mt-1">Stage: {workflow.stage}</div>
                      </div>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        {workflow.status}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Family Relationships */}
          {familyMembers.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Family Relationships</h2>
              <div className="space-y-2">
                {familyMembers.map((member) => (
                  <Link
                    key={member.client_id}
                    href={`/clients/${member.client_id}`}
                    className="block border border-gray-200 rounded p-3 hover:border-gray-400 hover:shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{member.name}</div>
                        <div className="text-sm text-gray-600">{member.relationship}</div>
                      </div>
                      <span className="text-blue-600">→</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
