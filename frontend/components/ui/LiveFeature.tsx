'use client';

/** Shared page frame + live context bar for feature workspaces. */
import React, { ReactNode } from 'react';
import { PageShell, PageHeader, Field, Select, QueryPanel } from './WorkbenchUI';
import { useApp } from '@/lib/app-context';
import type { ParamSpec } from './WorkbenchUI';
import { Card, CardContent } from '@/components/ui/card';

export function FeaturePage({
  eyebrow,
  title,
  description,
  actions,
  children,
  wide,
  context = [],
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  wide?: boolean;
  context?: ('client' | 'demo' | 'workflow' | 'book')[];
}) {
  return (
    <PageShell wide={wide}>
      <PageHeader eyebrow={eyebrow} title={title} description={description} actions={actions} />
      {context.length > 0 && <ContextBar needs={context} />}
      <div className="mt-5 space-y-5">{children}</div>
    </PageShell>
  );
}

export function ContextBar({ needs }: { needs: ('client' | 'demo' | 'workflow' | 'book')[] }) {
  const app = useApp();
  return (
    <Card>
      <CardContent className="grid grid-cols-1 gap-3 px-4 py-3 sm:grid-cols-2 lg:grid-cols-4">
      {needs.includes('client') && (
        <Field label="Client (live client book)">
          <Select
            ariaLabel="Client"
            value={app.clientId}
            onChange={app.setClientId}
            options={app.clientOptions}
            placeholder={app.clients.length ? 'Select client' : 'No clients loaded'}
          />
        </Field>
      )}
      {needs.includes('demo') && (
        <Field label="Portfolio client (live demo book)">
          <Select
            ariaLabel="Portfolio client"
            value={app.demoClientId}
            onChange={app.setDemoClientId}
            options={app.demoClientOptions}
            placeholder={app.demoClients.length ? 'Select client' : 'No clients loaded'}
          />
        </Field>
      )}
      {needs.includes('workflow') && (
        <Field label="Workflow (live instances)">
          <Select
            ariaLabel="Workflow"
            value={app.workflowId}
            onChange={app.setWorkflowId}
            options={app.workflowOptions}
            placeholder={app.workflows.length ? 'Select workflow' : 'No workflows yet'}
          />
        </Field>
      )}
      {needs.includes('book') && (
        <Field label="Book (live session)">
          <Select
            ariaLabel="Book"
            value={app.bookId}
            onChange={app.setBookId}
            options={(app.session?.books || []).map((b) => ({ value: b.book_id, label: b.display_name }))}
            placeholder="No books in session"
          />
        </Field>
      )}
      <div className="flex items-end pb-0.5 text-[10px] text-muted-foreground lg:col-span-4 -mt-1">
        Your selections stay in sync across every workspace and reflect live records.
      </div>
      </CardContent>
    </Card>
  );
}

/** Build a select-based path parameter bound to live context data. */
export function contextParam(
  name: string,
  label: string,
  value: string,
  options: { value: string; label: string }[],
  extra: Partial<ParamSpec> = {},
): ParamSpec {
  return {
    name,
    label,
    in: 'path',
    type: 'select',
    default: value,
    options,
    ...extra,
  };
}

export function Grid({ children, cols = 2 }: { children: ReactNode; cols?: 1 | 2 | 3 }) {
  const cls = cols === 1 ? '' : cols === 3 ? 'lg:grid-cols-3' : 'lg:grid-cols-2';
  return <div className={`grid grid-cols-1 gap-5 ${cls}`}>{children}</div>;
}

/**
 * A live, executable operation with an editable JSON request body. Used for
 * the strict contract endpoints whose payloads are defined by OpenAPI schemas.
 */
export function OperationPanel({
  title,
  subtitle,
  method = 'POST',
  path,
  params = [],
  bodyDefault = '{}',
  headers,
  auto,
  autoKey,
  deps,
  actionLabel,
  rowsOf,
}: {
  title: string;
  subtitle: string;
  method?: 'POST' | 'PATCH' | 'PUT' | 'GET';
  path: string | ((values: Record<string, string>) => string);
  params?: ParamSpec[];
  bodyDefault?: string;
  headers?: Record<string, string>;
  /**
   * Read-only operations load automatically. Mutations stay behind an explicit
   * click: auto-firing a POST on mount would write a duplicate row on every
   * page visit and on every live-context change.
   */
  auto?: boolean;
  autoKey?: string;
  deps?: unknown[];
  actionLabel?: string;
  rowsOf?: (data: any) => any[];
}) {
  const shouldAuto = auto ?? (method === 'GET');
  return (
    <QueryPanel
      title={title}
      subtitle={subtitle}
      method={method}
      path={path}
      params={[
        ...params,
        {
          name: 'bodyJson',
          // Raw JSON is a technical escape hatch, not part of the advisory
          // workflow. Keep it available but collapsed behind Advanced options.
          label: 'Details to submit',
          in: 'none',
          type: 'json',
          default: bodyDefault,
          placeholder: '{ … }',
          advanced: true,
        } as ParamSpec,
      ]}
      body={(v) => {
        try {
          return JSON.parse(v.bodyJson || '{}');
        } catch {
          return {};
        }
      }}
      headers={headers}
      auto={shouldAuto}
      autoKey={autoKey}
      deps={deps}
      actionLabel={actionLabel}
      rowsOf={rowsOf}
    />
  );
}
