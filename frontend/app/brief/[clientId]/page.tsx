'use client';

import { useRouter } from 'next/navigation';
import React, { useEffect, useState } from 'react';
import CanonicalBriefView from '@/components/CanonicalBriefView';

export default function BriefPage({ params }: { params: { clientId: string } }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [brief, setBrief] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBrief();
  }, [params.clientId]);

  const loadBrief = async () => {
    try {
      setLoading(true);
      setError(null);
      // Real implementation would call GET /briefs/{brief_id}
      // For now, demonstrate contract structure with fixture data
      setBrief({
        brief_id: '00000000-0000-0000-0000-000000000001',
        client_id: params.clientId,
        version: 1,
        generated_at: new Date().toISOString(),
        generated_by: 'fixture-user-001',
        environment: { kind: 'FIXTURE', id: 'test-env-001' },
        sections: {
          portfolio_overview: {
            key: 'portfolio_overview',
            item_hash: '0'.repeat(64),
            narrative: null,
            claims: [],
            agenda: [],
            availability: 'UNAVAILABLE',
            completeness: 'EMPTY',
            capability_state: 'UNCONFIGURED',
            review_state: 'UNREVIEWED',
            sources: [
              {
                id: '00000000-0000-0000-0000-000000000010',
                environment: { kind: 'FIXTURE', id: 'test-env-001' },
                availability: 'UNAVAILABLE',
                origin: 'RECORDED',
                live_response: false,
                limitation_codes: ['PROVIDER_UNCONFIGURED'],
              },
            ],
            limitations: ['Context provider not configured - demonstrating contract structure'],
          },
          material_changes: {
            key: 'material_changes',
            item_hash: '0'.repeat(64),
            narrative: null,
            claims: [],
            agenda: [],
            availability: 'UNAVAILABLE',
            completeness: 'EMPTY',
            capability_state: 'UNCONFIGURED',
            review_state: 'UNREVIEWED',
            sources: [
              {
                id: '00000000-0000-0000-0000-000000000011',
                environment: { kind: 'FIXTURE', id: 'test-env-001' },
                availability: 'UNAVAILABLE',
                origin: 'RECORDED',
                live_response: false,
                limitation_codes: ['PROVIDER_UNCONFIGURED'],
              },
            ],
            limitations: ['Context provider not configured - demonstrating contract structure'],
          },
          recent_interactions: {
            key: 'recent_interactions',
            item_hash: '0'.repeat(64),
            narrative: null,
            claims: [],
            agenda: [],
            availability: 'UNAVAILABLE',
            completeness: 'EMPTY',
            capability_state: 'UNCONFIGURED',
            review_state: 'UNREVIEWED',
            sources: [
              {
                id: '00000000-0000-0000-0000-000000000012',
                environment: { kind: 'FIXTURE', id: 'test-env-001' },
                availability: 'UNAVAILABLE',
                origin: 'RECORDED',
                live_response: false,
                limitation_codes: ['PROVIDER_UNCONFIGURED'],
              },
            ],
            limitations: ['Context provider not configured - demonstrating contract structure'],
          },
          market_news: {
            key: 'market_news',
            item_hash: '0'.repeat(64),
            narrative: null,
            claims: [],
            agenda: [],
            availability: 'UNAVAILABLE',
            completeness: 'EMPTY',
            capability_state: 'UNCONFIGURED',
            review_state: 'UNREVIEWED',
            sources: [
              {
                id: '00000000-0000-0000-0000-000000000013',
                environment: { kind: 'FIXTURE', id: 'test-env-001' },
                availability: 'UNAVAILABLE',
                origin: 'RECORDED',
                live_response: false,
                limitation_codes: ['PROVIDER_UNCONFIGURED'],
              },
            ],
            limitations: ['Context provider not configured - demonstrating contract structure'],
          },
          proposed_agenda: {
            key: 'proposed_agenda',
            item_hash: '0'.repeat(64),
            narrative: null,
            claims: [],
            agenda: [],
            availability: 'UNAVAILABLE',
            completeness: 'EMPTY',
            capability_state: 'UNCONFIGURED',
            review_state: 'UNREVIEWED',
            sources: [
              {
                id: '00000000-0000-0000-0000-000000000014',
                environment: { kind: 'FIXTURE', id: 'test-env-001' },
                availability: 'UNAVAILABLE',
                origin: 'RECORDED',
                live_response: false,
                limitation_codes: ['PROVIDER_UNCONFIGURED'],
              },
            ],
            limitations: ['Context provider not configured - demonstrating contract structure'],
          },
        },
        blockers: [],
      });
    } catch (error) {
      console.error('Error loading brief:', error);
      setError('Failed to load brief');
    } finally {
      setLoading(false);
    }
  };

  const handleSectionReview = async (
    sectionKey: string,
    hash: string,
    decision: 'APPROVED' | 'REJECTED'
  ) => {
    try {
      // Real implementation would call POST /briefs/{brief_id}/reviews
      console.log(`Review section ${sectionKey}: ${decision}`);
      alert(`Section ${sectionKey} ${decision.toLowerCase()}`);
    } catch (error) {
      console.error('Error reviewing section:', error);
      alert('Failed to review section');
    }
  };

  const handleSectionEdit = (sectionKey: string) => {
    // Real implementation would open edit modal
    console.log(`Edit section ${sectionKey}`);
    alert(`Edit ${sectionKey} not yet implemented`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading brief...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-black z-50">
        <div className="max-w-[1920px] mx-auto h-full px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => router.push('/')} className="text-white hover:text-gray-300">
              ← Back to Dashboard
            </button>
          </div>
          <div className="text-white font-semibold">Client Brief</div>
          <div className="text-white text-sm">RM User</div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16 pb-12 px-8 max-w-[1400px] mx-auto">
        <div className="pt-12">
          <h1 className="text-4xl font-light mb-4">Meeting Brief</h1>
          <p className="text-gray-600 mb-8">
            Review sections and approve before meeting
          </p>

          {/* Canonical Brief View */}
          {brief && (
            <CanonicalBriefView
              brief={brief}
              onSectionReview={handleSectionReview}
              onSectionEdit={handleSectionEdit}
              editable={true}
            />
          )}

          {/* Actions */}
          <div className="mt-8 flex gap-4">
            <button
              onClick={() => router.push('/')}
              className="px-8 py-3 bg-black text-white text-sm uppercase font-medium rounded hover:bg-gray-800"
            >
              Continue
            </button>
            <button
              onClick={() => router.push('/')}
              className="px-8 py-3 border border-gray-300 text-gray-700 text-sm uppercase font-medium rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
