'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface WorkflowDetail {
  workflow_id: string;
  workflow_type: string;
  client_id: string;
  client_name?: string;
  stage: string;
  status: string;
  created_at: string;
  updated_at: string;
  context?: Record<string, any>;
  artifacts?: Artifact[];
}

interface Artifact {
  id: string;
  type: string;
  name: string;
  created_at: string;
  url?: string;
}

export default function WorkflowDetailPage() {
  const params = useParams();
  const workflowId = params?.workflowId as string;

  const [loading, setLoading] = useState(true);
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (workflowId) {
      loadWorkflow();
    }
  }, [workflowId]);

  const loadWorkflow = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<{ workflow: any }>(`/workflows/${workflowId}`);
      const wfData = response.data as { workflow: any };
      const wf = wfData.workflow || response.data;
      setWorkflow({
        workflow_id: wf.id || wf.workflow_id,
        workflow_type: wf.type || wf.workflow_type,
        stage: wf.current_stage || wf.stage,
        client_id: wf.client_id,
        client_name: wf.client_name,
        status: wf.status,
        created_at: wf.created_at,
        updated_at: wf.updated_at,
        context: wf.context,
        artifacts: wf.artifacts,
      } as WorkflowDetail);
    } catch (err: any) {
      console.error('Error loading workflow:', err);
      setError(err.message || 'Failed to load workflow details');
    } finally {
      setLoading(false);
    }
  };

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
              <span className="text-sm text-gray-600">Loading workflow...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-4">
            <Link href="/workflows" className="text-blue-600 hover:text-blue-800">
              ← Back to Workflows
            </Link>
          </div>
          <div className="bg-red-50 border border-red-300 rounded p-6">
            <p className="text-red-700">{error || 'Workflow not found'}</p>
            <button
              onClick={loadWorkflow}
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
          <Link href="/workflows" className="text-blue-600 hover:text-blue-800">
            ← Back to Workflows
          </Link>
        </div>

        {/* Workflow Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">{workflow.workflow_type}</h1>
              <p className="text-gray-600">Workflow ID: {workflow.workflow_id}</p>
            </div>
            <span className={`px-3 py-1 text-sm font-medium rounded ${getStatusColor(workflow.status)}`}>
              {workflow.status}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {workflow.client_name && (
              <div>
                <div className="text-sm text-gray-600">Client</div>
                <Link
                  href={`/clients/${workflow.client_id}`}
                  className="text-lg font-semibold text-blue-600 hover:text-blue-800"
                >
                  {workflow.client_name}
                </Link>
              </div>
            )}
            <div>
              <div className="text-sm text-gray-600">Current Stage</div>
              <div className="text-lg font-semibold">{workflow.stage}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Created</div>
              <div className="text-sm font-medium">
                {new Date(workflow.created_at).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Last Updated</div>
              <div className="text-sm font-medium">
                {new Date(workflow.updated_at).toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Context Snapshot */}
          {workflow.context && Object.keys(workflow.context).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Context Snapshot</h2>
              <div className="bg-gray-50 rounded p-4 overflow-auto max-h-96">
                <pre className="text-xs font-mono">
                  {JSON.stringify(workflow.context, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Artifacts */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Artifacts</h2>
            {!workflow.artifacts || workflow.artifacts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No artifacts generated</div>
            ) : (
              <div className="space-y-3">
                {workflow.artifacts.map((artifact) => (
                  <div
                    key={artifact.id}
                    className="border border-gray-200 rounded p-4 hover:border-gray-400 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-semibold">{artifact.name}</div>
                        <div className="text-sm text-gray-600 mt-1">Type: {artifact.type}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(artifact.created_at).toLocaleString()}
                        </div>
                      </div>
                      {artifact.url && (
                        <a
                          href={artifact.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                        >
                          View →
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">Actions</h2>
          <div className="flex items-center gap-3">
            <Link
              href={`/workflows/${workflowId}/messages`}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 transition-colors"
            >
              View Messages
            </Link>
            <button
              onClick={loadWorkflow}
              className="px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded hover:bg-gray-300 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
