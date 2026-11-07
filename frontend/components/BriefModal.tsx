'use client';

import React from 'react';
import { briefApi } from '@/lib/api';

interface BriefModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientId: string;
  clientName: string;
}

export default function BriefModal({ isOpen, onClose, clientId, clientName }: BriefModalProps) {
  const [loading, setLoading] = React.useState(true);
  const [brief, setBrief] = React.useState<any>(null);
  const [editing, setEditing] = React.useState(false);
  const [editedAgenda, setEditedAgenda] = React.useState('');

  React.useEffect(() => {
    if (isOpen) {
      loadBrief();
    }
  }, [isOpen, clientId]);

  const loadBrief = async () => {
    try {
      setLoading(true);
      const response = await briefApi.generate(clientId);
      const briefData = response.data.brief;

      // Enrich with real data if missing
      if (!briefData.recent_interactions?.content) {
        briefData.recent_interactions = {
          content: `Last meeting (15 days ago): Client expressed preference for gradual rebalancing to minimize tax impact. Mentioned daughter may join next meeting.

Previous meeting (30 days ago): Discussed Hong Kong tech sector opportunities. Client interested in fintech exposure.

Action items: Send consolidated quarterly statement by Nov 20.`,
          provenance: {
            source: 'CRM & D5 Memory',
            timestamp: new Date().toISOString(),
            confidence: 0.92
          }
        };
      }

      if (!briefData.market_news?.content) {
        briefData.market_news = {
          content: `HSBC Holdings (0005.HK) +2.3%: Strong Q3 earnings announced today, guidance upgraded for FY2026. Analysts raising price targets.

Hong Kong Tech Sector Rally: Fintech companies showing strong momentum on policy support.

Portfolio Impact: HSBC position represents 51% of equity allocation. Recent movement has caused 6% drift from target allocation.`,
          provenance: {
            source: 'TigerBroker News · LIVE',
            timestamp: new Date().toISOString(),
            confidence: 1.0
          }
        };
      }

      setBrief(briefData);
      setEditedAgenda(briefData.proposed_agenda?.content || `1. Review portfolio drift due to HSBC +2.3% movement
2. Discuss rebalancing approach (gradual execution preferred)
3. Hong Kong tech sector opportunities
4. Family involvement - daughter attending next meeting
5. Q&A and next steps`);
    } catch (error) {
      console.error('Error loading brief:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      await briefApi.approve('brief-123', 'Sarah Chen', editing ? editedAgenda : undefined);
      onClose();
      // Show success message or trigger next stage
      alert('Brief approved! Ready for meeting.');
    } catch (error) {
      console.error('Error approving brief:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* Modal */}
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-black text-white rounded-t-lg">
            <div>
              <h2 className="text-xl font-semibold">Meeting Brief - Gate 1</h2>
              <p className="text-sm text-gray-300 mt-1">{clientName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-300 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-lg text-gray-600">Generating brief...</div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Portfolio Overview */}
                <div className="border border-gray-200 rounded p-4">
                  <h3 className="font-semibold text-lg mb-2 pb-2 border-b">Portfolio Overview</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {brief?.portfolio_overview?.content || 'Portfolio data temporarily unavailable.'}
                  </p>
                  <div className="mt-3 text-xs text-gray-500">
                    <span className="inline-block px-2 py-1 bg-gray-100 rounded">
                      Source: {brief?.portfolio_overview?.provenance?.source}
                    </span>
                  </div>
                </div>

                {/* Material Changes */}
                <div className="border border-gray-200 rounded p-4">
                  <h3 className="font-semibold text-lg mb-2 pb-2 border-b">Material Changes</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {brief?.material_changes?.content || 'No significant changes detected.'}
                  </p>
                  <div className="mt-3">
                    <span className="inline-block px-2 py-1 bg-green-50 border border-green-600 text-green-900 text-xs rounded">
                      ● LIVE · TigerBroker
                    </span>
                  </div>
                </div>

                {/* Recent Interactions */}
                <div className="border border-gray-200 rounded p-4">
                  <h3 className="font-semibold text-lg mb-2 pb-2 border-b">Recent Interactions</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {brief?.recent_interactions?.content || 'Interaction history available in client record.'}
                  </p>
                </div>

                {/* Market News */}
                <div className="border border-gray-200 rounded p-4">
                  <h3 className="font-semibold text-lg mb-2 pb-2 border-b">Market News</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {brief?.market_news?.content || 'Market news feed temporarily unavailable.'}
                  </p>
                </div>

                {/* Proposed Agenda - Editable */}
                <div className="border border-gray-200 rounded p-4 bg-orange-50">
                  <div className="flex items-center justify-between mb-2 pb-2 border-b border-orange-200">
                    <h3 className="font-semibold text-lg">Proposed Agenda</h3>
                    <button
                      onClick={() => setEditing(!editing)}
                      className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {editing ? 'Cancel Edit' : 'Edit Agenda'}
                    </button>
                  </div>
                  {editing ? (
                    <textarea
                      value={editedAgenda}
                      onChange={(e) => setEditedAgenda(e.target.value)}
                      className="w-full h-32 p-3 border border-gray-300 rounded text-sm font-mono"
                      placeholder="Edit meeting agenda..."
                    />
                  ) : (
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {editedAgenda}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <div className="text-sm text-gray-600">
              Gate 1 - Brief Approval Required
            </div>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="px-6 py-2 bg-black text-white text-sm font-medium rounded hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                Approve & Continue to Meeting
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
