'use client';

import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid, contextParam } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

/**
 * Client Memory workspace.
 *
 * All read panels auto-load on mount and whenever the live client changes.
 * The proposal form is the only block with a button: POST writes a row, so it
 * must stay behind an explicit click (auto-firing it would create a duplicate
 * proposal on every page visit).
 */
export default function MemoryPage() {
  const app = useApp();
  const cid = contextParam('cid', 'Client', app.clientId, app.clientOptions);

  return (
    <FeaturePage
      eyebrow="Clients & Relationships"
      title="Client Memory"
      description="Confirmed client facts, proposals awaiting review, and the meeting / call history they came from."
      context={['client']}
      actions={<ViewAll href="/relationships" label="Relationships" />}
    >
      <Grid>
        <QueryPanel
          key={`mem-${app.clientId}`}
          title="Memory for client"
          subtitle="Confirmed facts held about this client"
          method="GET"
          path={(v) => `/clients/${v.cid}/memory`}
          params={[cid]}
          autoKey={app.clientId}
          columns={[
            { key: 'entry_type', label: 'Type', width: '112px' },
            { key: 'content', label: 'Fact' },
            { key: 'confidence', label: 'Confidence', width: '104px' },
          ]}
          emptyTitle="No confirmed memory yet"
          emptyDetail="Confirmed facts appear here. Pending suggestions are shown below."
        />
        <QueryPanel
          key={`propose-${app.clientId}`}
          title="Propose memory entry"
          subtitle="Suggest a new fact for RM review"
          method="POST"
          path={(v) => `/clients/${v.cid}/memory/proposals`}
          params={[
            cid,
            { name: 'kind', label: 'Entry type', in: 'body', type: 'select', default: 'PREFERENCE', options: [
              { value: 'PREFERENCE', label: 'Preference' }, { value: 'FACT', label: 'Fact' },
              { value: 'CONSTRAINT', label: 'Constraint' }, { value: 'GOAL', label: 'Goal' },
            ] },
            {
              name: 'content',
              label: 'Content',
              in: 'body',
              default: 'Prefers a short written recap after each call',
              placeholder: 'e.g. Prefers quarterly reviews',
            },
            // Must be `source_ref`, not `sourceRef`: body params are merged into
            // the payload by their exact name, and the API forbids extra keys.
            { name: 'source_ref', label: 'Source', in: 'body', default: 'Relationship manager note', advanced: true },
          ]}
          body={(v) => ({ kind: v.kind, content: v.content, source_ref: v.source_ref })}
          auto={false}
          actionLabel="Submit proposal"
          emptyTitle="Not submitted yet"
          emptyDetail="Use Submit proposal to create a NEEDS_REVIEW entry."
        />
      </Grid>

      <Grid>
        <QueryPanel
          key={`pending-${app.clientId}`}
          title="Pending proposals"
          subtitle="Suggestions awaiting RM review — not yet facts"
          method="GET"
          path={(v) => `/clients/${v.cid}/memory/proposals`}
          params={[cid]}
          autoKey={app.clientId}
          columns={[
            { key: 'entry_type', label: 'Type', width: '112px' },
            { key: 'content', label: 'Suggested fact' },
            { key: 'state', label: 'State', width: '140px' },
            { key: 'proposed_by', label: 'Proposed by' },
          ]}
          emptyTitle="No pending proposals"
          emptyDetail="New suggestions appear here until an RM reviews them."
        />
        <QueryPanel
          key={`conversations-${app.clientId}`}
          title="Conversation history"
          subtitle="Meetings and calls the memory facts were drawn from"
          method="GET"
          path={(v) => `/clients/${v.cid}/conversations`}
          params={[cid]}
          autoKey={app.clientId}
          columns={[
            { key: 'interaction_date', label: 'Date', width: '150px' },
            { key: 'interaction_type', label: 'Channel', width: '96px' },
            { key: 'summary', label: 'Summary' },
            { key: 'confidence', label: 'Confidence', width: '100px' },
          ]}
          emptyTitle="No conversations recorded"
          emptyDetail="Meeting and call notes for this client will appear here."
        />
      </Grid>
    </FeaturePage>
  );
}
