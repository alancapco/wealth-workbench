'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { endpoints } from '@/lib/endpoints';
import { useApp } from '@/lib/app-context';
import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import {
  Card, DataTable, Loading, ErrorState, EmptyState, StatusBadge,
  Button, SectionLabel, Field, Select, TextInput,
} from '@/components/ui/WorkbenchUI';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

/**
 * IANA timezone configured for the fixture book. API-015 (evaluate) and
 * API-016 (latest) must receive the SAME local date / timezone pair, otherwise
 * they resolve to different local days and the "run then refresh" loop looks
 * broken even when it is not.
 */
const BOOK_TIMEZONE = 'Asia/Singapore';

/** DST-safe local date for an IANA zone, formatted YYYY-MM-DD for API-016. */
function localDate(timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const part = (t: string) => parts.find((p) => p.type === t)?.value ?? '';
  return `${part('year')}-${part('month')}-${part('day')}`;
}

interface RecommendationRef {
  evaluation_id: string;
  client_id: string;
  reason_key: string;
  reason_hash: string;
}

/**
 * Derive a recommendation_ref from a REAL stored evaluation item.
 * priority_controls and contact_outcomes both carry a composite FK to
 * priority_items, so a fabricated zero UUID can never be valid.
 */
function recommendationFrom(evaluation: any, clientId: string): RecommendationRef | null {
  const items = Array.isArray(evaluation?.items) ? evaluation.items : [];
  if (!evaluation?.id || items.length === 0) return null;
  const item = items.find((i: any) => i?.client?.id === clientId) || items[0];
  const reason = Array.isArray(item?.reasons) ? item.reasons[0] : null;
  if (!item?.client?.id || !reason?.key || !reason?.hash) return null;
  return {
    evaluation_id: String(evaluation.id),
    client_id: String(item.client.id),
    reason_key: String(reason.key),
    reason_hash: String(reason.hash),
  };
}

const CONTROL_TYPES = [
  { value: 'PIN', label: 'Pin client' },
  { value: 'SNOOZE', label: 'Snooze client' },
  { value: 'DISMISS', label: 'Dismiss client' },
];

const SNOOZE_PERIODS = [
  { value: '24', label: '24 hours' },
  { value: '48', label: '48 hours' },
  { value: '168', label: '7 days' },
];

const OUTCOMES = [
  { value: 'CONTACTED', label: 'Contacted' },
  { value: 'MEETING_BOOKED', label: 'Meeting booked' },
  { value: 'NO_RESPONSE', label: 'No response' },
  { value: 'NOT_RELEVANT', label: 'Not relevant' },
];

/**
 * Book evaluation & controls.
 *
 * The read state auto-loads on mount and whenever the live book changes — no
 * Run button. The three writes remain explicit one-click actions: auto-firing a
 * POST on page load would insert a duplicate row on every visit.
 */
