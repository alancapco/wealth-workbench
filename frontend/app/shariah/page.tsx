'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

export default function ShariahPage() {
  const app = useApp();
  const cid = contextParam('cid', 'Client', app.clientId, app.clientOptions);
  const wid = contextParam('wid', 'Workflow', app.workflowId, app.workflowOptions);

  return (
    <FeaturePage
      eyebrow="Advice & Execution"
      title="Shariah Screening"
      description="Preliminary technical screening estimates based on AAOIFI evidence, evidence retrieval and the live client screening report. These are not religious rulings. Availability depends on the religious-screening setting."
      context={['client', 'workflow']}
      actions={<ViewAll href="/admin" label="Manage gates" />}
    >
      {/* Legal framing must stay visible even when a query fails or returns no data. */}
      <div className="border border-gray-300 bg-gray-50 rounded-xl p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-700 mb-1">
          Preliminary technical assessment — not a religious ruling
        </p>
        <p className="text-xs text-gray-600 leading-relaxed">
          This is a preliminary technical estimate based on available AAOIFI evidence. It is NOT a fatwa,
          religious authority ruling, or compliance approval. Consult qualified Shariah scholars before
          making investment decisions.
        </p>
      </div>

      <QueryPanel
        title="Pilot gate state"
        subtitle="Check whether religious screening is switched on"
        method="GET"
        path="/admin/config/gates"
        params={[{ name: 'tenant_id', label: 'Tenant', in: 'query', default: app.tenantId }]}
        rowsOf={(d: any) => (d?.gates || []).filter((g: any) => String(g.key).startsWith('DEC-05'))}
        columns={[
          { key: 'key', label: 'Gate' },
          { key: 'enabled', label: 'Enabled', render: (r: any) => (r.enabled ? 'Yes' : 'No') },
          { key: 'updated_at', label: 'Updated' },
        ]}
      />

      <Grid>
        <QueryPanel
          key={`report-${app.clientId}`}
          title="Client screening report"
          subtitle="Preliminary technical assessment for this client — not a religious ruling"
          method="GET"
          path={(v) => `/clients/${v.cid}/shariah-report`}
          params={[cid]}
          emptyTitle="No compliance report"
          emptyDetail="The report is derived from the client's holdings in the database."
        />
        <QueryPanel
          title="Evidence for product"
          subtitle="Supporting evidence for this product"
          method="GET"
          path={(v) => `/workflows/shariah/evidence/${encodeURIComponent(v.ref)}/`.replace(/\/$/, '')}
          params={[{ name: 'ref', label: 'Product reference', in: 'path', default: 'FUND-001', placeholder: 'e.g. FUND-001' }]}
          auto={false}
          emptyTitle="Enter a product reference and run"
        />
      </Grid>

      <OperationPanel
        title="Generate preliminary technical estimate"
        subtitle="Not a religious ruling; requires screening to be enabled"
        method="POST"
        path={(v) => `/workflows/${v.wid}/shariah/estimates`}
        params={[wid]}
        bodyDefault={JSON.stringify({ product_ref: 'FUND-001' }, null, 2)}
      />
    </FeaturePage>
  );
}
