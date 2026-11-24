'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll, ParamSpec } from '@/components/ui/WorkbenchUI';

export default function BriefsPage() {
  const app = useApp();
  const clientQuery: ParamSpec[] = [
    { name: 'client_id', label: 'Client', in: 'query', type: 'select', default: app.clientId, options: app.clientOptions },
  ];
  const briefId: ParamSpec = { name: 'briefId', label: 'Brief', in: 'path', placeholder: 'Selected brief', advanced: true };

  return (
    <FeaturePage
      eyebrow="Advice & Execution"
      title="Client Briefs"
      description="Generate meeting briefs from live client holdings, then review and edit canonical brief artifacts."
      context={['client', 'workflow']}
      actions={<ViewAll href="/admin/artifacts" label="Version history" />}
    >
      <Grid>
        <QueryPanel
          key={`list-${app.clientId}`}
          title="Briefs for client"
          subtitle="All briefs prepared for your clients"
          method="GET"
          path="/briefs"
          params={clientQuery}
          emptyTitle="No briefs generated yet"
          emptyDetail="Generate a meeting brief below, or create a canonical brief artifact."
        />
        <QueryPanel
          key={`gen-${app.clientId}`}
          title="Generate meeting brief"
          subtitle="Build a brief from holdings, market data and recent conversations"
          method="POST"
          path="/briefs/generate"
          params={[
            contextParam('cid', 'Client', app.clientId, app.clientOptions),
            { name: 'force', label: 'Force regenerate', in: 'none', type: 'select', default: 'false', options: [{ value: 'false', label: 'No' }, { value: 'true', label: 'Yes' }] },
          ]}
          body={(v) => ({ client_id: v.cid, force_regenerate: v.force === 'true' })}
          rowsOf={(d: any) => (d?.brief ? [d.brief] : [])}
          emptyTitle="Brief unavailable"
          emptyDetail="The selected client needs a client record and holdings in the database."
        />
      </Grid>

      <Grid>
        <QueryPanel
          key={`wf-${app.workflowId}`}
          title="Briefs by workflow"
          subtitle="Briefs produced by this workflow"
          method="GET"
          path={(v) => `/briefs/workflows/${v.wid}/briefs`}
          params={[contextParam('wid', 'Workflow', app.workflowId, app.workflowOptions)]}
          emptyTitle="No workflows with briefs"
          emptyDetail="Create a workflow from the Workflows page first."
        />
        <QueryPanel
          title="Brief detail"
          subtitle="Open the selected brief"
          method="GET"
          path={(v) => `/briefs/briefs/${v.briefId}`}
          params={[briefId]}
          auto={false}
          emptyTitle="Enter a brief ID and run"
        />
      </Grid>

      <Grid>
        <QueryPanel
          title="Create canonical brief"
          subtitle="Create a brief without duplicating an earlier one"
          method="POST"
          path="/briefs/briefs"
          params={[
            { name: 'workflow_id', label: 'Workflow', in: 'body', default: app.workflowId, placeholder: 'Workflow reference' },
            { name: 'section_keys', label: 'Section keys (JSON)', in: 'body', type: 'json', default: '["portfolio_overview","material_changes"]' },
          ]}
          headers={() => ({ 'Idempotency-Key': `ui-brief-${Date.now()}` })}
          auto={false}
        />
        <QueryPanel
          title="Edit brief"
          subtitle="Edit the content of this brief"
          method="PATCH"
          path={(v) => `/briefs/briefs/${v.briefId}`}
          params={[
            briefId,
            { name: 'section_edits', label: 'Section edits (JSON)', in: 'body', type: 'json', default: '[{"key":"proposed_agenda","narrative":"Updated agenda"}]', placeholder: '[{"key":"...","narrative":"..."}]' },
            { name: 'reason', label: 'Reason', in: 'body', default: 'RM review update' },
          ]}
          auto={false}
        />
      </Grid>

      <QueryPanel
        title="Record section review"
        subtitle="Copy the four artifact_ref values from the brief detail response; a stale content hash returns 412"
        method="POST"
        path={(v) => `/briefs/briefs/${v.briefId}/reviews`}
        params={[
          briefId,
          { name: 'artifactId', label: 'Document', in: 'none', placeholder: 'From the brief response', advanced: true },
          { name: 'revisionId', label: 'Revision', in: 'none', placeholder: 'From the brief response', advanced: true },
          { name: 'version', label: 'Version', in: 'none', type: 'number', default: '1' },
          { name: 'hash', label: 'Content hash (sha256)', in: 'none', placeholder: 'artifact_ref.hash' },
          { name: 'sections', label: 'Sections (JSON)', in: 'body', type: 'json', default: '[]' },
        ]}
        body={(v) => ({
          artifact_ref: {
            artifact_id: v.artifactId,
            revision_id: v.revisionId,
            version: Number(v.version),
            hash: v.hash,
          },
        })}
        headers={(v) => ({ 'If-Match': `"${v.revisionId}:${v.hash}"` })}
        auto={false}
      />
    </FeaturePage>
  );
}
