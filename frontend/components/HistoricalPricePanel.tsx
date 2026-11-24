'use client';

/**
 * Live "Historical prices" panel for the Market Data page.
 *
 * Replaces the generic table QueryPanel with a real stock chart. Reads auto-load
 * on mount and whenever the symbol / bar count changes (debounced), consistent
 * with the rest of the workbench. Nothing is invented: the chart plots exactly
 * the OHLCV bars returned by GET /market/historical/{symbol}.
 */
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { get, ApiError } from '@/lib/endpoints';
import StockPriceChart, {
  type OhlcBar,
  type StockChartMode,
} from '@/components/StockPriceChart';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; error: unknown }
  | { status: 'success'; symbol: string; bars: OhlcBar[]; raw: unknown };

const UP = '#dc2626';
const DOWN = '#16a34a';

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

/** Accept the bare `{symbol,data,count}` payload and any envelope variant. */
function normaliseBars(payload: unknown): OhlcBar[] {
  const root: any = payload;
  const rows: unknown[] = Array.isArray(root)
    ? root
    : Array.isArray(root?.data)
      ? root.data
      : Array.isArray(root?.data?.data)
        ? root.data.data
        : [];
  return rows
    .filter(isRecord)
    .map((r: Record<string, unknown>): OhlcBar => ({
      timestamp: typeof r.timestamp === 'string' ? r.timestamp : '',
      open: Number(r.open),
      high: Number(r.high),
      low: Number(r.low),
      close: Number(r.close),
      volume: Number(r.volume ?? 0),
    }))
    .filter((b: OhlcBar) => [b.open, b.high, b.low, b.close].every(Number.isFinite));
}

