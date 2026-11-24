'use client';

/**
 * Shared presentation kit for the WM Workbench.
 *
 * Uses only the existing Capco monochrome palette (black / white / gray scale)
 * and the existing Inter typeface. Semantic status colours come from the
 * variables already declared in app/globals.css — no new colours are introduced.
 */
import React, { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, ChevronDown, ChevronRight, RefreshCw, Loader2 } from 'lucide-react';
import { ApiError, ApiResult, call, Method } from '@/lib/endpoints';
import { cn } from '@/lib/utils';
import { Button as ShadcnButton } from '@/components/ui/button';
import {
  Card as ShadcnCard,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge as ShadcnBadge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Select as ShadcnSelect,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { EmptyBlock, StatBlock } from '@/components/blocks';

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function PageShell({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <div className={`mx-auto w-full px-6 lg:px-8 py-7 ${wide ? 'max-w-[1800px]' : 'max-w-[1440px]'}`}>
      {children}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && (
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-500 mb-1.5">
            {eyebrow}
          </div>
        )}
        <h1 className="text-[26px] leading-tight font-semibold tracking-tight text-black">{title}</h1>
        {description && <p className="mt-1.5 text-sm text-gray-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Card({
  title,
  subtitle,
  action,
  children,
  className = '',
  bodyClassName = '',
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <ShadcnCard className={cn('flex flex-col', className)}>
      {(title || action || subtitle) && (
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 px-5 py-4">
          <div className="min-w-0">
            {title && <CardTitle className="text-sm">{title}</CardTitle>}
            {subtitle && <CardDescription className="mt-0.5 text-xs">{subtitle}</CardDescription>}
          </div>
          {action}
        </CardHeader>
      )}
      <CardContent className={cn('flex-1 min-w-0 p-5', bodyClassName)}>{children}</CardContent>
    </ShadcnCard>
  );
}

export function ViewAll({ href, label = 'View all' }: { href: string; label?: string }) {
  return (
    <Link
      href={href}
      className="shrink-0 text-xs font-medium text-gray-600 hover:text-black inline-flex items-center gap-1"
    >
      {label} <span aria-hidden>→</span>
    </Link>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-500 mb-3">
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Controls
// ---------------------------------------------------------------------------

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

export function Button({
  children,
  onClick,
  variant = 'secondary',
  disabled,
  loading,
  type = 'button',
  title,
  className = '',
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
  title?: string;
  className?: string;
}) {
  const variants: Record<ButtonVariant, 'default' | 'outline' | 'ghost' | 'destructive'> = {
    primary: 'default',
    secondary: 'outline',
    ghost: 'ghost',
    danger: 'destructive',
  };
  return (
    <ShadcnButton
      type={type}
      title={title}
      variant={variants[variant]}
      size="sm"
      disabled={disabled || loading}
      onClick={onClick}
      className={cn('gap-1.5 text-xs', className)}
    >
      {loading && <Loader2 size={13} className="animate-spin" />}
      {children}
    </ShadcnButton>
  );
}

export function TextInput({
  value,
  onChange,
  placeholder,
  type = 'text',
  className = '',
  ariaLabel,
}: {
  value: string | number;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <Input
      aria-label={ariaLabel || placeholder}
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={cn('h-8 text-xs', className)}
    />
  );
}

export function Select({
  value,
  onChange,
  options,
  placeholder = 'Select…',
  className = '',
  ariaLabel,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  className?: string;
  ariaLabel?: string;
}) {
  const choices = options.filter((o) => o.value !== '');
  return (
    <ShadcnSelect value={value || undefined} onValueChange={onChange}>
      <SelectTrigger
        aria-label={ariaLabel || placeholder}
        className={cn('h-8 text-xs', className)}
      >
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {choices.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </ShadcnSelect>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="block min-w-0">
      <Label className="mb-1 block text-[11px] font-medium text-muted-foreground">{label}</Label>
      {children}
      {hint && <span className="mt-1 block text-[10px] text-muted-foreground">{hint}</span>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="space-y-2 py-8">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 size={14} className="animate-spin" /> {label}
      </div>
      <Skeleton className="h-3 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}

export function EmptyState({
  title = 'No records yet',
  detail = 'When data is available it will appear here.',
  action,
}: {
  title?: string;
  detail?: string;
  action?: ReactNode;
}) {
  return <EmptyBlock title={title} detail={detail} action={action} />;
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error);
  const status = error instanceof ApiError ? error.status : undefined;
  const code = error instanceof ApiError ? error.code : undefined;
  return (
    <Alert variant="destructive">
      <AlertCircle size={15} className="mt-0.5 shrink-0" />
      <div className="min-w-0">
        <AlertTitle className="text-sm font-medium">
          Request failed{status ? ` (HTTP ${status})` : ''}
        </AlertTitle>
        <AlertDescription className="mt-1 break-words text-xs">
          {message}
          {code && <span className="ml-2 font-mono text-[10px] opacity-70">{code}</span>}
        </AlertDescription>
        {onRetry && (
          <Button className="mt-3" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    </Alert>
  );
}

export function StatusBadge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'success' | 'warning' | 'error' | 'info';
}) {
  const color =
    tone === 'neutral'
      ? 'var(--capco-gray-600)'
      : `var(--color-${tone})`;
  return (
    <ShadcnBadge
      variant="outline"
      className="text-[10px] font-semibold uppercase tracking-wide"
      style={{ color, borderColor: color, background: 'transparent' }}
    >
      {children}
    </ShadcnBadge>
  );
}

// ---------------------------------------------------------------------------
// Data rendering
// ---------------------------------------------------------------------------

export type Column<T = any> = {
  key: string;
  label: string;
  align?: 'left' | 'right';
  width?: string;
  render?: (row: T) => ReactNode;
};

export function DataTable<T = any>({
  columns,
  rows,
  onRowClick,
  emptyTitle,
  emptyDetail,
}: {
  columns: Column<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDetail?: string;
}) {
  if (!rows || rows.length === 0) {
    return <EmptyState title={emptyTitle} detail={emptyDetail} />;
  }
  return (
    <div className="overflow-x-auto -mx-5 -my-5">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            {columns.map((c) => (
              <TableHead
                key={c.key}
                style={{ width: c.width }}
                className={cn(
                  'whitespace-nowrap px-5 py-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground',
                  c.align === 'right' && 'text-right',
                )}
              >
                {c.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, i) => (
            <TableRow
              key={i}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={onRowClick ? 'cursor-pointer' : undefined}
            >
              {columns.map((c) => (
                <TableCell
                  key={c.key}
                  className={cn(
                    'px-5 py-3 text-xs align-top',
                    c.align === 'right' && 'text-right tabular-nums',
                  )}
                >
                  {c.render ? c.render(row) : formatCell((row as any)?.[c.key])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function formatCell(value: unknown): ReactNode {
  if (value === null || value === undefined || value === '') {
    return <span className="text-gray-300">—</span>;
  }
  if (typeof value === 'boolean') {
    return <StatusBadge tone={value ? 'success' : 'neutral'}>{value ? 'Yes' : 'No'}</StatusBadge>;
  }
  if (typeof value === 'number') {
    return <span className="tabular-nums">{value.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>;
  }
  if (Array.isArray(value)) {
    return value.length ? `${value.length} item${value.length > 1 ? 's' : ''}` : <span className="text-gray-300">—</span>;
  }
  if (typeof value === 'object') {
    const summary = (value as any).description
      || (value as any).name
      || (value as any).title
      || (value as any).label;
    if (typeof summary === 'string' && summary.trim()) {
      return <span className="text-gray-700">{summary}</span>;
    }
    return <span className="text-gray-300">—</span>;
  }
  const text = String(value);
  if (isMachineValue(text)) {
    return <span className="text-gray-300">—</span>;
  }
  if (/^\d{4}-\d{2}-\d{2}T/.test(text)) {
    const d = new Date(text);
    if (!Number.isNaN(d.getTime())) return d.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });
  }
  return text;
}

export function StatCard({
  label,
  value,
  sub,
  href,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  href?: string;
}) {
  return <StatBlock label={label} value={value} sub={sub} href={href} />;
}

function JsonNode({ value, name, depth = 0 }: { value: unknown; name?: string; depth?: number }) {
  const [open, setOpen] = useState(depth < 1);
  const isObj = value !== null && typeof value === 'object';
  if (!isObj) {
    if (isMachineValue(value)) return null;
    return (
      <div className="flex gap-2 py-0.5 text-xs">
        {name && <span className="text-gray-500 min-w-[140px] shrink-0">{prettify(name)}</span>}
        <span className="text-black break-all">{formatCell(value)}</span>
      </div>
    );
  }
  const entries = (Array.isArray(value)
    ? value.map((v, i) => [String(i), v] as [string, unknown])
    : Object.entries(value as Record<string, unknown>)
  ).filter(([k, v]) => {
    if (!Array.isArray(value) && isHiddenKey(k)) return false;
    if (!isObj || (v !== null && typeof v === 'object')) return true;
    return hasDisplayValue(v);
  });
  if (entries.length === 0) return null;
  return (
    <div className={depth > 0 ? 'ml-3 border-l border-gray-200 pl-3' : ''}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs font-medium text-gray-700 py-0.5 hover:text-black"
      >
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        {name ? prettify(name) : 'Details'}
        <span className="text-gray-400 font-normal">
          {Array.isArray(value) ? `[${entries.length}]` : `{${entries.length}}`}
        </span>
      </button>
      {open && entries.map(([k, v]) => <JsonNode key={k} name={k} value={v} depth={depth + 1} />)}
    </div>
  );
}

/** Render any live API payload as a readable table, key/value list or tree. */
export function DataView<T = any>({
  data,
  columns,
  rowsOf,
  emptyTitle,
  emptyDetail,
  onRowClick,
}: {
  data: T;
  columns?: Column[];
  rowsOf?: (data: T) => any[];
  emptyTitle?: string;
  emptyDetail?: string;
  onRowClick?: (row: any) => void;
}) {
  const rows = useMemo(() => (rowsOf ? rowsOf(data) : extractArray(data)), [data, rowsOf]);

  if (rows && rows.length > 0) {
    const cols: Column[] = columns || humanColumns(rows);
    return <DataTable columns={cols} rows={rows} onRowClick={onRowClick} />;
  }

  if (Array.isArray(data) && data.length === 0) {
    return <EmptyState title={emptyTitle} detail={emptyDetail} />;
  }

  if (data && typeof data === 'object') {
    const entries = Object.entries(data as Record<string, unknown>).filter(([k, v]) => {
      if (isHiddenKey(k)) return false;
      if (isMachineValue(v)) return false;
      return true;
    });
    if (entries.length === 0) return <EmptyState title={emptyTitle} detail={emptyDetail} />;
    const flat = entries.every(([, v]) => v === null || typeof v !== 'object' || v === undefined);
    if (flat) {
      return (
        <div className="divide-y divide-gray-100">
          {entries.map(([k, v]) => (
            <div key={k} className="flex flex-wrap gap-2 py-2 text-xs">
              <span className="w-48 shrink-0 text-gray-500">{prettify(k)}</span>
              <span className="text-black min-w-0 break-words">{formatCell(v)}</span>
            </div>
          ))}
        </div>
      );
    }
    return <JsonNode value={data} />;
  }

  if (data === null || data === undefined || data === '') {
    return <EmptyState title={emptyTitle} detail={emptyDetail} />;
  }
  return <div className="text-xs text-black break-words">{String(data)}</div>;
}

export function extractArray(value: any): any[] | null {
  if (Array.isArray(value)) return value;
  if (!value || typeof value !== 'object') return null;
  // Common envelope shapes: {clients: []}, {items: []}, {events: []}, {breakdown: []}
  for (const key of ['items', 'clients', 'events', 'rows', 'results', 'breakdown', 'data', 'gates', 'news', 'quotes', 'signals', 'holdings', 'priorities', 'relationships', 'messages', 'evaluations']) {
    if (Array.isArray(value[key])) return value[key];
  }
  const arrayValues = Object.values(value).filter(Array.isArray) as any[][];
  if (arrayValues.length === 1) return arrayValues[0];
  return null;
}

/**
 * Technical field names are still present in live payloads. Translate the
 * common ones into the words a relationship manager would use in a column
 * header, and soften the rest so no screen reads like a database dump.
 */
const KEY_LABELS: Record<string, string> = {
  // Form / path params that still use prettify when no explicit label is set.
  tenant_id: 'Organisation',
  book_id: 'Book',
  client_id: 'Client',
  workflow_id: 'Workflow',
  meeting_id: 'Meeting',
  symbol: 'Instrument',
  metric_name: 'Activity type',
  created_at: 'Created',
  updated_at: 'Updated',
  from_time: 'From',
  to_time: 'To',
  occurred_at: 'Occurred',
  timestamp: 'Time',
  feed_timestamp: 'Time',
  source_id: 'Source',
  signal_type: 'Signal',
  change_percent: 'Change %',
  prev_close: 'Previous close',
  status: 'Status',
  score: 'Score',
  reason: 'Reason',
  name: 'Name',
  title: 'Title',
  summary: 'Summary',
  content: 'Summary',
  description: 'Description',
  value_usd_millions: 'Value (USD m)',
  unrealized_gain_pct: 'Unrealised gain (%)',
  allocation_pct: 'Allocation (%)',
  weight_pct: 'Weight (%)',
  aum: 'Assets under management',
};

/**
 * Machine identifiers and transport fields stay in the payload for linking and
 * technical details, but they are never auto-rendered as table columns.
 */
const HIDDEN_KEYS = new Set([
  'id',
  'uuid',
  'guid',
  'url',
  'sourceurl',
  'source_url',
  'link',
  'href',
  'source_kind',
  'quoted_symbol',
  'symbols',
  'mode',
  'version',
  'version_stamp',
  'record_version',
  'item_hash',
  'content_hash',
  'synthetic_marker',
  'ingested_at',
  'licence_tag',
  'excluded_from_brief',
  'attribution',
  'correlation_id',
  'environment',
  'availability',
  'capability_state',
  'completeness',
  'review_state',
  'live_response',
  'limitation_codes',
  'authoritative_owner',
  'system_key',
  'record_id',
  'retrieved_at',
]);

const PREFERRED_KEYS = [
  'title',
  'name',
  'symbol',
  'price',
  'change',
  'change_percent',
  'volume',
  'signal_type',
  'content',
  'summary',
  'description',
  'source',
  'source_id',
  'timestamp',
  'feed_timestamp',
  'as_of',
  'status',
  'score',
  'reason',
  'open',
  'high',
  'low',
  'prev_close',
];

function isHiddenKey(key: string): boolean {
  const normalized = key.trim().toLowerCase();
  if (HIDDEN_KEYS.has(normalized)) return true;
  if (
    /(_id|_uuid|_guid|_hash|_href|_url|_ref)$/.test(normalized)
    && normalized !== 'source_id'
  ) {
    return true;
  }
  return false;
}

function isMachineValue(value: unknown): boolean {
  if (typeof value !== 'string') return false;
  const text = value.trim();
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(text)) return true;
  if (/^[0-9a-f]{32}$/i.test(text)) return true;
  if (/^https?:\/\//i.test(text)) return true;
  return false;
}

function hasDisplayValue(value: unknown): boolean {
  if (value === null || value === undefined || value === '') return false;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'object') return false;
  if (isMachineValue(value)) return false;
  return true;
}

function visibleKeys(rows: any[]): string[] {
  const keys = Array.from(
    new Set(rows.flatMap((row) => (row && typeof row === 'object' ? Object.keys(row) : []))),
  ).filter((key) => {
    if (isHiddenKey(key)) return false;
    return rows.some((row) => hasDisplayValue(row?.[key]));
  });

  const preferred = PREFERRED_KEYS.filter((key) => keys.includes(key));
  const rest = keys.filter((key) => !preferred.includes(key));
  return [...preferred, ...rest].slice(0, 9);
}

function humanColumns(rows: any[]): Column[] {
  return visibleKeys(rows).map((key) => {
    if (key === 'title') {
      return {
        key,
        label: prettify(key),
        render: (row: any) => {
          const title = row?.title || row?.headline || 'Untitled';
          const href = row?.url || row?.sourceUrl || row?.source_url || row?.link;
          if (typeof href === 'string' && /^https?:\/\//i.test(href)) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="font-medium text-black hover:underline">
                {title}
              </a>
            );
          }
          return title;
        },
      };
    }
    if (key === 'content' || key === 'summary' || key === 'description') {
      return {
        key,
        label: prettify(key),
        render: (row: any) => {
          const text = String(row?.[key] || '').trim();
          if (!text) return <span className="text-gray-300">—</span>;
          return <span className="line-clamp-2 text-gray-700">{text}</span>;
        },
      };
    }
    if (key === 'signal_type') {
      return {
        key,
        label: prettify(key),
        render: (row: any) => {
          const raw = String(row?.signal_type || '').trim();
          if (!raw) return <span className="text-gray-300">—</span>;
          const label = raw.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
          return <StatusBadge tone={raw.toUpperCase() === 'RISK' ? 'error' : 'success'}>{label}</StatusBadge>;
        },
      };
    }
    return {
      key,
      label: prettify(key),
      align: ['price', 'change', 'change_percent', 'volume', 'open', 'high', 'low', 'prev_close', 'score'].includes(key)
        ? 'right'
        : 'left',
    };
  });
}

export function prettify(key: string): string {
  if (KEY_LABELS[key]) return KEY_LABELS[key];
  return key
    .replace(/_pct$/, ' (%)')
    .replace(/_usd_millions$/, ' (USD m)')
    .replace(/_id$/, ' reference')
    .replace(/_at$/, ' date')
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

// ---------------------------------------------------------------------------
// Live query panel — the building block for every feature screen
// ---------------------------------------------------------------------------

export type BodyValue =
  | Record<string, any>
  | any[]
  | string
  | number
  | boolean
  | null
  | ((values: Record<string, string>) => unknown);

export interface ParamSpec {
  name: string;
  label?: string;
  in?: 'path' | 'query' | 'body' | 'none';
  type?: 'text' | 'number' | 'json' | 'datetime' | 'select';
  default?: string;
  options?: { value: string; label: string }[];
  required?: boolean;
  placeholder?: string;
  /** Technical fields (e.g. raw JSON bodies) are collapsed by default. */
  advanced?: boolean;
}

export function QueryPanel({
  title,
  subtitle,
  method = 'GET',
  path,
  params = [],
  body,
  headers,
  columns,
  rowsOf,
  action,
  auto = true,
  deps = [],
  autoKey,
  actionLabel,
  emptyTitle,
  emptyDetail,
  buildPath,
  buildQuery,
  onRowClick,
}: {
  title: string;
  subtitle?: string;
  method?: Method;
  path: string | ((values: Record<string, string>) => string);
  params?: ParamSpec[];
  body?: BodyValue;
  headers?: Record<string, string> | ((values: Record<string, string>) => Record<string, string>);
  columns?: Column[];
  rowsOf?: (data: any) => any[];
  action?: ReactNode;
  auto?: boolean;
  deps?: unknown[];
  /** Stable key that forces an auto panel to reload when live context changes. */
  autoKey?: string;
  /** Label for the explicit execution button on non-auto panels. */
  actionLabel?: string;
  emptyTitle?: string;
  emptyDetail?: string;
  buildPath?: (values: Record<string, string>) => string;
  buildQuery?: (values: Record<string, string>) => Record<string, any>;
  onRowClick?: (row: any) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(params.map((p) => [p.name, p.default ?? ''])),
  );
  const [result, setResult] = useState<ApiResult<any> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [showTechnical, setShowTechnical] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const resolvePath = useCallback(() => {
    if (typeof path === 'function') return path(values);
    let p = buildPath ? buildPath(values) : path;
    params
      .filter((x) => (x.in || 'path') === 'path')
      .forEach((x) => {
        p = p.replace(`{${x.name}}`, encodeURIComponent(values[x.name] || x.default || ''));
      });
    return p;
  }, [path, params, values, buildPath]);

  // A path with an empty placeholder resolves to an unroutable URL (for
  // example `/workflows//messages` -> 404 Not Found). Do not fire the request
  // at all: show a prompt to select the missing context value instead.
  const emptyPathParam = params.find(
    (p) => (p.in || 'path') === 'path' && !(values[p.name] ?? '').trim(),
  );
  const resolved = resolvePath();
  const malformedPath =
    /\/{2}|undefined|%7B|\{[A-Za-z_]+\}/.test(resolved) ||
    (Boolean(emptyPathParam) && /\/$/.test(resolved));
  const blocked = malformedPath;
  const blockedLabel = emptyPathParam?.label || 'a context value';

  const execute = useCallback(async () => {
    if (blocked) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const query: Record<string, any> = buildQuery ? buildQuery(values) : {};
      params
        .filter((x) => x.in === 'query')
        .forEach((x) => {
          const v = values[x.name];
          if (v !== undefined && v !== '') query[x.name] = v;
        });

      let payload: unknown = typeof body === 'function' ? body(values) : body;
      const bodyParams = params.filter((x) => x.in === 'body');
      if (bodyParams.length) {
        const extra: Record<string, unknown> = {};
        bodyParams.forEach((x) => {
          const v = values[x.name];
          if (v === undefined || v === '') return;
          if (x.type === 'json') {
            try {
              extra[x.name] = JSON.parse(v);
            } catch {
              extra[x.name] = v;
            }
          } else if (x.type === 'number') {
            extra[x.name] = Number(v);
          } else {
            extra[x.name] = v;
          }
        });
        payload = payload && typeof payload === 'object' ? { ...(payload as object), ...extra } : extra;
      }

      const extraHeaders = typeof headers === 'function' ? headers(values) : headers;
      const res = await call<any>(method, resolvePath(), { query, body: payload, headers: extraHeaders });
      setResult(res);
    } catch (e) {
      setError(e);
      setResult(null);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [method, path, params, body, headers, values, buildPath, buildQuery, resolvePath, blocked]);

  useEffect(() => {
    if (auto) void execute();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto, autoKey, blocked, ...deps]);

  const url = resolvePath();
  const visibleParams = params.filter((p) => !p.advanced);
  const advancedParams = params.filter((p) => p.advanced);

  const renderField = (p: ParamSpec) => (
    <Field key={p.name} label={p.label || prettify(p.name)}>
      {p.type === 'select' && p.options ? (
        <Select
          ariaLabel={p.label || p.name}
          value={values[p.name] ?? ''}
          onChange={(v) => setValues((s) => ({ ...s, [p.name]: v }))}
          options={p.options}
          placeholder={p.placeholder || 'Select…'}
        />
      ) : p.type === 'json' ? (
        <textarea
          aria-label={p.label || p.name}
          value={values[p.name] ?? ''}
          placeholder={p.placeholder}
          onChange={(e) => setValues((s) => ({ ...s, [p.name]: e.target.value }))}
          rows={3}
          spellCheck={false}
          className="w-full px-2.5 py-1.5 font-mono text-[11px] text-black bg-white border border-gray-300 rounded outline-none focus:border-black resize-y"
        />
      ) : (
        <TextInput
          ariaLabel={p.label || p.name}
          type={p.type === 'number' ? 'number' : p.type === 'datetime' ? 'datetime-local' : 'text'}
          value={values[p.name] ?? ''}
          onChange={(v) => setValues((s) => ({ ...s, [p.name]: v }))}
          placeholder={p.placeholder}
        />
      )}
    </Field>
  );

  return (
    <Card
      title={title}
      subtitle={subtitle}
      bodyClassName="p-0"
      action={
        <div className="flex items-center gap-1.5">
          {action}
          {auto ? (
            <button
              onClick={() => void execute()}
              title={blocked ? `Select ${blockedLabel} first` : 'Refresh'}
              aria-label="Refresh"
              disabled={blocked}
              className="p-1.5 text-gray-500 hover:text-black hover:bg-gray-100 rounded disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          ) : (
            <Button onClick={() => void execute()} loading={loading} disabled={blocked}>
              {actionLabel || 'Run'}
            </Button>
          )}
        </div>
      }
    >
      {visibleParams.length > 0 && (
        <div className="px-5 py-3 border-b border-gray-200 bg-gray-50 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {visibleParams.map(renderField)}
        </div>
      )}

      {advancedParams.length > 0 && (
        <div className="px-5 py-2 border-b border-gray-100">
          <button
            onClick={() => setShowAdvanced((s) => !s)}
            className="text-[10px] text-gray-400 hover:text-black"
          >
            {showAdvanced ? 'Hide' : 'Show'} advanced options
          </button>
          {showAdvanced && (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {advancedParams.map(renderField)}
            </div>
          )}
        </div>
      )}

      <div className="p-5 min-h-[90px]">
        {blocked ? (
          <EmptyState
            title={`Select ${blockedLabel} first`}
            detail="This panel needs a selected value before it can load live data. No request was sent."
          />
        ) : loading && !result ? (
          <Loading />
        ) : error ? (
          <ErrorState error={error} onRetry={() => void execute()} />
        ) : result ? (
          <>
            <DataView
              data={result.data}
              columns={columns}
              rowsOf={rowsOf}
              emptyTitle={emptyTitle}
              emptyDetail={emptyDetail}
              onRowClick={onRowClick}
            />
            <button
              onClick={() => setShowTechnical((s) => !s)}
              className="mt-3 text-[10px] text-gray-400 hover:text-black"
            >
              {showTechnical ? 'Hide' : 'Show'} technical details
            </button>
            {showTechnical && (
              <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-[10px] text-gray-700">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <code className="truncate">
                    <span className="font-semibold">{method}</span> {url}
                  </code>
                  <span className="shrink-0 text-gray-500">HTTP {result.status}</span>
                </div>
                <pre className="overflow-x-auto max-h-72 whitespace-pre-wrap">
                  {JSON.stringify(result.raw, null, 2)}
                </pre>
              </div>
            )}
          </>
        ) : (
          <EmptyState
            title={method === 'GET' ? 'Not loaded yet' : 'Not executed yet'}
            detail={
              actionLabel
                ? `Use ${actionLabel} to execute this action. Read-only panels load automatically.`
                : 'Use Run to load live data.'
            }
          />
        )}
      </div>
    </Card>
  );
}
