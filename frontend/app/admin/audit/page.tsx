'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll, Card, StatusBadge } from '@/components/ui/WorkbenchUI';

export default function AuditLogPage() {
  const app = useApp();
  return (
    <FeaturePage
      eyebrow="Platform"
      title="Audit Trail"
      description="Search the permanent change log. Filters are applied to the stored record, so the table only shows real events."
      wide
      actions={<ViewAll href="/admin/telemetry" label="Telemetry" />}
    >
      <QueryPanel
        key={app.tenantId}
        title="Audit events"
        subtitle="Search the permanent change log"
        method="GET"
        path="/admin/audit"
        params={[
          { name: 'tenant_id', label: 'Tenant', in: 'query', default: app.tenantId },
          { name: 'limit', label: 'Limit', in: 'query', type: 'number', default: '100' },
          { name: 'action', label: 'Action', in: 'query', placeholder: 'Optional filter' },
          { name: 'from_time', label: 'From', in: 'query', placeholder: '2026-01-01T00:00:00Z' },
          { name: 'to_time', label: 'To', in: 'query', placeholder: '2027-01-01T00:00:00Z' },
        ]}
        rowsOf={(d: any) => d?.events || []}
        columns={[
          { key: 'timestamp', label: 'When' },
          { key: 'actor', label: 'Actor' },
          { key: 'action', label: 'Action' },
          { key: 'resource_type', label: 'Resource' },
          {
            key: 'outcome', label: 'Outcome', render: (r: any) => (
              <StatusBadge tone={r.outcome === 'failure' ? 'error' : 'success'}>{r.outcome || 'success'}</StatusBadge>
            ),
          },
        ]}
        emptyTitle="No audit events"
        emptyDetail="Events are written when configuration gates, actions and briefs change state."
      />

      <Card title="About this log" subtitle="Data provenance">
        <p className="text-xs text-gray-600 leading-relaxed">
          The audit service records configuration changes, action previews, authorisations and execution attempts.
          Empty results mean no events have been recorded for the selected tenant and time range — the UI does not
          synthesise entries. Ask an administrator if you need additional filters.
        </p>
      </Card>
    </FeaturePage>
  );
}
