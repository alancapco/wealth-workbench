'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

export default function SkillsPage() {
  const app = useApp();
  return (
    <FeaturePage
      eyebrow="Platform"
      title="Skill Registry & Stage Runs"
      description="Registered workflow skills, live workflow instances and stage-run detail."
      context={['book', 'workflow']}
      actions={<ViewAll href="/workflows" label="Workflow workspace" />}
    >
      <Grid>
        <QueryPanel
          title="Registered skills"
          subtitle="Skills available to workflows"
          method="GET"
          path="/workflow/skills"
          rowsOf={(d: any) => d?.items || []}
          emptyTitle="No skills registered"
          emptyDetail="Skills are seeded when the workflow registry is initialised."
        />
        <QueryPanel
          key={app.bookId}
          title="Workflow instances"
          subtitle="Workflows in the selected book"
          method="GET"
          path="/workflow"
          params={[{ name: 'book_id', label: 'Book', in: 'query', default: app.bookId }]}
          rowsOf={(d: any) => d?.items || []}
          emptyTitle="No workflows yet"
          emptyDetail="Create one from the Workflows page."
        />
      </Grid>

      <Grid>
        <QueryPanel
          key={app.workflowId}
          title="Workflow detail"
          subtitle="Details of the selected workflow"
          method="GET"
          path={(v) => `/workflow/${v.wid}`}
          params={[{
            name: 'wid', label: 'Workflow', in: 'path', type: 'select',
            default: app.workflowId, options: app.workflowOptions,
          }]}
          auto={false}
        />
        <QueryPanel
          title="Stage run detail"
          subtitle="Outcome of this workflow step"
          method="GET"
          path={(v) => `/workflow/${v.wid}/runs/${v.runId}`}
          params={[
            { name: 'wid', label: 'Workflow', in: 'path', default: app.workflowId },
            { name: 'runId', label: 'Run reference', in: 'path', placeholder: 'Stage run reference' },
          ]}
          auto={false}
          emptyTitle="Enter a workflow and run ID"
        />
      </Grid>
    </FeaturePage>
  );
}
