'use client';

import { FeaturePage, Grid, OperationPanel } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

// Fixed defaults keep the server and client renders identical. A module-level
// new Date() is evaluated at different moments on each side and breaks hydration.
const DEFAULT_FROM = '2020-01-01T00:00:00Z';
const DEFAULT_TO = '2030-12-31T23:59:59Z';

export default function TelemetryPage() {
  return (
    <FeaturePage
      eyebrow="Platform"
      title="Telemetry"
      description="Review activity volumes and timings, or record a new system event. An empty result means nothing has been recorded for the selected period."
      actions={<ViewAll href="/admin/audit" label="Audit trail" />}
    >
      <Grid>
        <QueryPanel
          title="Metric aggregates"
          subtitle="Activity volumes and timings over the selected period"
          method="GET"
          path="/admin/telemetry/metrics"
          params={[
            { name: 'metric_name', label: 'Activity type', in: 'query', default: 'latency' },
            { name: 'from_time', label: 'From', in: 'query', default: DEFAULT_FROM },
            { name: 'to_time', label: 'To', in: 'query', default: DEFAULT_TO },
          ]}
        />
        <OperationPanel
          title="Record telemetry event"
          subtitle="Record a system activity event"
          method="POST"
          path="/telemetry/telemetry/events"
          bodyDefault={JSON.stringify({
            event_type: 'latency',
            labels: { screen: 'workbench-ui' },
            value: 1,
          }, null, 2)}
        />
      </Grid>
    </FeaturePage>
  );
}
