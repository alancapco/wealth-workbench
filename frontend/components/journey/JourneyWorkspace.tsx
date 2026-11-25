'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { call, get, post } from '@/lib/endpoints';
import { PageShell, Card, Button, SectionLabel, Loading, ErrorState } from '@/components/ui/WorkbenchUI';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { DatePicker } from '@/components/ui/date-picker';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import CanonicalBriefView from '@/components/CanonicalBriefView';
import { PolicyCheckPanel } from '@/components/PolicyCheckPanel';
import FamilyGraphPanel from '@/components/FamilyGraphPanel';

function isoDate(value?: Date) {
  if (!value) return undefined;
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${value.getFullYear()}-${month}-${day}`;
}

type Stage = 'engage' | 'pipeline' | 'discover' | 'recommend' | 'act' | 'approvals' | 'service';

const LINKS: { href: string; label: string; stage: Stage }[] = [
  { href: '/journey', label: 'Engage', stage: 'engage' },
  { href: '/journey/pipeline', label: 'Pipeline', stage: 'pipeline' },
  { href: '/journey/discover', label: 'Discover', stage: 'discover' },
  { href: '/journey/recommend', label: 'Recommend', stage: 'recommend' },
  { href: '/journey/act', label: 'Act', stage: 'act' },
  { href: '/journey/approvals', label: 'Approvals', stage: 'approvals' },
  { href: '/journey/service', label: 'Service', stage: 'service' },
];

function JourneyWorkspaceInner({ stage }: { stage: Stage }) {
  const params = useSearchParams();
  const requested = params.get('client') || '';
  const [clientId, setClientId] = useState<string>(requested);
  const [error, setError] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const [payload, setPayload] = useState<any>(null);
  const [extra, setExtra] = useState<any>(null);
  const [message, setMessage] = useState('');
  const [query, setQuery] = useState('');
  const [matches, setMatches] = useState<any[]>([]);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotQuestion, setCopilotQuestion] = useState('What should I prepare before this meeting?');
  const [copilotAnswer, setCopilotAnswer] = useState('');

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

  useEffect(() => {
    if (requested) setClientId(requested);
  }, [requested]);

  useEffect(() => {
    if (stage === 'engage') {
      run(async () => setPayload((await get('/journey/my-day')).data));
    } else if (stage === 'pipeline') {
      run(async () => setPayload((await get('/journey/pipeline')).data));
    } else if (stage === 'approvals') {
      run(async () => setPayload((await get('/journey/approvals')).data));
    } else if (stage === 'service') {
      run(async () => {
        const notes = await get('/journey/notifications');
        const leads = await get('/journey/leads');
        setPayload({ notes: notes.data, leads: leads.data });
        if (!clientId && leads.data?.[0]) setClientId(leads.data[0].client_id);
      });
    } else if (!clientId) {
      run(async () => {
        const leads = await get('/journey/leads');
        setExtra(leads.data);
        if (leads.data?.[0]) setClientId(leads.data[0].client_id);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  useEffect(() => {
    if (!clientId) return;
    if (stage === 'discover' || stage === 'service') {
      run(async () => {
        const view = (await get(`/journey/clients/${clientId}`)).data;
        if (stage === 'service') {
          setPayload((current: any) => ({ ...(current || {}), ...view }));
        } else {
          setPayload(view);
        }
      });
    }
    if (stage === 'recommend') {
      run(async () => setPayload((await get(`/journey/clients/${clientId}/shortlist`)).data));
    }
    if (stage === 'engage') {
      run(async () => setExtra((await get(`/journey/clients/${clientId}/brief`)).data));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId, stage]);

  return (
    <PageShell wide>
      <div className="mb-4 flex flex-wrap gap-2">
        {LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`rounded-full px-3 py-1 text-sm ${link.stage === stage ? 'bg-black text-white' : 'bg-neutral-100'}`}
          >
            {link.label}
          </Link>
        ))}
      </div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-neutral-500">
          Synthetic demonstration book. Figures come from the calculation engine. The model writes the words. Orders stay in the sandbox.
        </p>
        <Button variant="secondary" onClick={() => setCopilotOpen((open) => !open)}>Ask the copilot</Button>
      </div>
      {copilotOpen && (
        <Card title="Wealth copilot">
          <Textarea rows={2} value={copilotQuestion} onChange={(e) => setCopilotQuestion(e.target.value)} />
          <Button className="mt-2" onClick={() => run(async () => {
            const answer = await call('POST', `/journey/clients/${clientId}/copilot`, {
              body: { question: copilotQuestion, stage: stage.toUpperCase() },
              timeout: 28000,
            });
            setCopilotAnswer(`${answer.data.source}: ${answer.data.text}`);
          })}>Ask</Button>
          {copilotAnswer && <p className="mt-2 text-sm whitespace-pre-wrap">{copilotAnswer}</p>}
        </Card>
      )}
      {error && <ErrorState error={error} />}
      {busy && <Loading />}

      {stage === 'engage' && payload && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Focus today">
            <SectionLabel>Prioritised leads</SectionLabel>
            <ul className="space-y-2">
              {(payload.focus || []).map((lead: any) => (
                <li key={lead.client_id} className="rounded border p-2">
                  <button className="font-medium" onClick={() => setClientId(lead.client_id)} type="button">
                    {lead.rank}. {lead.name}
                  </button>
                  <div className="text-sm text-neutral-600">Score {lead.score}. {lead.next_best_action}</div>
                  <div className="mt-1 flex gap-2">
                    {['PIN', 'SNOOZE', 'DISMISS'].map((state) => (
                      <Button
                        key={state}
                        variant="secondary"
                        onClick={() => run(async () => {
                          await post(`/journey/leads/${lead.client_id}/control`, { state });
                          setPayload((await get('/journey/my-day')).data);
                        })}
                      >
                        {state}
                      </Button>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm">RPQ inside the window: {(payload.rpq_expiring || []).length}. Open pipeline: {payload.pipeline_open}. Weighted forecast USD {payload.weighted_forecast_usd}.</p>
            <div className="mt-3 flex gap-2 items-end">
              <div className="flex-1 space-y-1.5">
                <Label>Search the book</Label>
                <Input placeholder="Name or risk profile" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
              <Button onClick={() => run(async () => {
                const found = await get('/journey/clients', { q: query });
                setMatches(found.data || []);
              })}>Search</Button>
            </div>
            {matches.map((lead: any) => (
              <button key={lead.client_id} className="mt-1 block text-sm" type="button" onClick={() => setClientId(lead.client_id)}>
                {lead.name} · {lead.jurisdiction} · {lead.risk_profile}
              </button>
            ))}
          </Card>
          <Card title="Meeting preparation">
            {extra?.ai?.source && (
              <p className="mb-2 text-xs text-neutral-500">
                {extra.ai.source === 'llm' ? `AI synthesised${extra.ai.model ? ` · ${extra.ai.model}` : ''}` : 'Deterministic brief'} · {extra.ai.grounded_in}
              </p>
            )}
            {extra?.sections ? <CanonicalBriefView brief={extra} /> : <p>Select a lead to prepare the brief.</p>}
            {clientId && (
              <Link href={`/meetings?client=${clientId}`} className="mt-3 inline-block text-sm underline">Open meeting studio</Link>
            )}
          </Card>
        </div>
      )}

      {stage === 'pipeline' && payload && (
        <div className="grid gap-3 md:grid-cols-3">
          {(payload.stages || []).map((name: string) => (
            <Card key={name} title={name.replaceAll('_', ' ')}>
              {(payload.board?.[name] || []).map((row: any) => (
                <div key={row.id} className="mb-2 border-b pb-2 text-sm">
                  <div className="font-medium">{row.client_name}</div>
                  <div>{row.title}</div>
                  <div>USD {row.value_usd} · {row.probability_pct}%</div>
                  <Button variant="secondary" onClick={() => run(async () => {
                    await post(`/journey/pipeline/${row.id}/advance`);
                    setPayload((await get('/journey/pipeline')).data);
                  })}>Advance</Button>
                </div>
              ))}
            </Card>
          ))}
          <p className="text-sm">Weighted forecast USD {payload.forecast_usd}</p>
        </div>
      )}

      {stage === 'discover' && (
        <Discover stagePayload={payload} clientId={clientId} leads={extra} setClientId={setClientId} run={run} reload={async () => setPayload((await get(`/journey/clients/${clientId}`)).data)} />
      )}

      {stage === 'recommend' && payload && (
        <Recommend clientId={clientId} payload={payload} setMessage={setMessage} message={message} run={run} setPayload={setPayload} />
      )}

      {stage === 'act' && (
        <Act clientId={clientId} setClientId={setClientId} leads={extra} run={run} />
      )}

      {stage === 'approvals' && (
        <Card title="Approvals">
          <p className="mb-2 text-sm">The person who submits a cart cannot approve it. A vulnerable client or a non-GREEN suitability result waits here.</p>
          {(payload || []).length === 0 && <p>No approval requests.</p>}
          {(payload || []).map((row: any) => (
            <div key={row.id} className="mb-3 border-b pb-2 text-sm">
              <div className="font-medium">{row.client_name} · {row.status} · {row.queue}</div>
              <div>{row.reason}</div>
              {row.status === 'PENDING' && (
                <div className="mt-2 flex gap-2">
                  <Button onClick={() => run(async () => {
                    await post(`/journey/approvals/${row.id}/decide`, {
                      decision: 'APPROVE', role: 'SALES_MANAGER', actor: 'fixture:sales-manager@example.test', reason: 'Checker approved',
                    });
                    setPayload((await get('/journey/approvals')).data);
                  })}>Approve as sales manager</Button>
                  <Button variant="secondary" onClick={() => run(async () => {
                    await post(`/journey/approvals/${row.id}/decide`, {
                      decision: 'REJECT', role: 'COMPLIANCE', actor: 'fixture:compliance@example.test', reason: 'Compliance rejected',
                    });
                    setPayload((await get('/journey/approvals')).data);
                  })}>Reject as compliance</Button>
                </div>
              )}
            </div>
          ))}
        </Card>
      )}

      {stage === 'service' && payload && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Notifications">
            <Button onClick={() => run(async () => {
              await post('/journey/evaluate');
              const notes = await get('/journey/notifications');
              setPayload({ ...payload, notes: notes.data });
            })}>Run rebalance and expiry check</Button>
            <ul className="mt-3 space-y-2 text-sm">
              {(payload.notes || []).map((note: any) => (
                <li key={note.id} className="rounded border p-2">
                  <div className="font-medium">{note.title}</div>
                  <div>{note.body}</div>
                  <Button variant="secondary" onClick={() => run(async () => {
                    await post(`/journey/notifications/${note.id}/read`);
                  })}>Mark read</Button>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Shared portfolio">
            <ClientPicker leads={payload.leads || []} clientId={clientId} setClientId={setClientId} />
            {payload.holdings && (
              <div className="mt-3 text-sm">
                <div className="font-medium">{payload.name}</div>
                {(payload.holdings || []).map((h: any) => (
                  <div key={h.asset_name}>{h.asset_name} · {h.allocation_pct}% · gain {h.unrealized_gain_pct}%</div>
                ))}
                <SectionLabel>SAA drift</SectionLabel>
                {(payload.saa || []).map((row: any) => (
                  <div key={row.bucket}>{row.bucket}: actual {row.actual_pct}% vs {row.target_pct}% {row.breach ? '(breach)' : ''}</div>
                ))}
                <SectionLabel>Transactions</SectionLabel>
                {(payload.transactions || []).map((txn: any, index: number) => (
                  <div key={index}>{txn.date} {txn.type} {txn.description} USD {txn.amount_usd} ({txn.source})</div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </PageShell>
  );
}

export function JourneyWorkspace({ stage }: { stage: Stage }) {
  return (
    <Suspense fallback={<PageShell><Loading /></PageShell>}>
      <JourneyWorkspaceInner stage={stage} />
    </Suspense>
  );
}

function ClientPicker({ leads, clientId, setClientId }: { leads: any[]; clientId: string; setClientId: (id: string) => void }) {
  if (!leads?.length) return null;
  return (
    <label className="block max-w-xs space-y-1.5 text-sm">
      <Label>Client</Label>
      <Select value={clientId} onValueChange={setClientId}>
        <SelectTrigger>
          <SelectValue placeholder="Select a client" />
        </SelectTrigger>
        <SelectContent>
          {leads.map((lead) => (
            <SelectItem key={lead.client_id} value={lead.client_id}>{lead.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}

function Discover({ stagePayload, clientId, leads, setClientId, run, reload }: any) {
  const [transcript, setTranscript] = useState('Client wants moderate growth and a retirement goal.');
  const [goalName, setGoalName] = useState('Education');
  const [goalAmount, setGoalAmount] = useState('2000000');
  const [goalDate, setGoalDate] = useState<Date | undefined>();
  const [expiry, setExpiry] = useState<Date | undefined>();
  const [docName, setDocName] = useState('kyc-refresh.pdf');
  const [docExpiry, setDocExpiry] = useState<Date | undefined>();
  const profile = stagePayload?.financial_profile;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Confirm circumstances">
        <ClientPicker leads={leads || []} clientId={clientId} setClientId={setClientId} />
        {stagePayload && (
          <div className="mt-3 text-sm">
            <div className="font-medium">{stagePayload.name} · {stagePayload.profile?.jurisdiction}</div>
            <div>RPQ {stagePayload.investor?.rpq_band} expires {stagePayload.investor?.expiry_date}</div>
            <div>CKA {stagePayload.investor?.cka_passed ? 'current' : 'missing'} · {stagePayload.investor?.investor_status}</div>
            <div>Income {profile?.annual_income_band} · assets {profile?.investable_assets_band} · objective {profile?.investment_objective}</div>
            <SectionLabel>Goals</SectionLabel>
            {(stagePayload.goals || []).map((goal: any) => (
              <div key={goal.id}>{goal.name} · {goal.progress_pct}% · USD {goal.target_usd}</div>
            ))}
            <SectionLabel>Documents</SectionLabel>
            {(stagePayload.documents || []).map((doc: any) => (
              <div key={doc.id}>{doc.type} · {doc.file_name}. {doc.note}</div>
            ))}
            <SectionLabel>Conversations</SectionLabel>
            {(stagePayload.conversations || []).map((item: any, index: number) => (
              <div key={index}>{item.date} · {item.summary}</div>
            ))}
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>RPQ expiry</Label>
                <DatePicker value={expiry} onChange={setExpiry} placeholder="Pick RPQ expiry" />
              </div>
              <div className="space-y-1.5">
                <Label>Goal target date</Label>
                <DatePicker value={goalDate} onChange={setGoalDate} placeholder="Pick a target date" />
              </div>
              <div className="space-y-1.5">
                <Label>Goal name</Label>
                <Input value={goalName} onChange={(e) => setGoalName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Goal amount (USD)</Label>
                <Input type="number" value={goalAmount} onChange={(e) => setGoalAmount(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Document name</Label>
                <Input value={docName} onChange={(e) => setDocName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Document expiry</Label>
                <DatePicker value={docExpiry} onChange={setDocExpiry} placeholder="Pick an expiry" />
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button onClick={() => run(async () => {
                await post(`/journey/clients/${clientId}/confirm-unchanged`);
                await reload();
              })}>Confirm no change</Button>
              <Button variant="secondary" onClick={() => run(async () => {
                await call('PUT', `/journey/clients/${clientId}/financial-profile`, {
                  body: {
                    annual_income_band: profile?.annual_income_band || '1M-5M',
                    investable_assets_band: profile?.investable_assets_band || '5M+',
                    liquidity_need: profile?.liquidity_need || 'MEDIUM',
                    investment_objective: profile?.investment_objective || 'Growth',
                  },
                });
                await reload();
              })}>Save four fields</Button>
              <Button variant="secondary" onClick={() => run(async () => {
                if (expiry) {
                  await call('PUT', `/journey/clients/${clientId}/investor-profile`, { body: { expiry_date: isoDate(expiry) } });
                }
                if (goalDate && goalName) {
                  await post(`/journey/clients/${clientId}/goals`, {
                    name: goalName,
                    target_usd: Number(goalAmount) || 0,
                    target_date: isoDate(goalDate),
                  });
                }
                if (docName) {
                  await post(`/journey/clients/${clientId}/documents`, {
                    file_name: docName,
                    document_type: 'KYC',
                    expires_on: isoDate(docExpiry),
                  });
                }
                await reload();
              })}>Save dates</Button>
            </div>
          </div>
        )}
      </Card>
      <Card title="Knowledge graph">
        {clientId ? <FamilyGraphPanel clientId={clientId} title="Wealth graph" subtitle="Household, holdings and the rules that apply" /> : <p>Select a client.</p>}
      </Card>
      <Card title="AI Assist">
        <div className="space-y-1.5">
          <Label>Meeting notes</Label>
          <Textarea rows={4} value={transcript} onChange={(e) => setTranscript(e.target.value)} />
        </div>
        <Button onClick={() => run(async () => {
          const proposed = await post(`/journey/clients/${clientId}/assist`, { transcript });
          await post(`/journey/clients/${clientId}/assist/accept`, { proposals: proposed.data.proposals });
          await post(`/journey/clients/${clientId}/documents`, { file_name: 'kyc-prefill.txt', document_type: 'KYC', note: 'Prefilled from the conversation' });
          await reload();
        })}>Propose and accept updates</Button>
      </Card>
    </div>
  );
}

function Recommend({ clientId, payload, setMessage, message, run, setPayload }: any) {
  const [plan, setPlan] = useState<any>(null);
  const blockers = (payload.products || [])
    .filter((product: any) => product.assessment.rating === 'RED')
    .slice(0, 3)
    .map((product: any) => ({
      code: product.product_id,
      field: 'suitability',
      config_ref: null,
      resolution: 'REVIEW' as const,
    }));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="CIO shortlist">
        <PolicyCheckPanel blockers={blockers} context="Suitability pre-screen" />
        {(payload.products || []).map((product: any) => (
          <div key={product.product_id} className="mb-3 border-b pb-2 text-sm">
            <div className="font-medium">{product.name}</div>
            <div>{product.cio_rating} · {product.share_class} · {product.saa_bucket} · <Badge variant={product.assessment.rating === 'RED' ? 'destructive' : 'secondary'}>{product.assessment.rating}</Badge></div>
            <div>{product.rationale}</div>
            <Button variant="secondary" onClick={() => run(async () => {
              const pitch = await get(`/journey/clients/${clientId}/pitch/${product.product_id}`);
              setMessage(`${pitch.data.source === 'llm' ? 'Model' : 'Local rules'}: ${pitch.data.text}`);
            })}>Explain</Button>
          </div>
        ))}
      </Card>
      <Card title="Explain and project">
        <p className="text-sm">{message || 'Choose a product to explain it.'}</p>
        <div className="mt-3 flex gap-2">
          <Button onClick={() => run(async () => {
            const proposal = await post(`/journey/clients/${clientId}/optimise`);
            setMessage(JSON.stringify(proposal.data.items));
          })}>One-click proposal</Button>
          <Button variant="secondary" onClick={() => run(async () => {
            const answer = await post('/journey/protect', { question: 'What if the client is vulnerable and the product is complex?' });
            const body = answer.data.answered ? `${answer.data.text} [${answer.data.citations.join(', ')}]` : answer.data.text;
            setMessage(`${answer.data.source === 'llm' ? 'Model' : 'Local rules'}: ${body}`);
          })}>Ask policy</Button>
          <Button variant="secondary" onClick={() => run(async () => {
            const found = await get('/journey/catalogue', { q: 'bond' });
            const planned = await call('POST', `/journey/clients/${clientId}/plan`, {
              body: {
                current_age: 50,
                retirement_age: 65,
                current_savings_usd_millions: 20,
                monthly_contribution_usd: 20000,
                target_retirement_corpus_usd_millions: 40,
                assumed_annual_return_pct: 6,
                inflation_pct: 2.5,
              },
              timeout: 28000,
            });
            const stressed = await post(`/journey/clients/${clientId}/stress`, { market_shock_pct: -10, fx_shock_pct: -5, sector_shock_pct: 0 });
            setPayload({ ...payload, search: found.data });
            setPlan(planned.data);
            setMessage(`${planned.data.projection_source === 'llm' ? 'Model commentary' : 'Calculation only'}. Stress impact USD ${stressed.data.impact_usd}.`);
          })}>Plan and stress</Button>
        </div>
        {(payload.search || []).map((product: any) => (
          <div key={product.product_id} className="text-sm">{product.name}</div>
        ))}
        {plan && (
          <div className="mt-3 text-sm">
            <div className="font-medium">USD {plan.projected_corpus_usd_millions}M nominal · USD {plan.real_projected_corpus_usd_millions}M in today&apos;s dollars</div>
            <p className="mt-1">{plan.executive_narrative || plan.summary}</p>
            <p className="mt-1">{plan.gap_analysis}</p>
            {(plan.year_by_year || []).map((row: any) => (
              <div key={row.year} className="text-xs text-neutral-600">{row.year} age {row.age}: USD {row.corpus_usd_millions}M</div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function Act({ clientId, setClientId, leads, run }: any) {
  const [result, setResult] = useState<any>(null);
  const [signer, setSigner] = useState('Client in meeting');
  return (
    <Card title="Wealth shopping cart">
      <ClientPicker leads={leads || []} clientId={clientId} setClientId={setClientId} />
      <p className="my-2 text-sm">Client reviews the cart on this screen and signs before any hand-off.</p>
      <div className="mt-3 max-w-sm space-y-1.5">
        <Label>Client signature name</Label>
        <Input value={signer} onChange={(e) => setSigner(e.target.value)} />
      </div>
      <div className="mt-2">
        <Button onClick={() => run(async () => {
          const cart = await post('/journey/carts', {
            client_id: clientId,
            items: [{ product_id: 'BOND-HSBC-2029', amount_usd: 100000, side: 'BUY' }],
          });
          const signed = await post(`/journey/carts/${cart.data.cart_id}/sign`, { signer_name: signer });
          const submitted = await post(`/journey/carts/${cart.data.cart_id}/submit`);
          await call('POST', '/journey/events', { body: { stage: 'ACT', event: 'stage_completed', client_id: clientId } });
          setResult({ cart: cart.data, signed: signed.data, submitted: submitted.data });
        })}>Review, sign and hand off a bond</Button>
      </div>
      {result && (
        <pre className="mt-3 overflow-auto text-xs">{JSON.stringify(result, null, 2)}</pre>
      )}
    </Card>
  );
}
