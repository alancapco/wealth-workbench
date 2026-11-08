'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { DEFAULT_SESSION } from '@/lib/session';

interface Workflow {
  workflow_id: string;
  workflow_type: string;
  client_id: string;
  client_name?: string;
  stage: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function WorkflowsPage() {
  const [loading, setLoading] = useState(true);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ items: Workflow[], total: number }>(`/workflows?book_id=${DEFAULT_SESSION.book_id}`);
      const wfData = response.data as { items: Workflow[], total: number };
      setWorkflows(wfData.items || []);
    } catch (err: any) {
      console.error('Error loading workflows:', err);
      setError(err.message || 'Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const filteredWorkflows = workflows.filter((workflow) =>
    filterStatus === 'all' ? true : workflow.status === filterStatus
  );

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading workflows...</span>
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
          <h1 className="text-3xl font-bold mb-2">Workflows</h1>
          <p className="text-gray-600">Active workflows for your clients</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-300 rounded p-4">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadWorkflows}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                filterStatus === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                filterStatus === 'active'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                filterStatus === 'completed'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Completed
            </button>
            <button
              onClick={() => setFilterStatus('pending')}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                filterStatus === 'pending'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Pending
            </button>
          </div>
        </div>

        {/* Workflow List */}
        {filteredWorkflows.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500">
              {filterStatus === 'all' ? 'No workflows found' : `No ${filterStatus} workflows`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredWorkflows.map((workflow) => (
              <Link
                key={workflow.workflow_id}
                href={`/workflows/${workflow.workflow_id}`}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-400 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {workflow.workflow_type}
                    </h3>
                    {workflow.client_name && (
                      <p className="text-sm text-gray-600">{workflow.client_name}</p>
                    )}
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(workflow.status)}`}>
                    {workflow.status}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-600">Stage: </span>
                    <span className="font-medium">{workflow.stage}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">ID: </span>
                    <span className="font-mono text-xs">{workflow.workflow_id.slice(0, 8)}</span>
                  </div>
                  <div className="text-gray-500 pt-3 border-t border-gray-100">
                    Created: {new Date(workflow.created_at).toLocaleString()}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
