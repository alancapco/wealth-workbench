/**
 * Canonical Brief View Component - Single source of truth for brief rendering.
 * 
 * Used by all brief entry points (full page, modal, mobile). Consumes frozen
 * contract response.data.brief.sections with exact 5 keys.
 * 
 * Per Architecture §6.3: Never fabricates data, shows truthful source states.
 * Authority: U-014 - Responsive support integrated
 */
'use client';

import React from 'react';
import { useBreakpoint } from '@/lib/responsive';
import MobileBriefView from '@/components/responsive/MobileBriefView';

interface Source {
  id: string;
  environment: { kind: string; id: string };
  availability: string;
  origin: string;
  live_response: boolean;
  as_of?: string;
  retrieved_at?: string;
  limitation_codes: string[];
  authoritative_owner?: string;
  system_key?: string;
}

interface BriefClaim {
  id: string;
  text: string;
  origin: string;
  evidence_refs: any[];
  confidence?: number;
}

interface AgendaItem {
  id: string;
  text: string;
  origin: string;
  evidence_refs: any[];
}

interface BriefSection {
  key: string;
  item_hash: string;
  narrative?: string;
  claims: BriefClaim[];
  agenda: AgendaItem[];
  availability: string;
  completeness: string;
  capability_state: string;
  review_state: string;
  sources: Source[];
  limitations: string[];
}

interface Brief {
  brief_id: string;
  client_id: string;
  version: number;
  generated_at: string;
  generated_by: string;
  sections: {
    portfolio_overview: BriefSection;
    material_changes: BriefSection;
    recent_interactions: BriefSection;
    market_news: BriefSection;
    proposed_agenda: BriefSection;
  };
  environment: { kind: string; id: string };
  blockers: any[];
}

interface CanonicalBriefViewProps {
  brief: Brief;
  onSectionReview?: (sectionKey: string, hash: string, decision: 'APPROVED' | 'REJECTED') => void;
  onSectionEdit?: (sectionKey: string) => void;
  editable?: boolean;
}

const sectionTitles: Record<string, string> = {
  portfolio_overview: 'Portfolio Overview',
  material_changes: 'Material Changes',
  recent_interactions: 'Recent Interactions',
  market_news: 'Market News',
  proposed_agenda: 'Proposed Agenda',
};

