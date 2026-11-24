'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

export default function MessagesPage() {
  const app = useApp();
  const wid = contextParam('wid', 'Workflow', app.workflowId, app.workflowOptions);

  return (
    <FeaturePage
      eyebrow="Engagement"
      title="Messages"
      description="Draft client messages against a workflow, then edit the message artifact. Approvals are handled through the action control flow."
      context={['workflow', 'client']}
      actions={<ViewAll href="/actions" label="Actions & approvals" />}
    >
      <QueryPanel
        key={`list-${app.workflowId}`}
        title="Workflow messages"
        subtitle="Messages prepared for this workflow"
        method="GET"
        path={(v) => `/workflows/${v.wid}/messages`}
        params={[wid]}
        rowsOf={(d: any) => (Array.isArray(d) ? d : d?.messages || d?.items || [])}
        emptyTitle="No message drafts"
        emptyDetail="Generate a draft below once a workflow is selected."
      />

      <Grid>
        <OperationPanel
          title="Generate message draft"
          subtitle="Draft a new client message"
          method="POST"
          path={(v) => `/workflows/${v.wid}/messages`}
          params={[wid]}
          bodyDefault={JSON.stringify({
            mode: 'FOLLOWUP',
            channel: 'EMAIL',
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
    </FeaturePage>
  );
}
