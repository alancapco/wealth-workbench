'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { endpoints } from '@/lib/endpoints';
import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import {
  Card, DataTable, ErrorState, Loading, TextInput, Button, ViewAll,
  StatusBadge, EmptyState,
} from '@/components/ui/WorkbenchUI';
import { money } from '@/lib/format';

export default function ClientsPage() {
  const app = useApp();
  const [clients, setClients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [search, setSearch] = useState('');

  const load = () => {
    setLoading(true);
    endpoints.clients.list()
      .then((r: any) => { setClients(r.data?.clients || []); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return clients;
    return clients.filter((c) =>
      [c.name, c.external_id, c.email, c.region, c.client_type, c.risk_profile]
        .filter(Boolean).some((v: unknown) => String(v).toLowerCase().includes(q)),
    );
  }, [clients, search]);

  return (
    <FeaturePage
      eyebrow="Clients & Relationships"
      title="Client Book"
      description={`${clients.length} clients loaded from the live client service. Select a client to work across every feature.`}
      wide
      actions={
        <>
          <ViewAll href="/relationships" label="Relationships" />
          <ViewAll href="/briefs" label="Client briefs" />
        </>
      }
    >
      <Card title="All clients" subtitle="Everyone in your book" bodyClassName="p-0">
        <div className="px-5 py-3 border-b border-gray-200 flex flex-wrap items-center gap-3">
          <TextInput value={search} onChange={setSearch} placeholder="Filter by name, region, segment…" className="max-w-sm" />
          <span className="text-xs text-gray-400">{rows.length} of {clients.length} shown</span>
          <div className="flex-1" />
          <Button onClick={load}>Refresh</Button>
        </div>
        <div className="p-5">
          {loading ? <Loading /> : error ? <ErrorState error={error} onRetry={load} /> : (
            <DataTable
              emptyTitle="No clients in the book"
              emptyDetail="Load the client seed data into the database to populate this table."
              rows={rows}
              columns={[
                {
                  key: 'name', label: 'Client', render: (c: any) => (
                    <Link href={`/clients/${c.id}`} className="font-medium text-black hover:underline">
                      {c.name}
                    </Link>
                  ),
                },
                { key: 'client_type', label: 'Segment' },
                { key: 'region', label: 'Region' },
                { key: 'risk_profile', label: 'Risk profile' },
                { key: 'aum', label: 'AUM', align: 'right', render: (c: any) => money(c.aum, c.currency) },
                {
                  key: 'shariah_compliant', label: 'Shariah', render: (c: any) => (
                    <StatusBadge tone={c.shariah_compliant ? 'success' : 'neutral'}>
                      {c.shariah_compliant ? 'Yes' : 'No'}
                    </StatusBadge>
                  ),
                },
                {
                  key: 'actions', label: '', render: (c: any) => (
                    <div className="flex gap-2 whitespace-nowrap">
                      <Link href={`/clients/${c.id}`} className="text-xs text-gray-600 hover:text-black">Profile →</Link>
                      <Link href={`/brief/${c.id}`} className="text-xs text-gray-600 hover:text-black">Brief →</Link>
                    </div>
                  ),
                },
              ]}
            />
          )}
        </div>
      </Card>

      <Grid>
        <Card title="Selected client" subtitle="Shared across all feature workspaces">
          {app.clientId ? (
            <div className="space-y-3">
              <div className="text-lg font-semibold text-black">
                {app.clientOptions.find((o) => o.value === app.clientId)?.label}
              </div>
              <div className="flex flex-wrap gap-2">
                <Link href={`/clients/${app.clientId}`}><Button>Open profile</Button></Link>
                <Link href="/relationships"><Button>Relationships</Button></Link>
                <Link href="/memory"><Button>Client memory</Button></Link>
                <Link href="/briefs"><Button>Briefs</Button></Link>
              </div>
            </div>
          ) : <EmptyState title="No client selected" detail="Choose a client in the header or from the table." />}
        </Card>
        <Card title="Portfolio client book" subtitle="Clients with portfolio data">
          {app.demoClients.length === 0 ? (
            <EmptyState title="No portfolio clients" detail="The demo client table has no records." />
          ) : (
            <DataTable
              rows={app.demoClients.slice(0, 8)}
              columns={[
                { key: 'name', label: 'Client' },
                { key: 'client_segment', label: 'Segment' },
                { key: 'portfolio_type', label: 'Portfolio' },
                { key: 'aum_usd_millions', label: 'AUM (USD M)', align: 'right' },
              ]}
            />
          )}
        </Card>
      </Grid>
    </FeaturePage>
  );
}
