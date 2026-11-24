'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll, Card, StatusBadge } from '@/components/ui/WorkbenchUI';

export default function SessionPage() {
  const app = useApp();
  return (
    <FeaturePage
      eyebrow="Platform"
      title="Session & Identity"
      description="Your current sign-in: permissions, books, environment and access level. Every screen uses this same sign-in."
      actions={<ViewAll href="/admin" label="Decision gates" />}
    >
      <Grid>
        <QueryPanel
          title="Current session"
          subtitle="Your sign-in and permissions"
          method="GET"
          path="/session"
        />
        <Card title="Session summary" subtitle="Your current sign-in and access context">
          <dl className="space-y-3 text-xs">
            {[
              ['Display name', app.session?.display_name],
              ['Subject', app.session?.subject],
              ['Tenant', app.session?.tenant_id],
              ['Environment', app.session?.environment?.kind],
              ['Device state', app.session?.device_state],
              ['Expires', app.session?.session_expires_at],
              ['Books', app.session?.books?.map((b) => b.display_name).join(', ')],
            ].map(([k, v]) => (
              <div key={k as string} className="flex flex-wrap gap-3 border-b border-gray-100 pb-2 last:border-0">
                <dt className="w-36 shrink-0 text-gray-500">{k}</dt>
                <dd className="text-black break-all">{v ? String(v) : '—'}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {(app.session?.permissions || []).map((p) => (
              <StatusBadge key={p}>{p}</StatusBadge>
            ))}
          </div>
        </Card>
      </Grid>

      <QueryPanel
        title="Capability gates for this tenant"
        subtitle="Which capabilities are switched on"
        method="GET"
        path="/admin/config/gates"
        params={[{ name: 'tenant_id', label: 'Tenant', in: 'query', default: app.tenantId }]}
        rowsOf={(d: any) => d?.gates || []}
      />
    </FeaturePage>
  );
}
