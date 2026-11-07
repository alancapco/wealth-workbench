'use client';

import React from 'react';
import type { Blocker } from '@/lib/contracts/common';

interface PolicyCheckPanelProps {
  blockers: Blocker[];
  context: string;
  onResolve?: (blocker: Blocker) => void;
}

/**
 * Shared component for displaying policy/capability blockers.
 * Shows blockers with resolution guidance and safe retry actions.
 * Authority: Architecture §5 common errors, Design P-020
 */
export function PolicyCheckPanel({ blockers, context, onResolve }: PolicyCheckPanelProps) {
  if (blockers.length === 0) {
    return null;
  }

  const getBlockerSeverity = (resolution: Blocker['resolution']) => {
    switch (resolution) {
      case 'NONE':
        return 'error';
      case 'ADMIN':
      case 'REVIEW':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getResolutionText = (resolution: Blocker['resolution']) => {
    switch (resolution) {
      case 'SAFE_RETRY':
        return 'You can retry this action';
      case 'EDIT':
        return 'Edit required before proceeding';
      case 'REVIEW':
        return 'Review and approval required';
      case 'ADMIN':
        return 'Administrative action required';
      case 'CHECK_STATUS':
        return 'Check status before retrying';
      case 'NONE':
        return 'Cannot proceed';
      default:
        return 'Action required';
    }
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border-red-400 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-400 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-400 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-400 text-gray-800';
    }
  };

  return (
    <div className="space-y-3">
      <div className="text-sm font-semibold text-gray-700">
        Cannot proceed with {context}:
      </div>
      {blockers.map((blocker, index) => {
        const severity = getBlockerSeverity(blocker.resolution);
        const styles = getSeverityStyles(severity);

        return (
          <div
            key={index}
            className={`border-l-4 p-4 rounded ${styles}`}
            role="alert"
            aria-live="polite"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="font-medium mb-1">
                  {blocker.code.replace(/_/g, ' ')}
                  {blocker.field && ` (${blocker.field})`}
                </div>
                <div className="text-sm opacity-90">{getResolutionText(blocker.resolution)}</div>
                {blocker.config_ref && (
                  <div className="text-xs mt-2 opacity-75">
                    Policy: {blocker.config_ref.id} (rev {blocker.config_ref.revision})
                  </div>
                )}
              </div>
              {onResolve && blocker.resolution !== 'NONE' && (
                <button
                  onClick={() => onResolve(blocker)}
                  className="px-3 py-1 text-sm font-medium rounded border border-current hover:bg-black hover:bg-opacity-10 transition-colors"
                  aria-label={`Resolve ${blocker.code}`}
                >
                  {blocker.resolution === 'SAFE_RETRY' ? 'Retry' : 'Resolve'}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
