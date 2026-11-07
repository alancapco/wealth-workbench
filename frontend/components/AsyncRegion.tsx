'use client';

import React from 'react';
import type { Region, Availability, Completeness, CapabilityState } from '@/lib/contracts/common';

interface AsyncRegionProps<T> {
  region: Region<T> | null;
  loading?: boolean;
  children: (value: T) => React.ReactNode;
  loadingFallback?: React.ReactNode;
  emptyFallback?: React.ReactNode;
  errorFallback?: (error: string) => React.ReactNode;
  unavailableFallback?: React.ReactNode;
}

/**
 * Shared primitive for rendering data regions with capability states.
 * Handles loading, empty, error, unavailable, and stale states.
 * Authority: REMEDIATION_02_Product_Design.md P-020, Architecture §3.2
 */
export function AsyncRegion<T>({
  region,
  loading = false,
  children,
  loadingFallback,
  emptyFallback,
  errorFallback,
  unavailableFallback,
}: AsyncRegionProps<T>) {
  // Loading state
  if (loading || !region) {
    return (
      <div className="flex items-center justify-center py-8">
        {loadingFallback || (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
            <span className="text-sm text-gray-600">Loading...</span>
          </div>
        )}
      </div>
    );
  }

  // Capability unavailable or disabled
  if (
    region.capability_state === 'UNCONFIGURED' ||
    region.capability_state === 'UNAVAILABLE' ||
    region.capability_state === 'DISABLED'
  ) {
    return (
      <div className="py-8">
        {unavailableFallback || (
          <div className="bg-gray-50 border border-gray-300 rounded p-6 text-center">
            <div className="text-gray-700 font-medium mb-2">
              {region.capability_state === 'UNCONFIGURED' && 'Configuration Required'}
              {region.capability_state === 'UNAVAILABLE' && 'Temporarily Unavailable'}
              {region.capability_state === 'DISABLED' && 'Feature Disabled'}
            </div>
            <div className="text-sm text-gray-600">
              {region.capability_state === 'UNCONFIGURED' &&
                'This feature requires configuration before use.'}
              {region.capability_state === 'UNAVAILABLE' &&
                'This feature is currently unavailable. Please try again later.'}
              {region.capability_state === 'DISABLED' && 'This feature is currently disabled.'}
            </div>
            {region.error_code && (
              <div className="mt-2 text-xs text-gray-500">Error: {region.error_code}</div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Error state
  if (region.availability === 'UNAVAILABLE' && region.error_code) {
    return (
      <div className="py-8">
        {errorFallback ? (
          errorFallback(region.error_code)
        ) : (
          <div className="bg-red-50 border border-red-300 rounded p-6 text-center">
            <div className="text-red-700 font-medium mb-2">Unable to Load Data</div>
            <div className="text-sm text-red-600">
              An error occurred while loading this information.
            </div>
            <div className="mt-2 text-xs text-red-500">Error: {region.error_code}</div>
          </div>
        )}
      </div>
    );
  }

  // Empty state
  if (region.completeness === 'EMPTY') {
    return (
      <div className="py-8">
        {emptyFallback || (
          <div className="bg-gray-50 border border-gray-300 rounded p-6 text-center">
            <div className="text-gray-700 font-medium mb-2">No Data Available</div>
            <div className="text-sm text-gray-600">
              There is no data to display at this time.
            </div>
          </div>
        )}
      </div>
    );
  }

  // Conflict state
  if (region.availability === 'CONFLICT') {
    return (
      <div className="py-8">
        <div className="bg-yellow-50 border border-yellow-400 rounded p-6 text-center">
          <div className="text-yellow-800 font-medium mb-2">Data Conflict Detected</div>
          <div className="text-sm text-yellow-700">
            Multiple conflicting sources were found. Manual resolution required.
          </div>
        </div>
      </div>
    );
  }

  // Success: render children with optional stale indicator
  return (
    <div className="relative">
      {region.availability === 'STALE' && (
        <div className="mb-3 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-yellow-600"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm text-yellow-800 font-medium">
              Data may be outdated
              {region.as_of && ` (as of ${new Date(region.as_of).toLocaleString()})`}
            </span>
          </div>
        </div>
      )}
      {region.completeness === 'PARTIAL' && (
        <div className="mb-3 bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
          <div className="text-sm text-blue-800">
            <strong>Partial data:</strong> Some information is unavailable or incomplete.
          </div>
        </div>
      )}
      {children(region.value)}
    </div>
  );
}
