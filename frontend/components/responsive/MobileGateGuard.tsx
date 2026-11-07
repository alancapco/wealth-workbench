// Mobile gate guard - checks DEC-08 gate for mobile access
// Authority: U-014, REMEDIATION_02_Product_Design.md DEC-08

import { ReactNode, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useIsMobile } from '@/lib/responsive';

interface MobileGateGuardProps {
  children: ReactNode;
}

interface GateStatus {
  enabled: boolean;
  message?: string;
}

export default function MobileGateGuard({ children }: MobileGateGuardProps) {
  const isMobile = useIsMobile();
  const [gateStatus, setGateStatus] = useState<GateStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Only check gate on mobile devices
    if (!isMobile) {
      setGateStatus({ enabled: true });
      setLoading(false);
      return;
    }

    const checkGate = async () => {
      try {
        setLoading(true);
        // API-071: GET /admin/config/gates/MOBILE_ENABLED
        const response = await apiClient.get<{ enabled: boolean; message?: string }>(
          '/admin/config/gates/MOBILE_ENABLED'
        );
        setGateStatus(response.data);
        setError(null);
      } catch (err: any) {
        // Gate not configured or disabled - block mobile access
        setGateStatus({ enabled: false });
        setError(err.message || 'Unable to verify mobile access');
      } finally {
        setLoading(false);
      }
    };

    checkGate();
  }, [isMobile]);

  // Desktop always allowed
  if (!isMobile) {
    return <>{children}</>;
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-capco-black mx-auto mb-4"></div>
          <p className="text-capco-gray-600">Checking mobile access...</p>
        </div>
      </div>
    );
  }

  // Gate disabled - show message
  if (!gateStatus?.enabled) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4 bg-capco-gray-50">
        <div className="mobile-card max-w-md text-center">
          <div className="text-5xl mb-4" role="img" aria-label="Mobile access restricted">
            🚫
          </div>
          <h1 className="text-xl font-semibold text-capco-black mb-2">
            Mobile Access Restricted
          </h1>
          <p className="text-capco-gray-700 mb-4">
            Mobile access requires enablement. Contact your administrator to enable mobile features.
          </p>
          {error && (
            <p className="text-sm text-capco-gray-600 bg-capco-gray-100 p-3 rounded">
              {error}
            </p>
          )}
          {gateStatus?.message && (
            <p className="text-sm text-capco-gray-600 mt-4">
              {gateStatus.message}
            </p>
          )}
        </div>
      </div>
    );
  }

  // Gate enabled - render children
  return <>{children}</>;
}
