'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Button, Card, DataView, ErrorState, Field, Loading, PageShell, PageHeader,
  Select, StatusBadge, TextInput, EmptyState, prettify,
} from '@/components/ui/WorkbenchUI';
import { call } from '@/lib/endpoints';
import { defaultBody, fetchOpenApi, materialisePath, OpenApiOperation } from '@/lib/openapi';

export default function CataloguePage() {
  const [operations, setOperations] = useState<OpenApiOperation[]>([]);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [search, setSearch] = useState('');
  const [group, setGroup] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [values, setValues] = useState<Record<string, string>>({});
  const [body, setBody] = useState('{}');
  const [result, setResult] = useState<{ data: any; raw: any; status: number; ms: number } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [running, setRunning] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const load = () => {
    setLoadingList(true);
    fetchOpenApi()
      .then((ops) => {
        setOperations(ops);
        setLoadError(null);
        setSelectedId((prev) => prev || ops[0]?.id || '');
      })
      .catch((e) => setLoadError(e))
      .finally(() => setLoadingList(false));
  };

  useEffect(load, []);

  const groups = useMemo(
    () => Array.from(new Set(operations.map((o) => o.group))).sort(),
    [operations],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return operations.filter(
      (o) =>
        (!group || o.group === group) &&
        (!q || `${o.method} ${o.relativePath} ${o.summary}`.toLowerCase().includes(q)),
    );
  }, [operations, search, group]);

  const selected = operations.find((o) => o.id === selectedId);

  // Initialise the form from the selected operation's own OpenAPI contract.
  useEffect(() => {
    if (!selected) return;
    const initial: Record<string, string> = {};
    selected.params.forEach((p) => {
      initial[p.name] = p.example !== undefined ? String(p.example) : '';
    });
    setValues(initial);
    setBody(defaultBody(selected.bodyFields));
    setResult(null);
    setError(null);
  }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

  const pathParams = selected?.params.filter((p) => p.in === 'path') || [];
  const queryParams = selected?.params.filter((p) => p.in === 'query') || [];
  const headerParams = selected?.params.filter((p) => p.in === 'header') || [];

  const execute = async () => {
    if (!selected) return;
    setRunning(true);
    setError(null);
    const started = performance.now();
    try {
      const path = materialisePath(selected.relativePath, values);
      const query: Record<string, string> = {};
      queryParams.forEach((p) => {
        if (values[p.name]) query[p.name] = values[p.name];
      });
      const headers: Record<string, string> = {};
      headerParams.forEach((p) => {
        const v = values[p.name];
        if (v) headers[p.name] = v;
        else if (/csrf/i.test(p.name)) headers[p.name] = 'workbench-ui';
        else if (/idempotency/i.test(p.name)) headers[p.name] = `catalogue-${Date.now()}`;
        else if (/if-match/i.test(p.name)) headers[p.name] = '"0:0"';
      });
      let payload: unknown;
      if (selected.bodyFields.length) {
        try {
          payload = JSON.parse(body || '{}');
        } catch {
          throw new Error('Request body is not valid JSON');
        }
      }
      const res = await call(selected.method.toUpperCase() as any, path, {
        query,
        headers,
        body: payload,
      });
      setResult({ data: res.data, raw: res.raw, status: res.status, ms: Math.round(performance.now() - started) });
    } catch (e) {
      setError(e);
      setResult(null);
    } finally {
      setRunning(false);
    }
  };

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Platform"
        title="Developer reference"
        description="Advanced workspace for administrators. Look up any capability in the platform and run it against live data."
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge tone={loadError ? 'error' : 'success'}>
              {loadError ? 'Offline' : `${operations.length} capabilities available`}
            </StatusBadge>
            <Button onClick={load}>Reload</Button>
          </div>
        }
      />

      {loadingList ? (
        <Loading label="Loading available capabilities…" />
      ) : loadError ? (
        <ErrorState error={loadError} onRetry={load} />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(280px,360px)_1fr] gap-5 items-start">
          {/* Endpoint list */}
          <Card title="Available actions" subtitle="Grouped by business area" bodyClassName="p-0">
            <div className="px-4 py-3 border-b border-gray-200 space-y-2">
              <TextInput
                value={search}
                onChange={setSearch}
                placeholder="Search capabilities…"
                ariaLabel="Search capabilities"
              />
              <Select
                value={group}
                onChange={setGroup}
                options={groups.map((g) => ({ value: g, label: g }))}
                placeholder="All business areas"
              />
            </div>
            <div className="max-h-[640px] overflow-y-auto divide-y divide-gray-100">
              {filtered.length === 0 && <EmptyState title="No matching capabilities" />}
              {filtered.map((o) => (
                <button
                  key={o.id}
                  onClick={() => setSelectedId(o.id)}
                  className={`w-full text-left px-4 py-2.5 transition-colors ${
                    selectedId === o.id ? 'bg-gray-100 border-l-2 border-black' : 'hover:bg-gray-50 border-l-2 border-transparent'
                  }`}
                >
                  <div className="text-[12px] leading-tight text-black truncate">
                    {o.summary}
                  </div>
                  <div className="text-[10px] text-gray-400 mt-1 truncate">{o.group}</div>
                </button>
              ))}
            </div>
          </Card>

          {/* Operation runner */}
          {selected ? (
            <div className="space-y-5 min-w-0">
              <Card
                title={selected.summary}
                subtitle={selected.description || selected.group}
                action={<StatusBadge>{selected.method.toUpperCase() === 'GET' ? 'Read' : 'Change'}</StatusBadge>}
              >
                <details className="mb-4">
                  <summary className="text-[10px] text-gray-400 cursor-pointer hover:text-black">
                    Technical details
                  </summary>
                  <code className="block mt-2 text-xs text-black bg-gray-50 border border-gray-200 rounded px-3 py-2 break-all">
                    {selected.relativePath}
                  </code>
                </details>

                {[...pathParams, ...queryParams, ...headerParams].length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                    {[...pathParams, ...queryParams, ...headerParams].map((p) => (
                      <Field
                        key={`${p.in}-${p.name}`}
                        label={`${prettify(p.name)}${p.required ? ' *' : ''}`}
                        hint={p.description || (p.required ? 'Required' : 'Optional')}
                      >
                        {p.enum ? (
                          <Select
                            value={values[p.name] || ''}
                            onChange={(v) => setValues((s) => ({ ...s, [p.name]: v }))}
                            options={p.enum.map((e) => ({ value: String(e), label: String(e) }))}
                            placeholder="Select…"
                          />
                        ) : (
                          <TextInput
                            value={values[p.name] || ''}
                            onChange={(v) => setValues((s) => ({ ...s, [p.name]: v }))}
                            placeholder={p.example !== undefined ? `e.g. ${p.example}` : 'Enter value'}
                            ariaLabel={prettify(p.name)}
                          />
                        )}
                      </Field>
                    ))}
                  </div>
                )}

                {selected.bodyFields.length > 0 && (
                  <Field
                    label="Details to submit"
                    hint={`You can include: ${selected.bodyFields.map((f) => prettify(f.name)).join(', ')}`}
                  >
                    <textarea
                      value={body}
                      onChange={(e) => setBody(e.target.value)}
                      rows={Math.min(10, Math.max(4, selected.bodyFields.length + 2))}
                      spellCheck={false}
                      className="w-full px-3 py-2 font-mono text-[11px] text-black bg-white border border-gray-300 rounded outline-none focus:border-black resize-y"
                    />
                  </Field>
                )}

                <div className="mt-4 flex items-center gap-2">
                  <Button variant="primary" onClick={execute} loading={running} disabled={!selected}>
                    Run
                  </Button>
                  <span className="text-[10px] text-gray-400">Safety checks are applied automatically.</span>
                </div>
              </Card>

              <Card
                title="Result"
                subtitle="Live result"
                action={result ? <StatusBadge tone={result.status < 400 ? 'success' : 'error'}>Completed in {result.ms} ms</StatusBadge> : undefined}
              >
                {error ? (
                  <ErrorState error={error} onRetry={execute} />
                ) : result ? (
                  <>
                    <DataView data={result.data} emptyTitle="No records" emptyDetail="Nothing matched this selection." />
                    <button onClick={() => setShowRaw((s) => !s)} className="mt-3 text-[10px] text-gray-400 hover:text-black">
                      {showRaw ? 'Hide' : 'Show'} technical details
                    </button>
                    {showRaw && (
                      <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-[10px] text-gray-700 overflow-x-auto max-h-80">
                        {JSON.stringify(result.raw, null, 2)}
                      </pre>
                    )}
                  </>
                ) : (
                  <EmptyState title="Ready to run" detail="Choose Run to see live data." />
                )}
              </Card>
            </div>
          ) : (
            <Card title="Select a capability"><EmptyState /></Card>
          )}
        </div>
      )}
    </PageShell>
  );
}
