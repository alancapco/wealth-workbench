// Compact mobile client card for list view
// Authority: U-014, REMEDIATION_02_Product_Design.md §7 P-004

import Link from 'next/link';

interface Client {
  id: string;
  name: string;
  identifier: string;
  book: string;
  dataState: 'AVAILABLE' | 'STALE' | 'UNAVAILABLE';
  lastContact?: string;
}

interface MobileClientCardProps {
  client: Client;
}

export default function MobileClientCard({ client }: MobileClientCardProps) {
  const stateColors = {
    AVAILABLE: 'bg-green-100 text-green-800',
    STALE: 'bg-yellow-100 text-yellow-800',
    UNAVAILABLE: 'bg-red-100 text-red-800',
  };

  const stateLabels = {
    AVAILABLE: 'Current',
    STALE: 'Stale',
    UNAVAILABLE: 'Unavailable',
  };

  return (
    <Link href={`/clients/${client.id}`}>
      <div className="mobile-card hover:shadow-md transition-shadow cursor-pointer">
        {/* Client name and state */}
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-capco-black text-base flex-1">
            {client.name}
          </h3>
          <span
            className={`text-xs px-2 py-1 rounded-full ${stateColors[client.dataState]}`}
            aria-label={`Data state: ${stateLabels[client.dataState]}`}
          >
            {stateLabels[client.dataState]}
          </span>
        </div>

        {/* Client details */}
        <div className="space-y-1 text-sm text-capco-gray-600">
          <div className="flex items-center gap-2">
            <span className="font-medium">ID:</span>
            <span>{client.identifier}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium">Book:</span>
            <span>{client.book}</span>
          </div>
          {client.lastContact && (
            <div className="flex items-center gap-2">
              <span className="font-medium">Last contact:</span>
              <span>{client.lastContact}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
