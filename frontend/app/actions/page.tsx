'use client';

import { useEffect, useState } from 'react';
import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel } from '@/components/ui/LiveFeature';
import { QueryPanel, SectionLabel } from '@/components/ui/WorkbenchUI';
import { get } from '@/lib/endpoints';

interface ArtifactRef {
  artifact_id: string;
  revision_id: string;
  version: number;
  hash: string;
}

const EMPTY_REF: ArtifactRef = { artifact_id: '', revision_id: '', version: 1, hash: '' };

export default function ActionsPage() {
  const app = useApp();
  const [artifactRef, setArtifactRef] = useState<ArtifactRef | null>(null);

  // POST /actions/preview resolves the client from a real artifact_revisions row;
  // a fabricated zero-UUID ref returns 404, so seed the form with a live brief ref.
  useEffect(() => {
    get('/briefs')
      .then((res) => {
        const briefs = Array.isArray(res.data) ? res.data : res.data?.briefs ?? [];
        setArtifactRef(briefs.find((b: any) => b?.artifact_ref?.artifact_id)?.artifact_ref ?? EMPTY_REF);
      })
      .catch(() => setArtifactRef(EMPTY_REF));
  }, []);

  const previewBody = JSON.stringify(
    { artifact_ref: artifactRef ?? EMPTY_REF, action_class: 'CRM_WRITE' },
    null,
    2,
  );

  return (
    <FeaturePage
      eyebrow="Advice & Execution"
      title="Actions & Approvals"
      description="Four-stage action control: preview → authorise → execute → status. Each step returns the identifiers needed by the next."
      context={['client', 'workflow']}
      wide
    >
      <SectionLabel>1 · Preview</SectionLabel>
      {artifactRef && !artifactRef.artifact_id && (
        <div className="border border-gray-300 bg-gray-50 rounded-xl p-4 text-xs text-gray-600">
          No brief artifact is available yet. Generate a brief on the Client Briefs page, then return
          here — the preview must reference a real artifact revision.
        </div>
      )}
      <OperationPanel
        key={artifactRef ? 'ref-ready' : 'ref-loading'}
        title="Create action preview"
        subtitle="Backed by a live brief artifact revision. Action class must be CRM_WRITE, TASK_WRITE, MEMORY_WRITE, CLIENT_SEND or TICKET_PREFILL."
        method="POST"
        path="/actions/preview"
        bodyDefault={previewBody}
      />

      <SectionLabel>2 · Authorise and execute</SectionLabel>
      <Grid>
        <OperationPanel
          title="Authorise preview"
          subtitle="Paste the preview_hash returned by Create action preview"
          method="POST"
          path={(v) => `/actions/${v.pid}/authorize`}
          params={[{ name: 'pid', label: 'Preview', in: 'path', placeholder: 'From the preview response', advanced: true }]}
          bodyDefault={JSON.stringify({ preview_hash: '', confirmation: true }, null, 2)}
        />
        <OperationPanel
          title="Execute action"
          subtitle="Paste the authorization id returned by Authorise preview"
          method="POST"
          path="/actions/execute"
          bodyDefault={JSON.stringify({ authorization_id: '' }, null, 2)}
        />
      </Grid>

      <SectionLabel>3 · Track</SectionLabel>
      <Grid>
        <QueryPanel
          title="Action status"
          subtitle="Current state of this action"
          method="GET"
          path={(v) => `/actions/${v.aid}`}
          params={[{ name: 'aid', label: 'Action', in: 'path', placeholder: 'From the action response', advanced: true }]}
          auto={false}
          emptyTitle="Enter an action ID and run"
        />
        <QueryPanel
          title="Recent audit events"
          subtitle="Permanent record of every change"
          method="GET"
          path="/admin/audit"
          params={[{ name: 'tenant_id', label: 'Tenant', in: 'query', default: app.tenantId }]}
          rowsOf={(d: any) => d?.events || []}
          emptyTitle="No audit events yet"
          emptyDetail="Executed actions will be recorded here."
        />
      </Grid>
    </FeaturePage>
  );
}