export default function CanonicalBriefView({
  brief,
  onSectionReview,
  onSectionEdit,
  editable = false,
}: CanonicalBriefViewProps) {
  const breakpoint = useBreakpoint();
  const sectionKeys = [
    'portfolio_overview',
    'material_changes',
    'recent_interactions',
    'market_news',
    'proposed_agenda',
  ] as const;

  // Use mobile view on mobile breakpoint
  if (breakpoint === 'mobile') {
    const mobileBrief = {
      id: brief.brief_id,
      clientName: (brief as any).client_name || 'Client',
      version: brief.version.toString(),
      sections: sectionKeys.map(key => {
        const section = brief.sections[key];
        return {
          key,
          title: sectionTitles[key],
          content: section.narrative || section.claims.map(c => c.text).join('\n') || 'No data available',
          state: section.availability as 'AVAILABLE' | 'STALE' | 'UNAVAILABLE',
          sources: section.sources.map(s => ({
            id: s.id,
            origin: s.origin,
            as_of: s.as_of || null,
          })),
        };
      }),
    };

    return (
      <MobileBriefView 
        brief={mobileBrief}
        onSectionReview={onSectionReview ? (sectionKey: string) => {
          const section = brief.sections[sectionKey as keyof typeof brief.sections];
          if (section) {
            onSectionReview(sectionKey, section.item_hash, 'APPROVED');
          }
        } : undefined}
      />
    );
  }

  const renderSection = (key: string) => {
    const section = brief.sections[key as keyof typeof brief.sections];
    if (!section) return null;

    const isUnavailable = section.capability_state === 'UNAVAILABLE' || section.capability_state === 'UNCONFIGURED';
    const isEmpty = section.completeness === 'EMPTY';
    const isStale = section.availability === 'STALE';

    return (
      <div key={key} className="bg-white border border-gray-200 rounded p-6">
        <div className="flex items-center justify-between mb-3 pb-3 border-b">
          <h2 className="text-xl font-semibold">{sectionTitles[key]}</h2>
          <div className="flex items-center gap-2">
            {/* Capability state badge */}
            {isUnavailable && (
              <span className="px-2 py-1 bg-gray-100 border border-gray-300 text-gray-700 text-xs rounded">
                {section.capability_state === 'UNCONFIGURED' ? 'Not configured' : 'Unavailable'}
              </span>
            )}
            {isStale && (
              <span className="px-2 py-1 bg-yellow-50 border border-yellow-600 text-yellow-900 text-xs rounded">
                Needs refresh
              </span>
            )}
            {section.sources.some(s => s.live_response) && (
              <span className="px-2 py-1 bg-green-50 border border-green-600 text-green-900 text-xs rounded">
                Live
              </span>
            )}
            {editable && onSectionEdit && (
              <button
                onClick={() => onSectionEdit(key)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Edit
              </button>
            )}
          </div>
        </div>

        <div className="prose max-w-none">
          {/* Narrative */}
          {section.narrative && (
            <p className="whitespace-pre-wrap">{section.narrative}</p>
          )}

          {/* Claims with evidence */}
          {section.claims.length > 0 && (
            <div className="mt-4 space-y-2">
              {section.claims.map((claim) => (
                <div key={claim.id} className="flex items-start gap-2">
                  <span className="text-gray-600">•</span>
                  <div className="flex-1">
                    <span>{claim.text}</span>
                    {claim.confidence !== undefined && (
                      <span className="ml-2 text-xs text-gray-500">
                        ({Math.round(claim.confidence * 100)}% confidence)
                      </span>
                    )}
                    {claim.origin && claim.origin !== 'RECORDED' && (
                      <span className="ml-2 text-xs text-gray-400">
                        {String(claim.origin).replace(/_/g, ' ').toLowerCase()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Agenda items */}
          {section.agenda.length > 0 && (
            <div className="mt-4 space-y-2">
              {section.agenda.map((item, idx) => (
                <div key={item.id} className="flex items-start gap-2">
                  <span className="text-gray-600">{idx + 1}.</span>
                  <span>{item.text}</span>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {isEmpty && !section.narrative && section.claims.length === 0 && (
            <p className="text-gray-500 italic">
              {isUnavailable ? 'Source not configured' : 'No data available'}
            </p>
          )}
        </div>

        {/* Limitations */}
        {section.limitations.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> {section.limitations.join('; ')}
            </p>
          </div>
        )}

        {/* Source provenance */}
        <div className="mt-4 pt-4 border-t text-xs text-gray-500 space-y-1">
          {section.sources.map((source) => {
            const label = source.authoritative_owner
              || source.system_key?.replace(/_/g, ' ')
              || (source.origin ? String(source.origin).replace(/_/g, ' ').toLowerCase() : 'Recorded data');
            return (
              <div key={source.id} className="flex items-center gap-2">
                <span>Source: {label}</span>
                {source.as_of && (
                  <span>• As of: {new Date(source.as_of).toLocaleString()}</span>
                )}
                {source.environment.kind === 'FIXTURE' && (
                  <span className="px-1 py-0.5 bg-orange-100 text-orange-800 rounded">
                    Demo data
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Review actions */}
        {onSectionReview && (
          <div className="mt-4 pt-4 border-t flex gap-2">
            <button
              onClick={() => onSectionReview(key, section.item_hash, 'APPROVED')}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              disabled={section.review_state === 'APPROVED'}
            >
              Approve Section
            </button>
            <button
              onClick={() => onSectionReview(key, section.item_hash, 'REJECTED')}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              disabled={section.review_state === 'REJECTED'}
            >
              Reject Section
            </button>
            {section.review_state !== 'UNREVIEWED' && (
              <span className="px-3 py-1 text-sm text-gray-600">
                Status: {section.review_state}
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Brief metadata */}
      <div className="bg-blue-50 border border-blue-200 rounded p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-blue-900">Brief v{brief.version}</h3>
            <p className="text-sm text-blue-700">
              Generated {new Date(brief.generated_at).toLocaleString()}
              {brief.generated_by && !/^[0-9a-f-]{16,}$/i.test(brief.generated_by)
                ? ` by ${brief.generated_by}`
                : ''}
            </p>
          </div>
          {brief.environment.kind === 'FIXTURE' && (
            <span className="px-3 py-1 bg-orange-100 border border-orange-600 text-orange-900 text-sm rounded">
              FIXTURE Environment
            </span>
          )}
        </div>
      </div>

      {/* All five sections */}
      {sectionKeys.map(renderSection)}

      {/* Blockers */}
      {brief.blockers.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <h3 className="font-semibold text-red-900 mb-2">Blockers</h3>
          <ul className="space-y-1">
            {brief.blockers.map((blocker: any, idx: number) => (
              <li key={idx} className="text-sm text-red-700">
                • {blocker.code}: {blocker.resolution}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
