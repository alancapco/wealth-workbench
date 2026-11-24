'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

export default function ArtifactsPage() {
  const app = useApp();
  return (
    <FeaturePage
      eyebrow="Platform"
      title="Artifacts"
      description="Inspect artifact lineage and revisions, apply edits, and review brief artifacts linked to a workflow."
      context={['workflow']}
      actions={<ViewAll href="/admin/catalogue" label="Developer reference" />}
    >
      <Grid>
        <QueryPanel
          title="Artifact detail"
          subtitle="Version history and supporting evidence"
          method="GET"
          path={(v) => `/artifacts/artifacts/${v.aid}`}
          params={[{ name: 'aid', label: 'Document', in: 'path', placeholder: 'Document reference' }]}
          auto={false}
          emptyTitle="Enter an artifact ID and run"
        />
        <OperationPanel
          title="Edit artifact"
          subtitle="Create a new version of this document"
          method="PATCH"
          path={(v) => `/artifacts/artifacts/${v.aid}`}
          params={[{ name: 'aid', label: 'Document', in: 'path', placeholder: 'Document reference' }]}
          bodyDefault={JSON.stringify({ note: 'Reviewed in WM Workbench' }, null, 2)}
        />
      </Grid>

      <QueryPanel
        key={`wf-${app.workflowId}`}
        title="Briefs linked to workflow"
        subtitle="Briefs produced by this workflow"
        method="GET"
        path={(v) => `/briefs/workflows/${v.wid}/briefs`}
        params={[{
          name: 'wid', label: 'Workflow', in: 'path', type: 'select',
          default: app.workflowId, options: app.workflowOptions,
        }]}
        emptyTitle="No brief artifacts for this workflow"
      />
    </FeaturePage>
  );
}
