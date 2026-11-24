/** Compact currency for cards and tables. */
export function money(n: unknown, currency = 'USD'): string {
  if (typeof n !== 'number' || !Number.isFinite(n)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 1,
    notation: 'compact',
  }).format(n);
}

export function pct(n: unknown): string {
  return typeof n === 'number' && Number.isFinite(n)
    ? `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
    : '—';
}
