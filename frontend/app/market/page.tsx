'use client';

import { FeaturePage, Grid } from '@/components/ui/LiveFeature';
import { QueryPanel, SectionLabel } from '@/components/ui/WorkbenchUI';
import HistoricalPricePanel from '@/components/HistoricalPricePanel';

export default function MarketPage() {
  return (
    <FeaturePage
      eyebrow="Portfolio & Market"
      title="Market Data"
      description="Quotes, news, signals, historical prices and provider mode — all read from the live market service, with real error states when a provider is unconfigured."
      wide
    >
      <Grid>
        <QueryPanel
          title="Quotes"
          subtitle="Current prices for the selected instruments"
          method="GET"
          path="/market/quotes"
          params={[{ name: 'symbols', label: 'Symbols (comma separated)', in: 'query', default: '0005.HK,00700.HK' }]}
          emptyTitle="No quotes returned"
          emptyDetail="Set ALPHAVANTAGE_API_KEY for live quotes, or check the symbols."
        />
        <QueryPanel
          title="Market news"
          subtitle="English headlines from Newsfilter, with Yahoo Finance as fallback"
          method="GET"
          path="/market/news"
          params={[
            { name: 'symbols', label: 'Symbols (comma separated, optional)', in: 'query', default: '' },
            { name: 'limit', label: 'Limit', in: 'query', type: 'number', default: '10' },
          ]}
          rowsOf={(d: any) => d?.news || []}
          emptyTitle="No news available"
          emptyDetail="The news source reports no items for this query."
        />
      </Grid>

      <Grid>
        <QueryPanel
          title="Quote snapshot"
          subtitle="Overall market picture right now"
          method="GET"
          path="/market/snapshot"
          emptyTitle="Snapshot unavailable"
        />
        <QueryPanel
          title="Market signals"
          subtitle="Signals for the selected instruments"
          method="GET"
          path="/market/signals"
          params={[{ name: 'symbols', label: 'Symbols (comma separated)', in: 'query', default: '0005.HK,00700.HK' }]}
          emptyTitle="No signals detected"
        />
      </Grid>

      <SectionLabel>History and provider controls</SectionLabel>
      {/* Full width: a candlestick + volume chart needs more room than a
          two-column grid cell. The panel auto-loads from /market/historical. */}
      <Grid cols={1}>
        <HistoricalPricePanel />
        <QueryPanel
          title="Set market mode"
          subtitle="Switch between live and replay data"
          method="POST"
          path="/market/mode"
          params={[
            { name: 'mode', label: 'Mode', in: 'query', type: 'select', default: 'replay', options: [
              { value: 'replay', label: 'Replay' }, { value: 'live', label: 'Live' },
            ] },
          ]}
          auto={false}
        />
      </Grid>
    </FeaturePage>
  );
}
