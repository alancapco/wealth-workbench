'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import CanonicalBriefView from '@/components/CanonicalBriefView';

export default function BriefPage({ params }: { params: { clientId: string } }) {
  const router = useRouter();
  const [brief, setBrief] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBrief() {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get(`/briefs?client_id=${params.clientId}`);
        const briefsData = response.data as { briefs?: any[], items?: any[] } | any[];
        const briefs = Array.isArray(briefsData) ? briefsData : (briefsData.briefs || briefsData.items || []);
        setBrief(briefs.length > 0 ? briefs[0] : null);
      } catch (err: any) {
        setError(err?.message || 'Failed to load brief');
      } finally {
        setLoading(false);
      }
    }
    fetchBrief();
  }, [params.clientId]);

  const handleSectionReview = async (
    sectionKey: string,
    hash: string,
    decision: 'APPROVED' | 'REJECTED'
  ) => {
    try {
      console.log(`Review section ${sectionKey}: ${decision}`);
      alert(`Section ${sectionKey} ${decision.toLowerCase()}`);
    } catch (error) {
      console.error('Error reviewing section:', error);
      alert('Failed to review section');
    }
  };

  const handleSectionEdit = (sectionKey: string) => {
    console.log(`Edit section ${sectionKey}`);
    alert(`Edit ${sectionKey} not yet implemented`);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
          <Link href="/clients" className="text-gray-700 hover:text-black mt-2 inline-block">
            ← Back to Clients
          </Link>
        </div>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="p-6">
        <div className="mb-4">
          <Link href="/clients" className="text-gray-700 hover:text-black">
            ← Back to Clients
          </Link>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-500 mb-4">No brief generated yet for this client.</p>
          <button
            onClick={() => apiClient.post('/briefs', { client_id: params.clientId })}
            className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800"
          >
            Generate Brief
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* In-page header strip (no fixed positioning — sidebar layout handles nav) */}
      <div className="h-16 bg-black w-full">
        <div className="max-w-[1920px] mx-auto h-full px-8 flex items-center justify-between">
          <button onClick={() => router.push('/clients')} className="text-white hover:text-gray-300">
            ← Back to Clients
          </button>
          <div className="text-white font-semibold">Client Brief</div>
          <div className="text-white text-sm">RM User</div>
        </div>
      </div>

      {/* Main Content */}
      <main className="pb-12 px-8 max-w-[1400px] mx-auto">
        <div className="pt-8">
          <h1 className="text-4xl font-light mb-4">Meeting Brief</h1>
          <p className="text-gray-600 mb-8">Review sections and approve before meeting</p>

          <CanonicalBriefView
            brief={brief}
            onSectionReview={handleSectionReview}
            onSectionEdit={handleSectionEdit}
            editable={true}
          />

          <div className="mt-8 flex gap-4">
            <button
              onClick={() => router.push('/clients')}
              className="px-8 py-3 bg-black text-white text-sm uppercase font-medium rounded hover:bg-gray-800"
            >
              Continue
            </button>
            <button
              onClick={() => router.push('/clients')}
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
