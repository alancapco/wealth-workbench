'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { call, get, post } from '@/lib/endpoints';
import { PageShell, Card, Button, Loading, ErrorState } from '@/components/ui/WorkbenchUI';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

export default function MeetingStudioPage() {
  return (
    <Suspense fallback={<PageShell><Loading /></PageShell>}>
      <MeetingStudioInner />
    </Suspense>
  );
}

function MeetingStudioInner() {
  const params = useSearchParams();
  const [clientId, setClientId] = useState(params.get('client') || '');
  const [leads, setLeads] = useState<any[]>([]);
  const [title, setTitle] = useState('Client meeting');
  const [transcript, setTranscript] = useState('');
  const [consent, setConsent] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [accepted, setAccepted] = useState<Record<string, boolean>>({});
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [applied, setApplied] = useState<any>(null);

  useEffect(() => {
    get('/journey/leads').then((res) => {
      setLeads(res.data || []);
      if (!clientId && res.data?.[0]) setClientId(res.data[0].client_id);
    }).catch((err) => setError(err?.message || 'Could not load the book'));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = async (work: () => Promise<void>) => {
    setBusy(true);
    setError('');
    try {
      await work();
    } catch (err: any) {
      setError(err?.message || 'Request failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell wide>
      <h1 className="mb-1 text-xl font-semibold">AI Meeting Studio</h1>
      <p className="mb-4 text-sm text-neutral-500">
        Consent first. The summary proposes profile changes. Nothing is saved onto the client until you accept a line.
      </p>
      {error && <ErrorState error={error} />}
      {busy && <Loading />}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Transcript">
          <label className="mb-3 block text-sm">
            <Label>Client</Label>
            <select className="mt-1 w-full rounded border px-2 py-2" value={clientId} onChange={(e) => setClientId(e.target.value)}>
              {leads.map((lead) => (
                <option key={lead.client_id} value={lead.client_id}>{lead.name}</option>
              ))}
            </select>
          </label>
          <label className="mb-3 flex items-center gap-2 text-sm">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            Recording consent is on file
          </label>
          <div className="mb-2 flex gap-2">
            <Button variant="secondary" onClick={() => run(async () => {
              const sample = await get(`/journey/clients/${clientId}/meetings/sample`);
              setTitle(sample.data.title);
              setTranscript(sample.data.transcript);
            })}>Load sample</Button>
          </div>
          <Textarea rows={12} value={transcript} onChange={(e) => setTranscript(e.target.value)} />
          <Button className="mt-3" onClick={() => run(async () => {
            const result = await call('POST', `/journey/clients/${clientId}/meetings/summarise`, {
              body: { title, transcript, consent },
              timeout: 28000,
            });
            setSummary(result.data);
            setEmail(result.data.follow_up_email_draft || '');
            setApplied(null);
            const next: Record<string, boolean> = {};
            (result.data.proposed_profile_updates || []).forEach((item: any, index: number) => {
              next[String(index)] = true;
            });
            setAccepted(next);
          })}>Summarise</Button>
        </Card>
        <Card title="Summary">
          {!summary && <p className="text-sm">Summarise a consented transcript to see decisions, diffs and the follow-up note.</p>}
          {summary && (
            <div className="space-y-3 text-sm">
              <Badge variant="secondary">{summary.source === 'llm' ? 'AI synthesised' : 'Rule summary'}</Badge>
              <p>{summary.executive_summary}</p>
              <div>
                <div className="font-medium">Decisions</div>
                {(summary.key_decisions || []).map((item: string) => <div key={item}>{item}</div>)}
              </div>
              <div>
                <div className="font-medium">Proposed profile updates</div>
                {(summary.proposed_profile_updates || []).map((item: any, index: number) => (
                  <label key={`${item.field}-${index}`} className="mt-1 flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={Boolean(accepted[String(index)])}
                      onChange={(e) => setAccepted({ ...accepted, [String(index)]: e.target.checked })}
                    />
                    <span>{item.field}: {item.value}. Evidence: {item.evidence}</span>
                  </label>
                ))}
                <Button className="mt-2" onClick={() => run(async () => {
                  const chosen = (summary.proposed_profile_updates || []).filter((_: any, index: number) => accepted[String(index)]);
                  const result = await post(`/journey/clients/${clientId}/meetings/${summary.meeting_id}/apply`, { accepted: chosen });
                  setApplied(result.data);
                })}>Accept selected updates</Button>
                {applied && <p className="mt-2">Applied {applied.applied?.length || 0} update(s).</p>}
              </div>
              <div>
                <div className="font-medium">Follow-up note</div>
                <Textarea rows={6} value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
