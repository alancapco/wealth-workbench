'use client';

import React, { useState } from 'react';

interface NewsItem {
  id: string;
  title: string;
  content?: string;
  timestamp?: string;
  source?: string;
  url?: string;
  symbol?: string;
  sentiment?: string; // BULLISH | BEARISH | NEUTRAL
}

interface MarketNewsPanelProps {
  news: NewsItem[];
  symbols?: string[];
  onRefresh?: () => void;
}

function relativeTime(timestamp?: string): string {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '';
  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return 'just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function SourceBadge({ source }: { source?: string }) {
  const s = (source || '').toLowerCase();
  if (s.includes('tiger')) {
    return (
      <span className="inline-block px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-medium rounded">
        Tiger Broker
      </span>
    );
  }
  if (s.includes('alpha') || s.includes('alphavantage')) {
    return (
      <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded">
        Alpha Vantage
      </span>
    );
  }
  return (
    <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded">
      {source || 'News'}
    </span>
  );
}

function SentimentBadge({ sentiment }: { sentiment?: string }) {
  if (!sentiment) return null;
  const s = sentiment.toUpperCase();
  if (s === 'BULLISH') {
    return (
      <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
        ↑ Bullish
      </span>
    );
  }
  if (s === 'BEARISH') {
    return (
      <span className="inline-block px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded">
        ↓ Bearish
      </span>
    );
  }
  return (
    <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded">
      Neutral
    </span>
  );
}

export default function MarketNewsPanel({ news, symbols, onRefresh }: MarketNewsPanelProps) {
  const [visibleCount, setVisibleCount] = useState(5);

  const visible = news.slice(0, visibleCount);
  const canLoadMore = visibleCount < Math.min(news.length, 20);

  return (
    <div className="bg-white border border-gray-200 rounded p-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Market News</h2>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-xs text-gray-500 hover:text-black border border-gray-200 px-2 py-1 rounded hover:border-gray-400 transition-colors"
          >
            Refresh
          </button>
        )}
      </div>

      {news.length === 0 ? (
        <div className="py-8 text-center">
          <div className="text-sm text-gray-500 mb-2">No news available</div>
          <div className="text-xs text-gray-400">Powered by Tiger Broker · Alpha Vantage</div>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {visible.map((item) => (
              <div key={item.id || item.url || item.title} className="pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                <div className="font-semibold text-sm mb-1 leading-snug">
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:underline"
                    >
                      {item.title}
                    </a>
                  ) : (
                    item.title
                  )}
                </div>

                {item.content && (
                  <div className="text-xs text-gray-500 mb-2 leading-relaxed">
                    {item.content.length > 120
                      ? item.content.slice(0, 120) + '…'
                      : item.content}
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                  <SourceBadge source={item.source} />
                  <SentimentBadge sentiment={item.sentiment} />
                  {item.symbol && (
                    <span className="inline-block px-2 py-0.5 bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded font-mono">
                      {item.symbol}
                    </span>
                  )}
                  {item.timestamp && (
                    <span className="text-xs text-gray-400">{relativeTime(item.timestamp)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {canLoadMore && (
            <button
              onClick={() => setVisibleCount((c) => Math.min(c + 5, 20))}
              className="mt-4 w-full text-xs text-gray-500 hover:text-black py-1.5 border border-gray-200 rounded hover:border-gray-400 transition-colors"
            >
              Load more
            </button>
          )}
        </>
      )}
    </div>
  );
}
