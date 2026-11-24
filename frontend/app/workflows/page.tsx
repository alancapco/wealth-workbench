'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { endpoints } from '@/lib/endpoints';
import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel } from '@/components/ui/LiveFeature';
import {
  Card, DataTable, Loading, ErrorState, EmptyState, Button, StatusBadge,
  QueryPanel, SectionLabel,
} from '@/components/ui/WorkbenchUI';

export default function WorkflowsPage() {
  const app = useApp();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [feedback, setFeedback] = useState('');
  // Stage runs require a registered skill version; unregistered keys return 400.
  const [stageKey, setStageKey] = useState('');

  const load = () => {
    if (!app.bookId) return;
    setLoading(true);
    endpoints.workflows.list(app.bookId)
      .then((r: any) => { setItems(r.data?.items || []); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (app.ready) load(); }, [app.ready, app.bookId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    endpoints.workflows.skills()
      .then((r: any) => setStageKey(r.data?.items?.[0]?.id ?? ''))
      .catch(() => setStageKey(''));
  }, []);

  const control = async (name: string, fn: () => Promise<any>) => {
    setFeedback('');
    try {
      const res = await fn();
      setFeedback(`${name} → HTTP ${res.status} · ${JSON.stringify(res.data).slice(0, 180)}`);
      load();
    } catch (e) {
      setFeedback(`${name} failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  return (
    <FeaturePage
      eyebrow="Advice & Execution"
      title="Workflows"
      description="Live workflow instances for the selected book, plus stage execution and lifecycle controls."
      context={['book', 'client', 'workflow']}
      wide
      actions={<Button onClick={load}>Refresh</Button>}
    >
      {feedback && (
        <div className="border border-gray-300 bg-white rounded px-4 py-2 text-xs text-gray-700 break-words">{feedback}</div>
      )}

      <Card title="Workflow instances" subtitle="Workflows in the selected book" bodyClassName="p-0">
        <div className="p-5">
          {loading ? <Loading /> : error ? <ErrorState error={error} onRetry={load} /> : items.length === 0 ? (
            <EmptyState title="No workflows yet" detail="Create one below from a real client record." />
          ) : (
            <DataTable
              rows={items}
              columns={[
                {
                  key: 'type', label: 'Workflow', render: (w: any) => (
                    <Link href={`/workflows/${w.id}`} className="font-medium text-black hover:underline">
                      {(w.type || 'Workflow').replace(/_/g, ' ')}
                    </Link>
                  ),
                },
                {
                  key: 'client_name', label: 'Client', render: (w: any) => {
                    const label = w.client_name
                      || app.clientOptions.find((o) => o.value === w.client_id)?.label
                      || null;
                    return label || <span className="text-gray-300">—</span>;
                  },
                },
                { key: 'current_stage', label: 'Stage', render: (w: any) => (w.current_stage || '—').replace(/_/g, ' ') },
                {
                  key: 'status', label: 'Status', render: (w: any) => (
                    <StatusBadge tone={w.status === 'FAILED' || w.status === 'ABANDONED' ? 'error' : w.status === 'COMPLETED' ? 'success' : 'neutral'}>{w.status || '—'}</StatusBadge>
                  ),
                },
                { key: 'created_at', label: 'Created' },
                {
                  key: 'actions', label: '', render: (w: any) => (
                    <div className="flex gap-1 flex-wrap">
                      <Link href={`/workflows/${w.id}`}><Button>Detail</Button></Link>
                      <Link href={`/workflows/${w.id}/messages`}><Button>Messages</Button></Link>
                    </div>
                  ),
                },
              ]}
            />
          )}
        </div>
      </Card>

      <SectionLabel>Create and control</SectionLabel>
      <Grid>
        <OperationPanel
          title="Create workflow"
          subtitle="Start a new client workflow"
          method="POST"
          path="/workflow"
          bodyDefault={JSON.stringify({
            type: 'MEETING_PREP',
            client_id: app.clientId,
            entry: 'MY_DAY',
          }, null, 2)}
        />
        <QueryPanel
          title="Registered skills"
          subtitle="Skills available to workflows"
          method="GET"
          path="/workflow/skills"
          rowsOf={(d: any) => d?.items || []}
          emptyTitle="No skills registered"
          emptyDetail="Register a skill before running a workflow stage."
        />
      </Grid>

      <Grid>
        <OperationPanel
          key={`${stageKey}-${app.workflowId}`}
          title="Run a workflow stage"
          subtitle="Stage key must match a registered skill"
          method="POST"
          path={(v) => `/workflow/${v.wid}/stages/${v.stage}/runs`}
          params={[
            { name: 'wid', label: 'Workflow', in: 'path', default: app.workflowId },
            { name: 'stage', label: 'Stage key', in: 'path', default: stageKey, placeholder: 'Registered skill key' },
          ]}
          bodyDefault={JSON.stringify({ input_refs: [], context_revision: 1 }, null, 2)}
        />
        <Card title="Lifecycle controls" subtitle="Pause, resume or abandon a workflow">
          <div className="flex flex-wrap gap-2 mb-3">
            <Button onClick={() => void control('Pause', () => endpoints.workflows.pause(app.workflowId))}>Pause</Button>
            <Button onClick={() => void control('Resume', () => endpoints.workflows.resume(app.workflowId))}>Resume</Button>
            <Button onClick={() => void control('Abandon', () => endpoints.workflows.abandon(app.workflowId))}>Abandon</Button>
          </div>
          <div className="text-xs text-gray-500">
            Target: {app.workflowOptions.find((o) => o.value === app.workflowId)?.label || 'No workflow selected'}
          </div>
        </Card>
      </Grid>
    </FeaturePage>
  );
}
