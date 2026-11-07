// Canonical API envelope and error contracts
// Authority: REMEDIATION_03_Architecture_Contracts.md §5

// Success envelope for all API responses
export interface Envelope<T> {
  data: T;
  meta: {
    request_id: string;
    served_at: string; // RFC3339 UTC timestamp
    next_cursor: string | null;
  };
}

// Error response structure
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    fields: FieldError[];
    retryable: boolean;
    status_url: string | null;
  };
  meta: {
    request_id: string;
    served_at: string;
    next_cursor: null;
  };
}

export interface FieldError {
  path: string;
  code: string;
  message: string;
}

// Common error codes
export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  FORBIDDEN = 'FORBIDDEN',
  NOT_FOUND = 'NOT_FOUND',
  REQUEST_IN_PROGRESS = 'REQUEST_IN_PROGRESS',
  IDEMPOTENCY_CONFLICT = 'IDEMPOTENCY_CONFLICT',
  INVALID_TRANSITION = 'INVALID_TRANSITION',
  APPROVAL_INVALIDATED = 'APPROVAL_INVALIDATED',
  CONTEXT_CHANGED = 'CONTEXT_CHANGED',
  CONFIG_UNCONFIGURED = 'CONFIG_UNCONFIGURED',
  FEATURE_DISABLED = 'FEATURE_DISABLED',
  SOURCE_CONFLICT = 'SOURCE_CONFLICT',
  VERSION_MISMATCH = 'VERSION_MISMATCH',
  POLICY_BLOCKED = 'POLICY_BLOCKED',
  RATE_LIMITED = 'RATE_LIMITED',
  DEPENDENCY_UNAVAILABLE = 'DEPENDENCY_UNAVAILABLE',
  NOT_READY = 'NOT_READY',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
}

// Availability states
export type Availability = 'AVAILABLE' | 'STALE' | 'UNAVAILABLE' | 'CONFLICT';
export type Completeness = 'COMPLETE' | 'PARTIAL' | 'EMPTY';
export type CapabilityState = 'READY' | 'UNCONFIGURED' | 'UNAVAILABLE' | 'DISABLED';

// Region wrapper for data with source/capability metadata
export interface Region<T> {
  availability: Availability;
  completeness: Completeness;
  capability_state: CapabilityState;
  as_of: string | null;
  value: T;
  sources: Source[];
  error_code: string | null;
}

// Source provenance
export type Origin = 'RECORDED' | 'DERIVED' | 'RM_ENTERED';
export type EnvironmentKind = 'FIXTURE' | 'INSTITUTION_TEST' | 'PRODUCTION';

export interface Environment {
  kind: EnvironmentKind;
  id: string;
}

export interface Source {
  id: string;
  environment: Environment;
  availability: Availability;
  origin: Origin;
  system_key: string | null;
  record_id: string | null;
  record_version: string | null;
  as_of: string | null;
  retrieved_at: string | null;
  authoritative_owner: string | null;
  freshness_policy_ref: ConfigRef | null;
  live_response: boolean;
  adapter_receipt_id: string | null;
  confidence: string | null; // Decimal as string
  evidence: EvidenceLocation | null;
  limitation_codes: string[];
}

export interface EvidenceLocation {
  kind: 'RECORD' | 'TRANSCRIPT' | 'DOCUMENT' | 'RM_ENTRY';
  record_uri: string | null;
  segment_id: string | null;
  document_ref: string | null;
  page: number | null;
  excerpt: string | null;
  entered_by: string | null;
}

export interface ConfigRef {
  id: string;
  revision: number;
  hash: string;
}

export interface Blocker {
  code: string;
  field: string | null;
  config_ref: ConfigRef | null;
  resolution: 'SAFE_RETRY' | 'EDIT' | 'REVIEW' | 'ADMIN' | 'CHECK_STATUS' | 'NONE';
}

// Capability check result
export interface Capability {
  key: string;
  state: CapabilityState;
  blockers: Blocker[];
}
