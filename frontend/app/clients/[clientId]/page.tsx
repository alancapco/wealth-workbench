'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { endpoints } from '@/lib/endpoints';
import { useApp } from '@/lib/app-context';
import { Grid } from '@/components/ui/LiveFeature';
import {
  PageShell, PageHeader, Card, StatCard, Loading, ErrorState,
  QueryPanel, DataView, Button,
} from '@/components/ui/WorkbenchUI';
import FamilyGraphPanel from '@/components/FamilyGraphPanel';
import { money } from '@/lib/format';

export default function ClientDetailPage() {
  const params = useParams();
  const clientId = String(params?.clientId || '');
  const app = useApp();
  const [client, setClient] = useState<any>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    endpoints.clients.detail(clientId)
      .then((r: any) => { setClient(r.data?.client || r.data); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (clientId) load(); }, [clientId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (clientId && app.clientId !== clientId) app.setClientId(clientId); }, [clientId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Show the client record in the language a relationship manager uses, rather
  // than exposing internal identifiers and database column names.
  const clientRecord = client
    ? {
        Name: client.name,
        'Client type': client.client_type,
        Region: client.region,
        'Risk profile': client.risk_profile,
        'Base currency': client.currency,
        'Assets under management': money(client.aum, client.currency),
        'Shariah preference': client.shariah_compliant ? 'Shariah-compliant' : 'Standard',
        'Family office': client.is_family_office ? 'Yes' : 'No',
        Email: client.email,
        Phone: client.phone,
        'Record created': client.created_at,
      }
    : null;

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Clients & Relationships · Client profile"
        title={client?.name || 'Client profile'}
        description={
          [client?.client_type, client?.region, client?.risk_profile ? `${client.risk_profile} risk profile` : null]
            .filter(Boolean)
            .join(' · ') || 'Holdings, memory, relationships and briefs for this client'
        }
        actions={
          <>
            <Link href="/clients"><Button>← Client book</Button></Link>
            <Link href={`/brief/${clientId}`}><Button variant="primary">Generate brief</Button></Link>
          </>
        }
      />

      {loading ? <Card><Loading /></Card> : error ? <ErrorState error={error} onRetry={load} /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-5">
            <StatCard label="AUM" value={money(client?.aum, client?.currency)} sub={client?.currency} />
            <StatCard label="Risk profile" value={client?.risk_profile || '—'} sub={client?.client_type} />
            <StatCard label="Region" value={client?.region || '—'} sub={client?.email} />
            <StatCard label="Family office" value={client?.is_family_office ? 'Yes' : 'No'} sub={client?.phone} />
            <StatCard label="Shariah" value={client?.shariah_compliant ? 'Compliant' : 'Standard'} sub={client?.preferences?.shariah_standard || '—'} />
          </div>

          <Grid>
            <QueryPanel
              key={`portfolio-${clientId}`}
              title="Portfolio"
              subtitle="Holdings and allocation for this client"
              method="GET"
              path={`/clients/${clientId}/portfolio`}
            />
            <QueryPanel
              key={`memory-${clientId}`}
              title="Client memory"
              subtitle="Facts and preferences remembered for this client"
              method="GET"
              path={`/clients/${clientId}/memory`}
              emptyTitle="No memory entries"
              emptyDetail="Propose one from the Client Memory workspace."
            />
          </Grid>

          <Grid>
            <QueryPanel
              key={`rel-${clientId}`}
              title="Relationships"
              subtitle="Family and business connections"
              method="GET"
              path={`/clients/${clientId}/relationships`}
              emptyTitle="No relationships recorded"
            />
            <FamilyGraphPanel clientId={clientId} title="Family graph" subtitle="Household structure from live ownership and relationship data" />
          </Grid>

          <Grid>
            <QueryPanel
              key={`shariah-${clientId}`}
              title="Shariah compliance report"
              subtitle="Religious-compliance status for this client"
              method="GET"
              path={`/clients/${clientId}/shariah-report`}
              emptyTitle="No compliance report"
            />
            <QueryPanel
              key={`briefs-${clientId}`}
              title="Briefs for this client"
              subtitle="Briefs prepared for this client"
              method="GET"
              path="/briefs"
              buildQuery={() => ({ client_id: clientId })}
              emptyTitle="No briefs yet"
              emptyDetail="Generate one from the Client Briefs workspace."
            />
          </Grid>

          <Card title="Client record" subtitle="All details held for this client">
            <DataView data={clientRecord} />
          </Card>
        </>
      )}
    </PageShell>
  );
}
