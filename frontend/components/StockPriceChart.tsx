'use client';

/**
 * Stock price chart for GET /market/historical/{symbol}.
 *
 * Renders the OHLCV bars returned by the market service as a candlestick chart
 * with a volume panel, or as a close-price line. No data is invented: when the
 * bars carry distinct parseable timestamps the x-axis shows real dates; it
 * falls back to bar sequence numbers only if timestamps are missing or uniform.
 * The full timestamp is always shown on hover.
 *
 * Colour convention follows the Chinese / HK market: 涨 (up) = red, 跌 (down) = green.
 */
import { useEffect, useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from 'react';

export interface OhlcBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type StockChartMode = 'candles' | 'line';

interface StockPriceChartProps {
  bars: OhlcBar[];
  symbol: string;
  mode?: StockChartMode;
  height?: number;
}

const UP = '#dc2626';
const DOWN = '#16a34a';
const PAD = { top: 14, right: 62, bottom: 26, left: 10 };
const GAP = 14;
const VOLUME_RATIO = 0.2;

function priceLabel(v: number): string {
  return Number.isFinite(v) ? v.toFixed(2) : '—';
}

function volumeLabel(v: number): string {
  if (!Number.isFinite(v)) return '—';
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}K`;
  return String(v);
}

function timeLabel(ts: string): string {
  if (!ts) return '—';
  if (/^\d{4}-\d{2}-\d{2}$/.test(ts)) return ts; // date-only fixture (daily bars)
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? ts : d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
}

function dateLabel(ts: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(ts)) return ts.slice(5); // MM-DD
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? '' : d.toISOString().slice(5, 10);
}

export default function StockPriceChart({
  bars,
  symbol,
  mode = 'candles',
  height = 340,
}: StockPriceChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [width, setWidth] = useState(760);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const measure = () => {
      const w = Math.floor(el.getBoundingClientRect().width);
      if (w > 0) setWidth(w);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const clean = useMemo(
    () =>
      bars.filter(
        (b) =>
          b &&
          [b.open, b.high, b.low, b.close].every((v) => typeof v === 'number' && Number.isFinite(v)) &&
          b.high >= b.low,
      ),
    [bars],
  );

  const geom = useMemo(() => {
    const n = clean.length;
    const plotW = Math.max(1, width - PAD.left - PAD.right);
    const chartH = Math.max(120, height - PAD.top - PAD.bottom);
    const priceH = (chartH - GAP) * (1 - VOLUME_RATIO);
    const volTop = PAD.top + priceH + GAP;
    const volH = chartH - priceH - GAP;
    const lo = n ? Math.min(...clean.map((b) => b.low)) : 0;
    const hi = n ? Math.max(...clean.map((b) => b.high)) : 1;
    const span = hi - lo || 1;
    const pad = span * 0.08;
    const pMin = lo - pad;
    const pMax = hi + pad;
    const y = (p: number) => PAD.top + ((pMax - p) / (pMax - pMin)) * priceH;
    const vMax = n ? Math.max(...clean.map((b) => Number(b.volume) || 0), 1) : 1;
    const vy = (v: number) => volTop + volH - (v / vMax) * volH;
    const bandW = n ? plotW / n : plotW;
    const cx = (i: number) => PAD.left + (i + 0.5) * bandW;
    const bodyW = Math.max(2, Math.min(bandW * 0.62, 16));
    const ticks = Array.from({ length: 5 }, (_, i) => pMin + ((pMax - pMin) * i) / 4);
    return { n, plotW, chartH, priceH, volTop, volH, pMin, pMax, y, vy, bandW, cx, bodyW, ticks };
  }, [clean, width, height]);

  const active = hover !== null && hover >= 0 && hover < geom.n ? clean[hover] : null;
  const first = clean[0];
  const last = clean[clean.length - 1];

  // Real dates on the x-axis when timestamps are parseable and span more than one
  // calendar day; otherwise fall back to bar sequence numbers (avoids six copies
  // of the same day label when all bars share a timestamp).
  const dated = useMemo(() => {
    if (!clean.length) return false;
    const parsed = clean.map((b) => Date.parse(b.timestamp));
    if (parsed.some((t) => Number.isNaN(t))) return false;
    return new Set(parsed.map((t) => new Date(t).toISOString().slice(0, 10))).size > 1;
  }, [clean]);
  const axisLabel = (i: number) =>
    dated ? dateLabel(clean[i]?.timestamp ?? '') || `#${i + 1}` : `#${i + 1}`;
  const overallUp = Boolean(first && last && last.close >= first.open);
  const lineColor = overallUp ? UP : DOWN;

  const linePath = useMemo(() => {
    if (!geom.n || mode !== 'line') return '';
    return clean
      .map((b, i) => `${i === 0 ? 'M' : 'L'}${geom.cx(i).toFixed(2)},${geom.y(b.close).toFixed(2)}`)
      .join(' ');
  }, [clean, geom, mode]);

  const areaPath = linePath
    ? `${linePath} L${geom.cx(geom.n - 1).toFixed(2)},${(PAD.top + geom.priceH).toFixed(2)} L${geom.cx(0).toFixed(2)},${(PAD.top + geom.priceH).toFixed(2)} Z`
    : '';

  const onMove = (e: ReactMouseEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || !geom.n) return;
    const x = ((e.clientX - rect.left) / rect.width) * width;
    const i = Math.floor((x - PAD.left) / geom.bandW);
    setHover(Math.max(0, Math.min(geom.n - 1, i)));
  };

  if (!geom.n) {
    return (
      <div className="flex h-[260px] items-center justify-center text-sm text-muted-foreground">
        No price bars to chart
      </div>
    );
  }

  const tooltipLeft = Math.max(
    8,
    Math.min(width - 216, (hover !== null ? geom.cx(hover) : 0) + 14),
  );

  return (
    <div ref={wrapRef} className="relative w-full">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        role="img"
        aria-label={`${symbol} ${mode === 'candles' ? 'candlestick' : 'close price'} chart with volume`}
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        className="block"
      >
        {/* price grid + right-hand price axis */}
        {geom.ticks.map((t, i) => (
          <g key={i}>
            <line
              x1={PAD.left}
              x2={PAD.left + geom.plotW}
              y1={geom.y(t)}
              y2={geom.y(t)}
              stroke="hsl(var(--border))"
              strokeWidth={1}
              strokeDasharray={i === 0 || i === geom.ticks.length - 1 ? undefined : '3 4'}
            />
            <text
              x={PAD.left + geom.plotW + 8}
              y={geom.y(t) + 3.5}
              fontSize={10}
              fill="hsl(var(--muted-foreground))"
            >
              {priceLabel(t)}
            </text>
          </g>
        ))}

        {/* volume baseline */}
        <line
          x1={PAD.left}
          x2={PAD.left + geom.plotW}
          y1={geom.volTop + geom.volH}
          y2={geom.volTop + geom.volH}
          stroke="hsl(var(--border))"
          strokeWidth={1}
        />

        {/* candles OR close line */}
        {mode === 'candles'
          ? clean.map((b, i) => {
              const up = b.close >= b.open;
              const color = up ? UP : DOWN;
              const yHigh = geom.y(b.high);
              const yLow = geom.y(b.low);
              const yTop = geom.y(Math.max(b.open, b.close));
              const yBottom = geom.y(Math.min(b.open, b.close));
              const bodyH = Math.max(1.5, yBottom - yTop);
              const x = geom.cx(i);
              return (
                <g key={i}>
                  <line x1={x} x2={x} y1={yHigh} y2={yLow} stroke={color} strokeWidth={1} />
                  <rect
                    x={x - geom.bodyW / 2}
                    y={yTop}
                    width={geom.bodyW}
                    height={bodyH}
                    fill={color}
                    stroke={color}
                    strokeWidth={1}
                  />
                </g>
              );
            })
          : (
              <>
                <path d={areaPath} fill={lineColor} fillOpacity={0.12} />
                <path d={linePath} fill="none" stroke={lineColor} strokeWidth={2} />
                {last && (
                  <circle cx={geom.cx(geom.n - 1)} cy={geom.y(last.close)} r={3.5} fill={lineColor} />
                )}
              </>
            )}

        {/* volume histogram */}
        {clean.map((b, i) => {
          const up = b.close >= b.open;
          const color = up ? UP : DOWN;
          const v = Number(b.volume) || 0;
          const y = geom.vy(v);
          return (
            <rect
              key={`v-${i}`}
              x={geom.cx(i) - geom.bodyW / 2}
              y={y}
              width={geom.bodyW}
              height={Math.max(0, geom.volTop + geom.volH - y)}
              fill={color}
              fillOpacity={0.32}
            />
          );
        })}

        {/* last-price marker */}
        {last && (
          <g>
            <line
              x1={PAD.left}
              x2={PAD.left + geom.plotW}
              y1={geom.y(last.close)}
              y2={geom.y(last.close)}
              stroke={last.close >= last.open ? UP : DOWN}
              strokeWidth={1}
              strokeDasharray="4 4"
              strokeOpacity={0.7}
            />
            <rect
              x={PAD.left + geom.plotW + 2}
              y={geom.y(last.close) - 8}
              width={56}
              height={16}
              rx={2}
              fill={last.close >= last.open ? UP : DOWN}
            />
            <text
              x={PAD.left + geom.plotW + 30}
              y={geom.y(last.close) + 3.5}
              fontSize={10}
              textAnchor="middle"
              fill="#ffffff"
              fontWeight={600}
            >
              {priceLabel(last.close)}
            </text>
          </g>
        )}

        {/* x-axis: real dates when timestamps are distinct, bar sequence otherwise */}
        {Array.from({ length: Math.min(6, geom.n) }, (_, k) => {
          const i = Math.round((k * (geom.n - 1)) / Math.max(1, Math.min(6, geom.n) - 1));
          return (
            <text
              key={`x-${k}`}
              x={geom.cx(i)}
              y={height - 8}
              fontSize={10}
              textAnchor="middle"
              fill="hsl(var(--muted-foreground))"
            >
              {axisLabel(i)}
            </text>
          );
        })}
        <text x={PAD.left} y={geom.volTop - 2} fontSize={9} fill="hsl(var(--muted-foreground))">
          VOL
        </text>

        {/* crosshair */}
        {active && hover !== null && (
          <g pointerEvents="none">
            <line
              x1={geom.cx(hover)}
              x2={geom.cx(hover)}
              y1={PAD.top}
              y2={geom.volTop + geom.volH}
              stroke="hsl(var(--foreground))"
              strokeOpacity={0.45}
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <line
              x1={PAD.left}
              x2={PAD.left + geom.plotW}
              y1={geom.y(active.close)}
              y2={geom.y(active.close)}
              stroke="hsl(var(--foreground))"
              strokeOpacity={0.3}
              strokeWidth={1}
              strokeDasharray="3 3"
            />
            <circle
              cx={geom.cx(hover)}
              cy={geom.y(active.close)}
              r={3}
              fill={active.close >= active.open ? UP : DOWN}
            />
          </g>
        )}
      </svg>

      {active && (
        <div
          className="pointer-events-none absolute top-3 z-10 w-[200px] rounded-md border p-2.5 text-[11px] shadow-md"
          style={{
            left: tooltipLeft,
            backgroundColor: 'hsl(var(--popover))',
            color: 'hsl(var(--popover-foreground))',
            borderColor: 'hsl(var(--border))',
          }}
        >
          <div className="mb-1.5 font-semibold">Bar #{hover! + 1} · {symbol}</div>
          <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
            <span className="opacity-70">Open</span><span className="text-right tabular-nums">{priceLabel(active.open)}</span>
            <span className="opacity-70">High</span><span className="text-right tabular-nums">{priceLabel(active.high)}</span>
            <span className="opacity-70">Low</span><span className="text-right tabular-nums">{priceLabel(active.low)}</span>
            <span className="opacity-70">Close</span><span className="text-right tabular-nums font-semibold">{priceLabel(active.close)}</span>
            <span className="opacity-70">Volume</span><span className="text-right tabular-nums">{volumeLabel(active.volume)}</span>
          </div>
          <div className="mt-1.5 border-t pt-1.5 text-[10px] opacity-70" style={{ borderColor: 'hsl(var(--border))' }}>
            {timeLabel(active.timestamp)}
          </div>
        </div>
      )}
    </div>
  );
}
