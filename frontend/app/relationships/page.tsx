'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';
import FamilyGraphPanel from '@/components/FamilyGraphPanel';

export default function RelationshipsPage() {
  const app = useApp();
  const cid = contextParam('cid', 'Client', app.clientId, app.clientOptions);
  const wid = contextParam('wid', 'Workflow', app.workflowId, app.workflowOptions);

  return (
    <FeaturePage
      eyebrow="Clients & Relationships"
      title="Relationships & Households"
      description="Family relationships, household groups and household context. Gated capabilities report their real gate state instead of showing sample data."
      context={['client', 'workflow']}
      actions={<ViewAll href="/memory" label="Client memory" />}
    >
      <Grid>
        <QueryPanel
          key={`rel-${app.clientId}`}
          title="Client relationships"
          subtitle="Family and business connections"
          method="GET"
          path={(v) => `/clients/${v.cid}/relationships`}
          params={[cid]}
          emptyTitle="No relationships recorded"
          emptyDetail="Add a relationship using the form below."
        />
        <FamilyGraphPanel clientId={app.clientId} title="Family graph" subtitle="Household structure from live ownership and relationship data" />
      </Grid>

      <Grid>
        <QueryPanel
          title="Add relationship"
          subtitle="Link two clients, once family graph is enabled"
          method="POST"
          path={(v) => `/clients/${v.cid}/relationships`}
          params={[
            cid,
            { name: 'relatedId', label: 'Related client', in: 'body', placeholder: 'Client reference' },
            { name: 'relation', label: 'Relationship', in: 'body', type: 'select', default: 'SPOUSE', options: [
              { value: 'SPOUSE', label: 'Spouse' }, { value: 'CHILD', label: 'Child' },
              { value: 'PARENT', label: 'Parent' }, { value: 'SIBLING', label: 'Sibling' },
              { value: 'OTHER', label: 'Other' },
            ] },
          ]}
          body={(v) => ({ client_b_id: v.relatedId, relationship_type: v.relation })}
          auto={false}
        />
        <QueryPanel
          title="Household context"
          subtitle="Shared household context, once households are enabled"
          method="GET"
          path={(v) => `/workflows/${v.wid}/household-context`}
          params={[wid]}
          auto={false}
          emptyTitle="Enter a workflow and run"
        />
      </Grid>

      <Grid>
        <QueryPanel
          title="Create household"
          subtitle="Create a household, once households are enabled"
          method="POST"
          path="/households"
          params={[
            { name: 'name', label: 'Household name', in: 'body', default: '', placeholder: 'e.g. Tan Family Office' },
            { name: 'primaryClientId', label: 'Primary client', in: 'body', default: app.clientId },
          ]}
          body={(v) => ({ household_name: v.name, primary_contact_id: v.primaryClientId })}
          auto={false}
        />
        <QueryPanel
          title="Add household member"
          subtitle="Add someone to a household, once enabled"
          method="POST"
          path={(v) => `/households/${v.hid}/members`}
          params={[
            { name: 'hid', label: 'Household', in: 'path', placeholder: 'Household reference' },
            { name: 'clientId', label: 'Client', in: 'body', default: app.clientId },
            { name: 'role', label: 'Role', in: 'body', default: 'MEMBER' },
          ]}
          body={(v) => ({ client_id: v.clientId, role: v.role })}
          auto={false}
        />
      </Grid>
    </FeaturePage>
  );
}
