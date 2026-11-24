'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { endpoints } from '@/lib/endpoints';
import { Grid } from '@/components/ui/LiveFeature';
import {
  PageShell, PageHeader, Card, Loading, ErrorState, Button, DataView,
  QueryPanel, StatusBadge,
} from '@/components/ui/WorkbenchUI';

export default function WorkflowDetailPage() {
  const params = useParams();
  const workflowId = String(params?.workflowId || '');
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const load = () => {
    setLoading(true);
    endpoints.workflows.detail(workflowId)
      .then((r: any) => { setDetail(r.data); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (workflowId) load(); }, [workflowId]); // eslint-disable-line react-hooks/exhaustive-deps

  const wf = detail?.workflow || detail;

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Advice & Execution · Workflow detail"
        title={wf?.type ? String(wf.type).replace(/_/g, ' ') : 'Workflow'}
        description="Stage progress, briefs and messages for this client workflow"
        actions={
          <>
            <Link href="/workflows"><Button>← All workflows</Button></Link>
            <Link href={`/workflows/${workflowId}/messages`}><Button>Messages</Button></Link>
            <Link href="/briefs"><Button>Briefs</Button></Link>
          </>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Status</div><div className="mt-2"><StatusBadge tone={wf?.status === 'FAILED' ? 'error' : wf?.status === 'COMPLETED' ? 'success' : 'neutral'}>{wf?.status || '—'}</StatusBadge></div></Card>
        <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Current stage</div><div className="text-sm font-medium mt-2">{wf?.current_stage || '—'}</div></Card>
        <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Context revision</div><div className="text-xl font-semibold mt-1">{wf?.context_revision ?? '—'}</div></Card>
        <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Stages</div><div className="text-xl font-semibold mt-1">{wf?.stages?.length ?? 0}</div></Card>
      </div>

      {loading ? <Card><Loading /></Card> : error ? <ErrorState error={error} onRetry={load} /> : (
        <>
          <Card title="Workflow record" subtitle="Full details of this workflow" className="mb-5">
            <DataView data={detail} />
          </Card>
          <Grid>
            <QueryPanel
              key={`briefs-${workflowId}`}
              title="Briefs for this workflow"
              subtitle="Briefs produced by this workflow"
              method="GET"
              path={`/briefs/workflows/${workflowId}/briefs`}
              emptyTitle="No briefs linked"
            />
            <QueryPanel
              key={`msgs-${workflowId}`}
              title="Messages for this workflow"
              subtitle="Messages prepared for this workflow"
              method="GET"
              path={`/workflows/${workflowId}/messages`}
              rowsOf={(d: any) => (Array.isArray(d) ? d : d?.messages || d?.items || [])}
              emptyTitle="No message drafts"
            />
          </Grid>
        </>
      )}
    </PageShell>
  );
}
