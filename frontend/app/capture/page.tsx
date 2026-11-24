'use client';

import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import { QueryPanel, ViewAll } from '@/components/ui/WorkbenchUI';

const meeting: any = { name: 'meetingId', label: 'Meeting', in: 'path', placeholder: 'Selected meeting', advanced: true };
const consent: any = { name: 'consentId', label: 'Consent', in: 'path', placeholder: 'Selected consent', advanced: true };

export default function CapturePage() {
  return (
    <FeaturePage
      eyebrow="Engagement"
      title="Meeting Capture"
      description="Manage recording consent, capture sessions and transcript corrections for client meetings."
      context={['client']}
      actions={<ViewAll href="/calendar" label="Calendar & meetings" />}
    >
      <Grid>
        <QueryPanel
          title="Consent state"
          subtitle="Whether recording consent has been given"
          method="GET"
          path={(v) => `/meetings/${v.meetingId}/consent`}
          params={[meeting]}
          auto={false}
          emptyTitle="Enter a meeting ID and run"
        />
        <QueryPanel
          title="Start capture session"
          subtitle="Begin recording this meeting"
          method="POST"
          path={(v) => `/meetings/${v.meetingId}/capture/start`}
          params={[
            meeting,
            { name: 'consentId', label: 'Consent record', in: 'body', placeholder: 'Consent reference', default: '' },
            { name: 'policyRef', label: 'Policy ref (JSON)', in: 'body', type: 'json', default: '{"id":"policy-001","revision":"1","hash":"local"}' },
          ]}
          body={(v) => ({ consent_id: v.consentId, policy_ref: v.policyRef })}
          auto={false}
        />
      </Grid>

      <QueryPanel
        title="Record consent"
        subtitle="Record the client's consent decision and policy reference"
        method="POST"
        path={(v) => `/meetings/${v.meetingId}/consent`}
        params={[
          meeting,
          { name: 'policyRef', label: 'Policy ref (JSON)', in: 'body', type: 'json', default: '{"id":"policy-001","revision":"1","hash":"local"}' },
          { name: 'jurisdiction', label: 'Jurisdiction', in: 'body', default: 'HK' },
          { name: 'platform', label: 'Platform', in: 'body', default: 'workbench' },
          { name: 'language', label: 'Language', in: 'body', default: 'en' },
          { name: 'decision', label: 'Decision', in: 'body', type: 'select', default: 'ACCEPTED', options: [{ value: 'ACCEPTED', label: 'Accepted' }, { value: 'DECLINED', label: 'Declined' }] },
          { name: 'method', label: 'Method', in: 'body', default: 'explicit' },
          { name: 'participantRefs', label: 'Participant refs (JSON)', in: 'body', type: 'json', default: '[]' },
        ]}
        body={(v) => ({
          policy_ref: v.policyRef,
          jurisdiction: v.jurisdiction,
          platform: v.platform,
          language: v.language,
          decision: v.decision,
          method: v.method,
          participant_refs: v.participantRefs,
          coverage_confirmation: true,
        })}
        auto={false}
      />

      <Grid>
        <QueryPanel
          title="Append capture segments"
          subtitle="Add transcript segments to the capture"
          method="POST"
          path={(v) => `/meetings/${v.meetingId}/capture/segments`}
          params={[
            meeting,
            { name: 'audioMs', label: 'Audio progress (ms)', in: 'body', type: 'number', default: '0' },
            { name: 'transcriptMs', label: 'Transcript progress (ms)', in: 'body', type: 'number', default: '0' },
          ]}
          body={(v) => ({ audio_ms: Number(v.audioMs || 0), transcript_ms: Number(v.transcriptMs || 0) })}
          auto={false}
        />
        <QueryPanel
          title="Withdraw consent"
          subtitle="Withdraw a previously given consent"
          method="POST"
          path={(v) => `/meetings/${v.meetingId}/consents/${v.consentId}/withdraw`}
          params={[meeting, consent, { name: 'reason', label: 'Reason', in: 'body', placeholder: 'Optional reason' }]}
          body={(v) => ({ reason: v.reason ? { note: v.reason } : undefined })}
          auto={false}
        />
      </Grid>

      <QueryPanel
        title="Apply extraction edits"
        subtitle="Correct what was extracted from the transcript"
        method="PATCH"
        path={(v) => `/extractions/${v.extractionId}/edits`}
        params={[
          { name: 'extractionId', label: 'Correction', in: 'path', placeholder: 'Extraction reference' },
          { name: 'edits', label: 'Edits (JSON)', in: 'body', type: 'json', default: '[]' },
          { name: 'suppressed', label: 'Suppressed item keys (JSON)', in: 'body', type: 'json', default: '[]' },
          { name: 'confirmed', label: 'Impact confirmed', in: 'body', type: 'select', default: 'true', options: [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] },
        ]}
        body={(v) => ({
          edits: v.edits,
          suppressed_item_keys: v.suppressed,
          impact_confirmation: v.confirmed === 'true',
        })}
        auto={false}
      />
    </FeaturePage>
  );
}
