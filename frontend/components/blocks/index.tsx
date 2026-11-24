'use client';

/**
 * shadcn/ui "blocks" — composed, reusable sections.
 *
 * The shared WorkbenchUI kit delegates StatCard / DataTable / EmptyState to
 * these blocks so every screen in the app renders through shadcn primitives
 * without each page having to change its imports.
 */
import type { ReactNode } from 'react';
import Link from 'next/link';
import { Inbox } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export interface BlockColumn {
  key: string;
  label: string;
  align?: 'left' | 'right';
  width?: string;
  render?: (row: any) => ReactNode;
}

export function StatBlock({
  label,
  value,
  sub,
  trend,
  href,
  className,
}: {
  label: ReactNode;
  value: ReactNode;
  sub?: ReactNode;
  trend?: ReactNode;
  href?: string;
  className?: string;
}) {
  const body = (
    <Card className={cn('h-full', className)}>
      <CardHeader className="pb-2 pt-4 px-5">
        <CardDescription className="text-[10px] font-semibold uppercase tracking-[0.12em]">
          {label}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0 px-5 pb-4">
        <div className="text-2xl font-semibold tracking-tight tabular-nums">{value}</div>
        {(sub || trend) && (
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {sub}
            {trend}
          </div>
        )}
      </CardContent>
    </Card>
  );
  return href ? (
    <Link href={href} className="block h-full rounded-lg transition-opacity hover:opacity-80">
      {body}
    </Link>
  ) : (
    body
  );
}

export function EmptyBlock({
  title = 'No records yet',
  detail = 'When data is available it will appear here.',
  action,
  className,
}: {
  title?: string;
  detail?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-10 text-center', className)}>
      <Inbox size={22} className="mb-2 text-muted-foreground/50" />
      <div className="text-sm font-medium text-foreground">{title}</div>
      <div className="mt-1 max-w-sm text-xs text-muted-foreground">{detail}</div>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

export function DataTableBlock({
  title,
  subtitle,
  columns,
  rows,
  onRowClick,
  emptyTitle,
  emptyDetail,
  formatCell,
  className,
  bodyClassName,
}: {
  title?: string;
  subtitle?: string;
  columns: BlockColumn[];
  rows: any[];
  onRowClick?: (row: any) => void;
  emptyTitle?: string;
  emptyDetail?: string;
  formatCell?: (value: unknown) => ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  const renderValue = (value: unknown) => (formatCell ? formatCell(value) : String(value ?? ''));

  return (
    <Card className={cn('min-w-0', className)}>
      {(title || subtitle) && (
        <CardHeader className="px-5 py-4">
          {title && <CardTitle className="text-sm">{title}</CardTitle>}
          {subtitle && <CardDescription className="text-xs">{subtitle}</CardDescription>}
        </CardHeader>
      )}
      <CardContent className={cn('p-0', bodyClassName)}>
        {!rows || rows.length === 0 ? (
          <EmptyBlock title={emptyTitle} detail={emptyDetail} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((c) => (
                  <TableHead
                    key={c.key}
                    style={{ width: c.width }}
                    className={cn(
                      'text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground whitespace-nowrap',
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
                        'text-xs align-top',
                        c.align === 'right' && 'text-right tabular-nums',
                      )}
                    >
                      {c.render ? c.render(row) : renderValue((row as any)?.[c.key])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
