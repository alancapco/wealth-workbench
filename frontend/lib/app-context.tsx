'use client';

/**
 * Live application context.
 *
 * All selectors are populated from real API responses and shared across pages,
 * so a client chosen in the header is the same client used by every feature
 * screen. Nothing here is a fixture: if an API call fails the selector is empty
 * and the page shows an error state.
 */
import React, {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { endpoints } from './endpoints';

export interface SessionInfo {
  subject: string;
  tenant_id: string;
  display_name: string;
  permissions: string[];
  books: { book_id: string; display_name: string }[];
  environment?: { kind: string; id: string };
  device_state?: string;
  session_expires_at?: string;
}

interface AppContextValue {
  ready: boolean;
  error: string | null;
  session: SessionInfo | null;
  tenantId: string;
  bookId: string;
  clients: any[];
  demoClients: any[];
  workflows: any[];
  clientId: string;
  demoClientId: string;
  workflowId: string;
  setClientId: (v: string) => void;
  setDemoClientId: (v: string) => void;
  setWorkflowId: (v: string) => void;
  setBookId: (v: string) => void;
  clientOptions: { value: string; label: string }[];
  demoClientOptions: { value: string; label: string }[];
  workflowOptions: { value: string; label: string }[];
  refresh: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

const KEYS = {
  client: 'wb.clientId',
  demoClient: 'wb.demoClientId',
  workflow: 'wb.workflowId',
  book: 'wb.bookId',
};

function stored(key: string): string {
  if (typeof window === 'undefined') return '';
  try {
    return window.localStorage.getItem(key) || '';
  } catch {
    return '';
  }
}

function persist(key: string, value: string) {
  if (typeof window === 'undefined') return;
  try {
    if (value) window.localStorage.setItem(key, value);
    else window.localStorage.removeItem(key);
  } catch {
    /* storage unavailable — selection stays in memory */
  }
}

function asArray(payload: any, ...keys: string[]): any[] {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== 'object') return [];
  for (const k of keys) if (Array.isArray(payload[k])) return payload[k];
  for (const v of Object.values(payload)) if (Array.isArray(v)) return v as any[];
  return [];
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [clients, setClients] = useState<any[]>([]);
  const [demoClients, setDemoClients] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [clientId, setClientIdState] = useState('');
  const [demoClientId, setDemoClientIdState] = useState('');
  const [workflowId, setWorkflowIdState] = useState('');
  const [bookId, setBookIdState] = useState('');
  const [tick, setTick] = useState(0);

  const setClientId = useCallback((v: string) => {
    setClientIdState(v);
    persist(KEYS.client, v);
  }, []);
  const setDemoClientId = useCallback((v: string) => {
    setDemoClientIdState(v);
    persist(KEYS.demoClient, v);
  }, []);
  const setWorkflowId = useCallback((v: string) => {
    setWorkflowIdState(v);
    persist(KEYS.workflow, v);
  }, []);
  const setBookId = useCallback((v: string) => {
    setBookIdState(v);
    persist(KEYS.book, v);
  }, []);
  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [sessionRes, clientsRes, demoRes] = await Promise.all([
          endpoints.session().catch(() => null),
          endpoints.clients.list().catch(() => null),
          endpoints.demoClients.list().catch(() => null),
        ]);
        if (cancelled) return;

        const s = (sessionRes?.data || null) as SessionInfo | null;
        setSession(s);
        const c = asArray(clientsRes?.data, 'clients');
        const d = asArray(demoRes?.data, 'clients');
        setClients(c);
        setDemoClients(d);

        const preferredBook =
          stored(KEYS.book) || s?.books?.[0]?.book_id || process.env.NEXT_PUBLIC_BOOK_ID || '';
        setBookIdState(preferredBook);

        const cStored = stored(KEYS.client);
        const dStored = stored(KEYS.demoClient);
        setClientIdState(c.find((x) => x.id === cStored) ? cStored : c[0]?.id || '');
        setDemoClientIdState(d.find((x) => x.id === dStored) ? dStored : d[0]?.id || '');

        if (!sessionRes && !clientsRes && !demoRes) {
          setError('Backend unavailable. Start the API server to load live data.');
        } else {
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Unable to load application context');
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tick]);

  // Workflows depend on the selected book, so they load in a second pass.
  useEffect(() => {
    if (!bookId) {
      setWorkflows([]);
      return;
    }
    let cancelled = false;
    endpoints.workflows
      .list(bookId)
      .then((res) => {
        if (cancelled) return;
        const list = asArray(res.data, 'items', 'workflows');
        setWorkflows(list);
        const storedId = stored(KEYS.workflow);
        setWorkflowIdState(list.find((x) => x.id === storedId) ? storedId : list[0]?.id || '');
      })
      .catch(() => {
        if (!cancelled) setWorkflows([]);
      });
    return () => {
      cancelled = true;
    };
  }, [bookId, tick]);

  const value = useMemo<AppContextValue>(
    () => ({
      ready,
      error,
      session,
      tenantId: session?.tenant_id || process.env.NEXT_PUBLIC_TENANT_ID || '',
      bookId,
      clients,
      demoClients,
      workflows,
      clientId,
      demoClientId,
      workflowId,
      setClientId,
      setDemoClientId,
      setWorkflowId,
      setBookId,
      clientOptions: clients.map((c) => ({
        value: c.id,
        label: c.name || 'Unnamed client',
      })),
      demoClientOptions: demoClients.map((c) => ({
        value: c.id,
        label: c.name || `${c.firstname || ''} ${c.lastname || ''}`.trim() || 'Unnamed client',
      })),
      workflowOptions: workflows.map((w) => {
        const typeLabel = (w.type || 'Workflow').replace(/_/g, ' ');
        const clientLabel = clients.find((c) => c.id === w.client_id)?.name;
        const stage = w.current_stage ? String(w.current_stage).replace(/_/g, ' ') : '';
        return {
          value: w.id,
          label: [typeLabel, clientLabel, stage].filter(Boolean).join(' · '),
        };
      }),
      refresh,
    }),
    [
      ready, error, session, bookId, clients, demoClients, workflows,
      clientId, demoClientId, workflowId, setClientId, setDemoClientId,
      setWorkflowId, setBookId, refresh,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
