'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, OperationPanel, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll, SectionLabel } from '@/components/ui/WorkbenchUI';

const REF = {
  artifact_id: '00000000-0000-0000-0000-000000000000',
  revision_id: '00000000-0000-0000-0000-000000000000',
  version: 1,
  hash: '0000000000000000000000000000000000000000000000000000000000000000',
};

export default function AdvicePage() {
  const app = useApp();
  const wid = contextParam('wid', 'Workflow', app.workflowId, app.workflowOptions);

  return (
    <FeaturePage
      eyebrow="Advice & Execution"
      title="Products & Suitability"
      description="From understanding what the client needs, through product search and comparison, to suitability assessment and a justified override. Each step picks up the work of the previous one."
      context={['workflow', 'client']}
      wide
      actions={<ViewAll href="/admin" label="Capability settings" />}
    >
      <QueryPanel
        title="Capability state"
        subtitle="Check whether the product catalogue is switched on"
        method="GET"
        path="/admin/config/gates"
        params={[{ name: 'tenant_id', label: 'Tenant', in: 'query', default: app.tenantId }]}
        rowsOf={(d: any) => (d?.gates || []).filter((g: any) => String(g.key).startsWith('DEC-04'))}
        columns={[
          { key: 'key', label: 'Gate' },
          { key: 'enabled', label: 'Enabled', render: (r: any) => (r.enabled ? 'Yes' : 'No') },
          { key: 'updated_at', label: 'Updated' },
        ]}
        emptyTitle="No product catalogue gate configured"
      />

      <SectionLabel>1 · Interpret and confirm</SectionLabel>
      <Grid>
        <OperationPanel
          title="Interpret client query"
          subtitle="Interpret what the client is looking for"
          method="POST"
          path={(v) => `/products/${v.wid}/interpretations`}
          params={[wid]}
          bodyDefault={JSON.stringify({ query: 'Low risk USD income funds with quarterly liquidity' }, null, 2)}
        />
        <OperationPanel
          title="Edit filters on interpretation artifact"
          subtitle="Refine the product search criteria"
          method="PATCH"
          path={(v) => `/products/artifacts/${v.aid}/filters`}
          params={[{ name: 'aid', label: 'Interpretation', in: 'path', placeholder: 'Document reference' }]}
          bodyDefault={JSON.stringify({ filters: [], confirmation: true }, null, 2)}
        />
      </Grid>

      <SectionLabel>2 · Search and compare</SectionLabel>
      <Grid>
        <OperationPanel
          title="Search entitled products"
          subtitle="Search the product catalogue"
          method="POST"
          path={(v) => `/products/${v.wid}/searches`}
          params={[wid]}
          bodyDefault={JSON.stringify({ interpretation_ref: REF, confirmation: true }, null, 2)}
        />
        <OperationPanel
          title="Compare products"
          subtitle="Compare shortlisted products"
          method="POST"
          path={(v) => `/products/${v.wid}/comparisons`}
          params={[wid]}
          bodyDefault={JSON.stringify({ search_ref: REF, product_refs: [{ id: 'FUND-001', version: '1' }] }, null, 2)}
        />
      </Grid>

      <SectionLabel>3 · Select, assess and override</SectionLabel>
      <Grid>
        <OperationPanel
          title="Select candidate"
          subtitle="Select products for the client"
          method="POST"
          path={(v) => `/products/${v.wid}/selections`}
          params={[wid]}
          bodyDefault={JSON.stringify({ search_ref: REF, product_ref: { id: 'FUND-001', version: '1' }, confirmation: true }, null, 2)}
        />
        <OperationPanel
          title="Assess suitability"
          subtitle="Assess suitability for this client"
          method="POST"
          path={(v) => `/products/${v.wid}/assessments`}
          params={[wid]}
          bodyDefault={JSON.stringify({ product_ref: { id: 'FUND-001', version: '1' } }, null, 2)}
        />
      </Grid>

      <OperationPanel
        title="Override a soft suitability factor"
        subtitle="Record a justified override to a suitability result"
        method="POST"
        path={(v) => `/products/assessments/${v.aid}/overrides`}
        params={[{ name: 'aid', label: 'Assessment', in: 'path', placeholder: 'Assessment reference' }]}
        bodyDefault={JSON.stringify({
          assessment_ref: REF,
          factor_keys: ['liquidity'],
          reason: 'CLIENT_INSTRUCTION',
          rationale: 'Client explicitly accepts lower liquidity',
          confirmation: true,
        }, null, 2)}
      />
    </FeaturePage>
  );
}
