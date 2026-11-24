'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { endpoints } from '@/lib/endpoints';
import {
  PageShell, PageHeader, Card, Button, Loading, ErrorState, EmptyState,
  StatusBadge, DataView,
} from '@/components/ui/WorkbenchUI';

export default function BriefPage({ params }: { params: { clientId: string } }) {
  const clientId = params.clientId;
  const [brief, setBrief] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const generate = useCallback(async (force = false) => {
    setLoading(true);
    setError(null);
    try {
      const res: any = await endpoints.briefs.generateLegacy(clientId, force);
      setBrief(res.data?.brief || null);
    } catch (e) {
      setError(e);
      setBrief(null);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => { void generate(false); }, [generate]);

  const sections = brief
    ? Object.entries(brief).filter(([, v]) => v && typeof v === 'object' && !Array.isArray(v) && 'content' in (v as object))
    : [];

  return (
    <PageShell>
      <PageHeader
        eyebrow="Advice & Execution · Meeting brief"
        title={brief?.client_name ? `Meeting brief — ${brief.client_name}` : 'Meeting brief'}
        description="Generated from the live client record, holdings, quotes, interactions and news."
        actions={
          <>
            <Link href={`/clients/${clientId}`}><Button>Client profile</Button></Link>
            <Link href="/briefs"><Button>Briefs workspace</Button></Link>
            <Button variant="primary" onClick={() => void generate(true)} loading={loading}>
              Regenerate
            </Button>
          </>
        }
      />

      {loading ? (
        <Card><Loading label="Generating brief from live data…" /></Card>
      ) : error ? (
        <ErrorState error={error} onRetry={() => void generate(false)} />
      ) : !brief ? (
        <Card><EmptyState title="No brief returned" detail="The client needs a record and holdings in the database." /></Card>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
            <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Version</div><div className="text-xl font-semibold mt-1">{brief.version ?? '—'}</div></Card>
            <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Generated</div><div className="text-sm font-medium mt-2">{brief.generated_at ? new Date(brief.generated_at).toLocaleString('en-GB') : '—'}</div></Card>
            <Card><div className="text-[10px] uppercase tracking-wide text-gray-500">Sections</div><div className="text-xl font-semibold mt-1">{sections.length}</div></Card>
          </div>

          {sections.length === 0 ? (
            <Card><DataView data={brief} /></Card>
          ) : (
            <div className="space-y-4">
              {sections.map(([key, raw]) => {
                const section = raw as any;
                return (
                  <Card
                    key={key}
                    title={key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    subtitle={section?.provenance?.source || undefined}
                    action={
                      section?.provenance?.source_kind ? (
                        <StatusBadge>{section.provenance.source_kind}</StatusBadge>
                      ) : undefined
                    }
                  >
                    <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{section.content}</p>
                    {section?.provenance && (
                      <div className="mt-4 pt-3 border-t border-gray-100 text-[10px] text-gray-400">
                        Source: {section.provenance.source} · Confidence: {section.provenance.confidence ?? '—'} ·{' '}
                        {section.provenance.timestamp ? new Date(section.provenance.timestamp).toLocaleString('en-GB') : ''}
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}

          <div className="mt-5">
            <Card title="Review and edit" subtitle="Section-level review requires a canonical brief artifact">
              <p className="text-xs text-gray-600 mb-3">
                A generated meeting brief is a read-only projection. To record a section review or edit, create a canonical
                brief artifact in the Client Briefs workspace — reviews are validated against the artifact revision hash.
              </p>
              <Link href="/briefs"><Button variant="primary">Open Client Briefs</Button></Link>
            </Card>
          </div>
        </>
      )}
    </PageShell>
  );
}
