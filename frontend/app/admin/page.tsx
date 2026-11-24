'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { endpoints } from '@/lib/endpoints';
import { useApp } from '@/lib/app-context';
import { FeaturePage } from '@/components/ui/LiveFeature';
import {
  Card, Button, DataTable, ErrorState, Loading, StatusBadge, StatCard, EmptyState,
} from '@/components/ui/WorkbenchUI';

const QUICK_LINKS = [
  { href: '/admin/audit', label: 'Audit trail', description: 'Immutable audit events' },
  { href: '/admin/telemetry', label: 'Telemetry', description: 'Metrics and event recording' },
  { href: '/admin/artifacts', label: 'Artifacts', description: 'Lineage and revisions' },
  { href: '/admin/skills', label: 'Skill registry', description: 'Workflow skills and stage runs' },
  { href: '/admin/session', label: 'Session & identity', description: 'Live principal and permissions' },
  { href: '/admin/catalogue', label: 'Developer reference', description: 'Technical tool for administrators' },
];

export default function AdminDashboardPage() {
  const app = useApp();
  const [gates, setGates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    endpoints.admin.gates(app.tenantId || undefined)
      .then((r: any) => { setGates(r.data?.gates || []); setError(null); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (app.ready) load(); }, [app.ready, app.tenantId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = async (gate: any) => {
    setBusy(gate.key);
    try {
      await endpoints.admin.updateGate(gate.key, { enabled: !gate.enabled }, app.tenantId || undefined);
      load();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  return (
    <FeaturePage
      eyebrow="Platform"
      title="Decision Gates"
      description="Live capability switches. Toggling a gate writes to the configuration service and unlocks the corresponding feature pages."
      wide
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Gates" value={gates.length} sub="Configuration revisions" />
        <StatCard label="Enabled" value={gates.filter((g) => g.enabled).length} sub="Active capabilities" />
        <StatCard label="Clients" value={app.clients.length} sub="Live client book" />
        <StatCard label="Workflows" value={app.workflows.length} sub="Live instances" />
      </div>

      <Card title="Capability gates" subtitle="Live capability switches" bodyClassName="p-0">
        <div className="p-5">
          {loading ? <Loading /> : error ? <ErrorState error={error} onRetry={load} /> : gates.length === 0 ? (
            <EmptyState title="No switches configured" detail="No capability switches have been set up for this organisation." />
          ) : (
            <DataTable
              rows={gates}
              columns={[
                { key: 'key', label: 'Gate' },
                {
                  key: 'scope', label: 'Scope', render: (g: any) => {
                    const book = g.scope?.book_id;
                    const jurisdiction = g.scope?.jurisdiction;
                    const label = [book, jurisdiction].filter(Boolean).join(' · ');
                    return <span className="text-xs text-gray-600">{label || 'Organisation'}</span>;
                  },
                },
                {
                  key: 'enabled', label: 'State', render: (g: any) => (
                    <StatusBadge tone={g.enabled ? 'success' : 'neutral'}>{g.enabled ? 'Enabled' : 'Disabled'}</StatusBadge>
                  ),
                },
                { key: 'updated_at', label: 'Last updated' },
                {
                  key: 'action', label: '', render: (g: any) => (
                    <Button loading={busy === g.key} onClick={() => void toggle(g)}>
                      {g.enabled ? 'Disable' : 'Enable'}
                    </Button>
                  ),
                },
              ]}
            />
          )}
        </div>
      </Card>

      <Card title="Platform workspaces" subtitle="Every administrative capability has its own page">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {QUICK_LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="border border-gray-200 rounded px-4 py-3 hover:border-gray-500 transition-colors">
              <div className="text-sm font-semibold text-black">{l.label} →</div>
              <div className="text-xs text-gray-500 mt-1">{l.description}</div>
            </Link>
          ))}
        </div>
      </Card>
    </FeaturePage>
  );
}
