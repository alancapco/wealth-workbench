'use client';

import React from 'react';

interface ClientContextHeaderProps {
  clientId: string;
  clientName: string;
  bookId?: string | null;
  aum?: string | null;
  riskLabel?: string | null;
  onContextChange?: () => void;
}

/**
 * Shared component for displaying current client context.
 * Shows client identity and scope with change handling.
 * Authority: Design P-005, Architecture AUTH-01
 */
export function ClientContextHeader({
  clientId,
  clientName,
  bookId,
  aum,
  riskLabel,
  onContextChange,
}: ClientContextHeaderProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{clientName}</h2>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
              <span>ID: {clientId}</span>
              {bookId && (
                <>
                  <span className="text-gray-400">•</span>
                  <span>Book: {bookId}</span>
                </>
              )}
              {aum && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="font-medium">AUM: {aum}</span>
                </>
              )}
              {riskLabel && (
                <>
                  <span className="text-gray-400">•</span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium uppercase">
                    {riskLabel}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        {onContextChange && (
          <button
            onClick={onContextChange}
            className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            aria-label="Change client context"
          >
            Change Client
          </button>
        )}
      </div>
    </div>
  );
}