function PriorityControls({
  bookId,
  clientId,
  onChanged,
}: {
  bookId: string;
  clientId: string;
  onChanged: () => void;
}) {
  const date = useMemo(() => localDate(BOOK_TIMEZONE), []);
  const [latest, setLatest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tone: 'ok' | 'err'; text: string } | null>(null);
  const [lastRequest, setLastRequest] = useState<{ label: string; path: string; body: unknown } | null>(null);
  const [showTechnical, setShowTechnical] = useState(false);

  const [controlType, setControlType] = useState('PIN');
  const [pinned, setPinned] = useState(true);
  const [snoozeHours, setSnoozeHours] = useState('24');
  const [outcome, setOutcome] = useState('CONTACTED');
  const [note, setNote] = useState('');

  const loadLatest = useCallback(async () => {
    if (!bookId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await endpoints.priorities.latest(bookId, { date, timezone: BOOK_TIMEZONE });
      setLatest(res.data);
      setError(null);
    } catch (e) {
      setLatest(null);
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [bookId, date]);

  useEffect(() => {
    void loadLatest();
  }, [loadLatest]);

  const evaluation = latest?.evaluation ?? null;
  const capability = latest?.capability_state ?? 'UNKNOWN';
  const recommendationRef = useMemo(
    () => recommendationFrom(evaluation, clientId),
    [evaluation, clientId],
  );
  const canMutate = Boolean(recommendationRef && clientId && bookId);

  const runAction = async (
    key: string,
    label: string,
    path: string,
    body: unknown,
    fn: () => Promise<any>,
  ) => {
    setBusy(key);
    setFeedback(null);
    setLastRequest({ label, path, body });
    try {
      const res = await fn();
      setFeedback({ tone: 'ok', text: `${label}: ${JSON.stringify(res.data).slice(0, 220)}` });
      await loadLatest();
      onChanged();
    } catch (e) {
      setFeedback({
        tone: 'err',
        text: `${label} failed: ${e instanceof Error ? e.message : String(e)}`,
      });
    } finally {
      setBusy(null);
    }
  };

  const evaluationBody = { date, timezone: BOOK_TIMEZONE, trigger: 'RM_REFRESH' };

  const buildControlBody = (): Record<string, any> => {
    const control: Record<string, any> =
      controlType === 'PIN'
        ? { type: 'PIN', pinned }
        : controlType === 'SNOOZE'
          ? {
              type: 'SNOOZE',
              until: new Date(Date.now() + Number(snoozeHours) * 3_600_000).toISOString(),
            }
          : {
              type: 'DISMISS',
              reason: {
                code: 'RM_DISCRETION',
                catalog_ref: {
                  config_ref: {
                    id: evaluation?.policy_ref?.id ?? '00000000-0000-0000-0000-000000000000',
                    revision: 1,
                    hash: '0'.repeat(64),
                  },
                  catalog_key: 'RM_DISCRETION',
                },
              },
            };
    return { client_id: clientId, recommendation_ref: recommendationRef, control };
  };

  const buildOutcomeBody = (): Record<string, any> => ({
    recommendation_ref: recommendationRef,
    client_id: clientId,
    outcome,
    // One second of slack so a slightly fast browser clock is never treated as
    // a future contact by API-055's occurred_at validation.
    occurred_at: new Date(Date.now() - 1000).toISOString(),
    ...(note.trim() ? { note: note.trim() } : {}),
    evidence_refs: [],
  });

  return (
    <div className="space-y-4">
      <Alert>
        <AlertTitle className="text-sm">Live evaluation state · auto-loaded</AlertTitle>
        <AlertDescription className="text-xs">
          {loading
            ? 'Loading the latest stored evaluation for this book…'
            : error
              ? 'The latest evaluation could not be loaded. Use Retry below.'
              : `Local date ${date} (${BOOK_TIMEZONE}) · capability ${capability} · ${evaluation?.items?.length ?? 0} ranked item(s) · status ${evaluation?.status ?? 'NO EVALUATION'}.`}
        </AlertDescription>
      </Alert>

      {error ? <ErrorState error={error} onRetry={() => void loadLatest()} /> : null}

      {!loading && !canMutate && (
        <Alert>
          <AlertTitle className="text-sm">Controls disabled — no evaluated priority items</AlertTitle>
          <AlertDescription className="text-xs">
            Priority controls and contact outcomes reference a stored priority item through the
            composite key (tenant, book, evaluation, client). DEC-03 (ranking policy) is not
            configured, so book evaluations return <code>FAILED</code> with zero items. These
            two forms are disabled rather than submitting a fabricated reference. Enable DEC-03
            and run a successful evaluation to unlock them.
          </AlertDescription>
        </Alert>
      )}

      <Grid cols={3}>
        <Card
          title="Run book evaluation"
          subtitle="Recalculate which clients need attention"
          action={
            <Button
              variant="primary"
              loading={busy === 'evaluate'}
              disabled={!bookId}
              onClick={() =>
                void runAction(
                  'evaluate',
                  'Run evaluation',
                  `/books/${bookId}/priority-evaluations`,
                  evaluationBody,
                  () => endpoints.priorities.evaluate(bookId, evaluationBody),
                )
              }
            >
              Run evaluation
            </Button>
          }
        >
          <div className="space-y-2 text-xs">
            <StatusBadge tone={evaluation?.status === 'CURRENT' ? 'success' : 'warning'}>
              {evaluation?.status ?? 'NO EVALUATION'}
            </StatusBadge>
            <div className="text-muted-foreground">Evaluation date: {evaluation?.date ?? '—'}</div>
            <div className="text-muted-foreground">Stored items: {evaluation?.items?.length ?? 0}</div>
            <div className="text-muted-foreground break-words">
              Criteria: {evaluation?.criteria_summary ?? '—'}
            </div>
            <div className="text-[10px] text-muted-foreground pt-1">
              Payload: date {date}, timezone {BOOK_TIMEZONE}, trigger RM_REFRESH
            </div>
          </div>
        </Card>

        <Card
          title="Set priority control"
          subtitle="Adjust how a client is prioritised"
          action={
            <Button
              variant="primary"
              loading={busy === 'control'}
              disabled={!canMutate}
              title={canMutate ? undefined : 'Requires a stored priority item for this client'}
              onClick={() => {
                const body = buildControlBody();
                void runAction(
                  'control',
                  'Apply control',
                  `/books/${bookId}/priority-controls`,
                  body,
                  () => endpoints.priorities.control(bookId, body),
                );
              }}
            >
              Apply control
            </Button>
          }
        >
          <div className="space-y-3">
            <Field label="Control type">
              <Select value={controlType} onChange={setControlType} options={CONTROL_TYPES} />
            </Field>
            {controlType === 'PIN' && (
              <div className="flex items-center gap-2">
                <Switch id="pinned" checked={pinned} onCheckedChange={setPinned} />
                <Label htmlFor="pinned" className="text-xs">Pinned</Label>
              </div>
            )}
            {controlType === 'SNOOZE' && (
              <Field label="Snooze for">
                <Select value={snoozeHours} onChange={setSnoozeHours} options={SNOOZE_PERIODS} />
              </Field>
            )}
            {controlType === 'DISMISS' && (
              <div className="text-[11px] text-muted-foreground">
                Reason: RM discretion (catalog key RM_DISCRETION)
              </div>
            )}
            <div className="text-[10px] text-muted-foreground">
              {recommendationRef
                ? 'Priority item ready for the selected client'
                : 'No stored priority item for this client'}
            </div>
          </div>
        </Card>

        <Card
          title="Record contact outcome"
          subtitle="Record the outcome of a client contact"
          action={
            <Button
              variant="primary"
              loading={busy === 'outcome'}
              disabled={!canMutate}
              title={canMutate ? undefined : 'Requires a stored priority item for this client'}
              onClick={() => {
                const body = buildOutcomeBody();
                void runAction(
                  'outcome',
                  'Record outcome',
                  `/books/${bookId}/contact-outcomes`,
                  body,
                  () => endpoints.priorities.contactOutcome(bookId, body),
                );
              }}
            >
              Record outcome
            </Button>
          }
        >
          <div className="space-y-3">
            <Field label="Outcome">
              <Select value={outcome} onChange={setOutcome} options={OUTCOMES} />
            </Field>
            <Field label="Note (optional)">
              <TextInput
                value={note}
                onChange={setNote}
                placeholder="Context for this contact"
                ariaLabel="Note"
              />
            </Field>
            <div className="text-[10px] text-muted-foreground">
              Evidence refs: none · meaningful touchpoint stays NOT_CONFIRMED
            </div>
          </div>
        </Card>
      </Grid>

      {feedback && (
        <Alert variant={feedback.tone === 'err' ? 'destructive' : 'default'}>
          <AlertDescription className="text-xs break-words">{feedback.text}</AlertDescription>
        </Alert>
      )}

      <div className="border border-gray-200 rounded bg-white px-4 py-3">
        <button
          onClick={() => setShowTechnical((s) => !s)}
          className="text-[10px] text-gray-400 hover:text-black"
        >
          {showTechnical ? 'Hide' : 'Show'} technical details
        </button>
        {showTechnical && (
          <div className="mt-3 space-y-3 text-[10px] text-gray-700">
            <div>
              <div className="font-semibold">Auto-loaded GET (API-016)</div>
              <code className="break-all">
                GET /books/{bookId}/priority-evaluations/latest?date={date}&amp;timezone={encodeURIComponent(BOOK_TIMEZONE)}
              </code>
            </div>
            <div>
              <div className="font-semibold">Auto-loaded response</div>
              <pre className="overflow-x-auto max-h-56 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded p-2">
                {JSON.stringify(latest, null, 2)}
              </pre>
            </div>
            {lastRequest && (
              <div>
                <div className="font-semibold">Last action · POST {lastRequest.path}</div>
                <pre className="overflow-x-auto max-h-56 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded p-2">
                  {JSON.stringify(lastRequest.body, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function PrioritiesPage() {
  const app = useApp();
  const today = useMemo(() => localDate(BOOK_TIMEZONE), []);
  const [ranked, setRanked] = useState<any[]>([]);
  const [evalState, setEvalState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string>('');

  const load = useCallback(() => {
    if (!app.bookId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      endpoints.dashboard.myDay(),
      // Use the real API-016 contract instead of the UNCONFIGURED convenience
      // stub, so the header reflects actual stored evaluation state.
      endpoints.priorities.latest(app.bookId, { date: today, timezone: BOOK_TIMEZONE }),
    ])
      .then(([myDay, evaluation]: any[]) => {
        setRanked(myDay.data?.ranked_clients || []);
        setEvalState(evaluation.data || null);
        setError(null);
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [app.bookId, today]);

  useEffect(() => {
    load();
  }, [load]);

  const act = async (name: string, clientId: string, fn: () => Promise<any>) => {
    setBusy(`${name}-${clientId}`);
    setFeedback('');
    try {
      const res = await fn();
      setFeedback(`${name} → ${JSON.stringify(res.data).slice(0, 180)}`);
      load();
    } catch (e) {
      setFeedback(`${name} failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(null);
    }
  };

  return (
    <FeaturePage
      eyebrow="Engagement"
      title="Priority Book"
      description="Clients are ranked by the live priority service. Pin, snooze or dismiss a client, or recalculate today's list."
      context={['book', 'client']}
      wide
      actions={<Button onClick={load}>Refresh</Button>}
    >
      <Grid cols={3}>
        <Card title="Evaluation state" subtitle="State of the latest priority calculation">
          {loading ? <Loading /> : (
            <div className="space-y-2">
              <StatusBadge tone={evalState?.capability_state === 'READY' ? 'success' : 'warning'}>
                {evalState?.capability_state || 'UNKNOWN'}
              </StatusBadge>
              <div className="text-xs text-gray-600">Evaluation date: {evalState?.evaluation?.date || '—'}</div>
              <div className="text-xs text-gray-600">Status: {evalState?.evaluation?.status || '—'}</div>
              <div className="text-xs text-gray-600">Stored items: {evalState?.evaluation?.items?.length ?? 0}</div>
            </div>
          )}
        </Card>
        <Card title="Live ranked clients" subtitle="Clients ranked for today">
          <div className="text-2xl font-semibold text-black">{ranked.length}</div>
          <div className="text-xs text-gray-500 mt-1">Scored from real client records</div>
        </Card>
        <Card title="Active book" subtitle="Shared live context">
          <div className="text-sm font-medium text-black">
            {app.session?.books?.find((b: any) => b.book_id === app.bookId)?.display_name
              || (app.bookId ? 'Selected book' : '—')}
          </div>
          <div className="text-xs text-gray-500 mt-1">{app.session?.books?.length ?? 0} books in session</div>
        </Card>
      </Grid>

      {error ? <ErrorState error={error} onRetry={load} /> : null}
      {feedback && (
        <div className="border border-gray-300 bg-white rounded px-4 py-2 text-xs text-gray-700 break-words">{feedback}</div>
      )}

      <Card title="Ranked clients" subtitle="Scores, reasons and evidence returned by the ranking service" bodyClassName="p-0">
        <div className="p-5">
          {loading ? <Loading /> : ranked.length === 0 ? (
            <EmptyState title="No ranked clients" detail="No clients have been scored for this book yet. Run a priority evaluation below." />
          ) : (
            <DataTable
              rows={ranked}
              columns={[
                { key: 'rank', label: '#', width: '50px' },
                {
                  key: 'name', label: 'Client', render: (c: any) => (
                    <Link href={`/clients/${c.client_id}`} className="font-medium text-black hover:underline">{c.name}</Link>
                  ),
                },
                { key: 'total_score', label: 'Score', align: 'right' },
                { key: 'opportunity_score', label: 'Opportunity', align: 'right' },
                { key: 'risk_score', label: 'Risk', align: 'right' },
                { key: 'retention_score', label: 'Retention', align: 'right' },
                {
                  key: 'reason', label: 'Reason', render: (c: any) => (
                    <span className="text-xs text-gray-600">
                      {typeof c.reason === 'object' ? c.reason?.description || JSON.stringify(c.reason) : c.reason}
                    </span>
                  ),
                },
                {
                  key: 'controls', label: 'Controls', render: (c: any) => (
                    <div className="flex gap-1 flex-wrap">
                      <Button
                        loading={busy === `snooze-${c.client_id}`}
                        onClick={() => void act('Snooze', c.client_id, () => endpoints.priorities.snooze(c.client_id, new Date(Date.now() + 86400000).toISOString()))}
                      >Snooze 24h</Button>
                      <Button
                        loading={busy === `pin-${c.client_id}`}
                        onClick={() => void act('Pin', c.client_id, () => endpoints.priorities.pin(c.client_id))}
                      >Pin</Button>
                      <Button
                        loading={busy === `dismiss-${c.client_id}`}
                        onClick={() => void act('Dismiss', c.client_id, () => endpoints.priorities.dismiss(c.client_id))}
                      >Dismiss</Button>
                    </div>
                  ),
                },
              ]}
            />
          )}
        </div>
      </Card>

      <SectionLabel>Book evaluation &amp; controls</SectionLabel>
      <PriorityControls
        key={app.bookId}
        bookId={app.bookId}
        clientId={app.clientId}
        onChanged={load}
      />
    </FeaturePage>
  );
}
