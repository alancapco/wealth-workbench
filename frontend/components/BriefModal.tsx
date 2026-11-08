'use client';

import React from 'react';
import { briefApi } from '@/lib/api';

function BriefSection({ title, section }: { title: string; section?: { content?: string; provenance?: { source?: string } } }) {
  return (
    <div className="border border-gray-200 rounded p-4">
      <h3 className="font-semibold text-lg mb-2 pb-2 border-b">{title}</h3>
      <p className="text-sm text-gray-700 whitespace-pre-wrap">
        {section?.content || 'No data returned for this section.'}
      </p>
      {section?.provenance?.source && (
        <div className="mt-3 text-xs text-gray-500">
          <span className="inline-block px-2 py-1 bg-gray-100 rounded">
            Source: {section.provenance.source}
          </span>
        </div>
      )}
    </div>
  );
}

interface BriefModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientId: string;
  clientName: string;
}

export default function BriefModal({ isOpen, onClose, clientId, clientName }: BriefModalProps) {
  const [loading, setLoading] = React.useState(true);
  const [brief, setBrief] = React.useState<any>(null);
  const [error, setError] = React.useState('');
  const [editing, setEditing] = React.useState(false);
  const [editedAgenda, setEditedAgenda] = React.useState('');
  const [loadedClientId, setLoadedClientId] = React.useState(clientId);
  const requestSeq = React.useRef(0);

  if (loadedClientId !== clientId) {
    requestSeq.current += 1;
    setLoadedClientId(clientId);
    setBrief(null);
    setError('');
    setLoading(true);
    setEditing(false);
    setEditedAgenda('');
  }

  React.useEffect(() => {
    if (isOpen) {
      loadBrief();
    }
  }, [isOpen, clientId]);

  const loadBrief = async () => {
    const seq = ++requestSeq.current;
    const requestedId = clientId;
    try {
      setLoading(true);
      setError('');
      const response = await briefApi.generate(requestedId);
      if (seq !== requestSeq.current) return;
      const briefData = response.data.brief;
      setBrief(briefData);
      setEditedAgenda(briefData.proposed_agenda?.content || '');
    } catch (err) {
      if (seq !== requestSeq.current) return;
      console.error('Error loading brief:', err);
      setBrief(null);
      setError('The brief could not be loaded from the client record.');
    } finally {
      if (seq === requestSeq.current) setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!brief?.id) {
      alert('Cannot approve: Brief ID not available');
      return;
    }
    try {
      await briefApi.approve(brief.id, 'Sarah Chen', editing ? editedAgenda : undefined);
      onClose();
      // Show success message or trigger next stage
      alert('Brief approved! Ready for meeting.');
    } catch (error) {
      console.error('Error approving brief:', error);
      alert('Failed to approve brief. Please try again.');
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
            ) : error ? (
              <div className="flex items-center justify-center h-64 text-sm text-gray-600">{error}</div>
            ) : (
              <div className="space-y-6">
                <BriefSection title="Portfolio Overview" section={brief?.portfolio_overview} />
                <BriefSection title="Material Changes" section={brief?.material_changes} />
                <BriefSection title="Recent Interactions" section={brief?.recent_interactions} />
                <BriefSection title="Market News" section={brief?.market_news} />

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
