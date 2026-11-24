'use client';

import { useState } from 'react';
import type { DateRange } from 'react-day-picker';
import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { DatePicker } from '@/components/ui/date-picker';
import { DateRangePicker } from '@/components/ui/date-range-picker';

export default function CalendarPage() {
  const app = useApp();
  const [singleDate, setSingleDate] = useState<Date | undefined>();
  const [range, setRange] = useState<DateRange | undefined>();

  // The live events endpoint accepts from_time / to_time. A range overrides the
  // single date so the two controls can never contradict each other.
  const fromIso = (range?.from ?? singleDate)?.toISOString() ?? '';
  const toIso = range?.to?.toISOString() ?? '';
  const hasFilter = Boolean(fromIso || toIso);

  const eventId = {
    name: 'eventId',
    label: 'Event',
    in: 'path' as const,
    placeholder: 'Calendar event reference',
  };

  return (
    <FeaturePage
      eyebrow="Engagement"
      title="Calendar & Meetings"
      description="Live calendar events, event resolutions and meeting records from the workflow database."
      context={['client', 'workflow']}
      actions={<ViewAll href="/capture" label="Meeting capture" />}
    >
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Reporting period</CardTitle>
          <CardDescription className="text-xs">
            Filter live calendar events by date. Dates are sent to the API as ISO timestamps; no events are cached locally.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-muted-foreground">From date</Label>
              <DatePicker value={singleDate} onChange={setSingleDate} placeholder="Pick a date" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-[11px] font-medium text-muted-foreground">Date range</Label>
              <DateRangePicker value={range} onChange={setRange} />
            </div>
            <div className="flex items-end gap-2 pb-0.5">
              <Button
                variant="outline"
                size="sm"
                disabled={!hasFilter}
                onClick={() => { setSingleDate(undefined); setRange(undefined); }}
              >
                Clear filter
              </Button>
              <span className="text-[11px] text-muted-foreground">
                {hasFilter ? 'Filter active' : 'Showing all periods'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <Grid>
        <QueryPanel
          title="Calendar events"
          subtitle="Appointments and meetings in the selected period"
          method="GET"
          path="/calendar/calendar/events"
          params={[{ name: 'limit', label: 'Limit', in: 'query', type: 'number', default: '50' }]}
          buildQuery={() => ({
            ...(fromIso ? { from_time: fromIso } : {}),
            ...(toIso ? { to_time: toIso } : {}),
          })}
          deps={[fromIso, toIso]}
          rowsOf={(d: any) => d?.items || d?.events || []}
          emptyTitle="No calendar events"
          emptyDetail="Events appear here once meetings are scheduled in the workflow system."
        />
        <QueryPanel
          title="Meeting detail"
          subtitle="Details of the selected meeting"
          method="GET"
          path={(v) => `/meetings/meetings/${v.meetingId}`}
          params={[{ name: 'meetingId', label: 'Meeting', in: 'path', placeholder: 'Meeting reference' }]}
          auto={false}
          emptyTitle="Enter a meeting ID and run"
        />
      </Grid>

      <QueryPanel
        title="Resolve a calendar event"
        subtitle="Record how this calendar conflict was resolved"
        method="POST"
        path={(v) => `/calendar/calendar/events/${v.eventId}/resolutions`}
        params={[
          eventId,
          { name: 'eventVersion', label: 'Event version', in: 'body', default: '1' },
          { name: 'clientId', label: 'Client', in: 'body', default: app.clientId, placeholder: 'Client reference' },
          { name: 'confirmation', label: 'Confirmation', in: 'body', type: 'select', default: 'true', options: [{ value: 'true', label: 'Confirmed' }, { value: 'false', label: 'Not confirmed' }] },
        ]}
        body={(v) => ({
          event_version: v.eventVersion,
          client_id: v.clientId,
          confirmation: v.confirmation === 'true',
        })}
        auto={false}
      />
    </FeaturePage>
  );
}
