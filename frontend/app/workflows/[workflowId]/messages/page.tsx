'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Grid, OperationPanel } from '@/components/ui/LiveFeature';
import {
  PageShell, PageHeader, QueryPanel, Button, Card, EmptyState,
} from '@/components/ui/WorkbenchUI';

export default function WorkflowMessagesPage() {
  const params = useParams();
  const workflowId = String(params?.workflowId || '');

  return (
    <PageShell>
      <PageHeader
        eyebrow="Engagement · Messages"
        title="Workflow messages"
        description="Draft and edit the messages prepared for this client workflow"
        actions={
          <>
            <Link href="/messages"><Button>All messages</Button></Link>
            <Link href={`/workflows/${workflowId}`}><Button>Workflow detail</Button></Link>
          </>
        }
      />

      {!workflowId ? (
        <Card><EmptyState title="No workflow selected" detail="Open a workflow from the Workflows page first." /></Card>
      ) : (
        <>
          <QueryPanel
            key={workflowId}
            title="Message artifacts"
            subtitle="Messages prepared for this workflow"
            method="GET"
            path={`/workflows/${workflowId}/messages`}
            rowsOf={(d: any) => (Array.isArray(d) ? d : d?.messages || d?.items || [])}
            emptyTitle="No message drafts"
            emptyDetail="Generate a draft below."
          />
          <div className="mt-5">
            <Grid>
              <OperationPanel
                title="Generate message draft"
                subtitle="Draft a new client message"
                method="POST"
                path={`/workflows/${workflowId}/messages`}
                bodyDefault={JSON.stringify({
                  mode: 'FOLLOWUP', channel: 'EMAIL',
                  template_ref: { id: 'client-followup', revision: '1', hash: 'local' },
                }, null, 2)}
              />
              <OperationPanel
                title="Edit message artifact"
                subtitle="Edit a drafted message"
                method="PATCH"
                path={(v) => `/workflows/messages/${v.aid}`}
                params={[{ name: 'aid', label: 'Message', in: 'path', placeholder: 'Document reference' }]}
                bodyDefault={JSON.stringify({
                  recipients: ['client@example.com'],
                  subject: 'Follow-up from your relationship manager',
                  body: 'Hello, following up on our recent discussion.',
                }, null, 2)}
              />
            </Grid>
          </div>
        </>
      )}
    </PageShell>
  );
}
