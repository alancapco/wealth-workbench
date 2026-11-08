// Provides fixture session context for development.
// In production, this would read from the real /session endpoint.

export interface SessionContext {
  tenant_id: string;
  book_id: string;
  principal_id: string;
}

// Default fixture values — override via env vars
export const DEFAULT_SESSION: SessionContext = {
  tenant_id: process.env.NEXT_PUBLIC_TENANT_ID || 'tenant-fixture-001',
  book_id: process.env.NEXT_PUBLIC_BOOK_ID || 'book-fixture-001',
  principal_id: process.env.NEXT_PUBLIC_PRINCIPAL_ID || 'principal-fixture-001',
};