function errorInfo(error: unknown): { message: string; status?: number; code?: string } {
  const api = error instanceof ApiError ? error : null;
  return {
    message: error instanceof Error ? error.message : 'Request failed',
    status: api?.status,
    code: api?.code,
  };
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="min-w-[86px]">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-sm font-semibold tabular-nums" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}

export default function HistoricalPricePanel() {
  const [symbolInput, setSymbolInput] = useState('0005.HK');
  const [symbol, setSymbol] = useState('0005.HK');
  const [limit, setLimit] = useState('30');
  const [mode, setMode] = useState<StockChartMode>('candles');
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [rawOpen, setRawOpen] = useState(false);
  const seqRef = useRef(0);

  // Debounce free-text symbol entry so typing does not fire one request per key.
  useEffect(() => {
    const t = setTimeout(() => setSymbol(symbolInput.trim()), 400);
    return () => clearTimeout(t);
  }, [symbolInput]);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setState({ status: 'loading' });
    const s = symbol.trim();
    if (!s) {
      setState({ status: 'error', error: new Error('Enter a symbol to load prices.') });
      return;
    }
    try {
      const res = await get(`/market/historical/${encodeURIComponent(s)}`, {
        limit: Number(limit),
        // Cold-cache Alpha Vantage calls sit behind a rate-limit wait plus a 20s
        // upstream timeout on the backend; do not let the default 20s axios
        // timeout fire first.
        timeout: 45000,
      });
      if (seq !== seqRef.current) return;
      const bars = normaliseBars(res.data);
      const returnedSymbol =
        (isRecord(res.data) && typeof (res.data as any).symbol === 'string'
          ? (res.data as any).symbol
          : s) || s;
      setState({ status: 'success', symbol: returnedSymbol, bars, raw: res.raw });
    } catch (e) {
      if (seq !== seqRef.current) return;
      setState({ status: 'error', error: e });
    }
  }, [symbol, limit]);

  useEffect(() => {
    void load();
    return () => {
      seqRef.current += 1; // invalidate in-flight requests
    };
  }, [load]);

  const summary = useMemo(() => {
    if (state.status !== 'success' || state.bars.length === 0) return null;
    const bars = state.bars;
    const first = bars[0];
    const last = bars[bars.length - 1];
    const change = last.close - first.open;
    const pct = first.open !== 0 ? (change / first.open) * 100 : 0;
    return {
      last: last.close,
      change,
      pct,
      high: Math.max(...bars.map((b) => b.high)),
      low: Math.min(...bars.map((b) => b.low)),
      count: bars.length,
    };
  }, [state]);

  let body: ReactNode;
  if (state.status === 'loading') {
    body = (
      <div className="space-y-3">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-[340px] w-full" />
      </div>
    );
  } else if (state.status === 'error') {
    const info = errorInfo(state.error);
    body = (
      <div className="rounded-md border border-border bg-muted/30 p-4">
        <div className="text-sm font-semibold">Could not load price history</div>
        <p className="mt-1 text-sm text-muted-foreground">{info.message}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
          {info.status !== undefined && <Badge variant="outline">HTTP {info.status}</Badge>}
          {info.code && <Badge variant="outline">Code: {info.code}</Badge>}
        </div>
        <div className="mt-3">
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      </div>
    );
  } else if (state.bars.length === 0) {
    body = (
      <div className="flex h-[260px] items-center justify-center rounded-md border border-dashed border-border text-sm text-muted-foreground">
        No history returned for {state.symbol}
      </div>
    );
  } else {
    body = <StockPriceChart bars={state.bars} symbol={state.symbol} mode={mode} height={340} />;
  }

  const up = summary ? summary.change >= 0 : true;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">Historical prices</CardTitle>
            <CardDescription>Price history for this instrument</CardDescription>
          </div>
          <div className="flex items-center gap-1.5">
            {summary && <Badge variant="outline">{summary.count} bars</Badge>}
            <Button variant="outline" size="sm" onClick={() => void load()}>
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-[150px] flex-1">
            <Label htmlFor="history-symbol" className="text-[11px] text-muted-foreground">
              Symbol
            </Label>
            <Input
              id="history-symbol"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value)}
              placeholder="e.g. 0005.HK"
              className="mt-1 h-8 font-mono text-xs"
            />
          </div>
          <div className="w-[110px]">
            <Label className="text-[11px] text-muted-foreground">Bars</Label>
            <Select value={limit} onValueChange={setLimit}>
              <SelectTrigger className="mt-1 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="30">30</SelectItem>
                <SelectItem value="50">50</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant={mode === 'candles' ? 'default' : 'outline'}
              onClick={() => setMode('candles')}
            >
              Candles
            </Button>
            <Button
              size="sm"
              variant={mode === 'line' ? 'default' : 'outline'}
              onClick={() => setMode('line')}
            >
              Line
            </Button>
          </div>
        </div>

        {summary && (
          <>
            <Separator />
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
              <Stat label="Last close" value={summary.last.toFixed(2)} />
              <Stat
                label="Change"
                value={`${up ? '+' : ''}${summary.change.toFixed(2)} (${up ? '+' : ''}${summary.pct.toFixed(2)}%)`}
                color={up ? UP : DOWN}
              />
              <Stat label="High" value={summary.high.toFixed(2)} />
              <Stat label="Low" value={summary.low.toFixed(2)} />
            </div>
          </>
        )}

        {body}

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: UP }} />
            Up / 涨
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: DOWN }} />
            Down / 跌
          </span>
          <span>Faded bars = volume</span>
          <span className="ml-auto">Hover a bar for OHLCV and timestamp</span>
        </div>

        <div>
          <button
            onClick={() => setRawOpen((s) => !s)}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            {rawOpen ? 'Hide' : 'Show'} raw response
          </button>
          {rawOpen && state.status === 'success' && (
            <pre className="mt-2 max-h-56 overflow-auto rounded-md border border-border bg-muted/30 p-3 text-[10px]">
              {JSON.stringify(state.raw, null, 2)}
            </pre>
          )}
        </div>

        <p className="text-[10px] leading-relaxed text-muted-foreground">
          The x-axis shows real dates from the price history when distinct timestamps are available;
          it falls back to bar sequence numbers otherwise. Prices are shown exactly as returned by
          the market service.
        </p>
      </CardContent>
    </Card>
  );
}
