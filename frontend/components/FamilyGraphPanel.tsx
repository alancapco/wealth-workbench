'use client';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type ChangeEvent,
} from 'react';
import { endpoints, ApiError, get, post } from '@/lib/endpoints';
import GraphView, {
  type GraphData,
  type GraphNode,
  type GraphLink,
  type GraphCategory,
} from '@/components/ui/GraphView';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from '@/components/ui/tooltip';

interface FamilyGraphPanelProps {
  clientId: string;
  title?: string;
  subtitle?: string;
}

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; error: unknown }
  | { status: 'success'; data: GraphData; raw: string };

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

function str(v: unknown, fallback = ''): string {
  return typeof v === 'string' ? v : fallback;
}

function coerceCategories(c: unknown): GraphCategory[] {
  if (!Array.isArray(c)) return [];
  return c.map((entry, i) => ({
    name: isRecord(entry) ? str(entry.name, `Category ${i}`) : str(entry, `Category ${i}`),
  }));
}

/** Normalise the live (envelope-unwrapped) payload into the GraphView shape. */
function coerceGraphData(raw: unknown): GraphData {
  const root = isRecord(raw) ? raw : {};
  const known = new Set<string>();
  const nodes: GraphNode[] = (Array.isArray(root.nodes) ? root.nodes : []).map((n, i) => {
    const r = isRecord(n) ? n : {};
    const id = str(r.id) || `node-${i}`;
    const uniqueId = known.has(id) ? `${id}-${i}` : id;
    known.add(uniqueId);
    return {
      id: uniqueId,
      name: str(r.name, uniqueId),
      symbolSize: typeof r.symbolSize === 'number' ? r.symbolSize : 40,
      category: typeof r.category === 'number' ? Math.trunc(r.category) : 0,
      label: { show: true },
      entitlement: typeof r.entitlement === 'string' ? r.entitlement : null,
      kind: typeof r.kind === 'string' ? r.kind : null,
      is_root: r.is_root === true,
    };
  });
  const links: GraphLink[] = (Array.isArray(root.links) ? root.links : []).map((l) => {
    const r = isRecord(l) ? l : {};
    return {
      source: str(r.source),
      target: str(r.target),
      relationship_type: str(r.relationship_type, 'RELATED'),
      value: typeof r.value === 'number' ? r.value : 1,
    };
  });
  return {
    nodes,
    links,
    categories: coerceCategories(root.categories),
    root_id: typeof root.root_id === 'string' ? root.root_id : null,
  };
}

/** Validate arbitrary pasted graph JSON. Never persists anything. */
function parseCustomGraph(text: string): { graph: GraphData | null; error: string | null } {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text) as unknown;
  } catch (e) {
    return {
      graph: null,
      error: `Invalid JSON: ${e instanceof Error ? e.message : 'could not parse'}`,
    };
  }
  if (!isRecord(parsed)) {
    return { graph: null, error: 'Top-level value must be a JSON object.' };
  }
  const nodesRaw = parsed.nodes;
  const linksRaw = parsed.links;
  if (!Array.isArray(nodesRaw)) return { graph: null, error: '"nodes" must be an array.' };
  if (!Array.isArray(linksRaw)) return { graph: null, error: '"links" must be an array.' };

  const ids = new Set<string>();
  const nodes: GraphNode[] = [];
  for (let i = 0; i < nodesRaw.length; i++) {
    const n = nodesRaw[i];
    if (!isRecord(n)) {
      return { graph: null, error: `nodes[${i}] must be an object with "id" and "name".` };
    }
    const id = str(n.id);
    if (!id) return { graph: null, error: `nodes[${i}] is missing an "id".` };
    if (ids.has(id)) return { graph: null, error: `Duplicate node id "${id}".` };
    ids.add(id);
    nodes.push({
      id,
      name: str(n.name, id),
      symbolSize: typeof n.symbolSize === 'number' ? n.symbolSize : 40,
      category: typeof n.category === 'number' ? Math.trunc(n.category) : 0,
      label: { show: true },
      entitlement: typeof n.entitlement === 'string' ? n.entitlement : null,
      kind: typeof n.kind === 'string' ? n.kind : null,
      is_root: n.is_root === true,
    });
  }

  const links: GraphLink[] = [];
  for (let i = 0; i < linksRaw.length; i++) {
    const l = linksRaw[i];
    if (!isRecord(l)) {
      return { graph: null, error: `links[${i}] must be an object with "source" and "target".` };
    }
    const source = str(l.source);
    const target = str(l.target);
    if (!ids.has(source)) {
      return {
        graph: null,
        error: `links[${i}].source "${source || '(empty)'}" does not match any node id.`,
      };
    }
    if (!ids.has(target)) {
      return {
        graph: null,
        error: `links[${i}].target "${target || '(empty)'}" does not match any node id.`,
      };
    }
    links.push({
      source,
      target,
      relationship_type: str(l.relationship_type, 'RELATED'),
      value: typeof l.value === 'number' ? l.value : 1,
    });
  }

  let categories = coerceCategories(parsed.categories);
  if (categories.length === 0) {
    const maxCat = nodes.reduce((m, n) => Math.max(m, n.category), 0);
    categories = Array.from({ length: maxCat + 1 }, (_, i) => ({ name: `Category ${i}` }));
  }

  return { graph: { nodes, links, categories, root_id: null }, error: null };
}

function errorInfo(error: unknown): { message: string; status?: number; code?: string } {
  const api = error instanceof ApiError ? error : null;
  return {
    message: error instanceof Error ? error.message : 'Request failed',
    status: api?.status,
    code: api?.code,
  };
}

export default function FamilyGraphPanel({
  clientId,
  title = 'Family graph',
  subtitle = 'Household structure from live ownership and relationship data',
}: FamilyGraphPanelProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [customGraph, setCustomGraph] = useState<GraphData | null>(null);
  const [pasteOpen, setPasteOpen] = useState(false);
  const [pasteText, setPasteText] = useState('');
  const [pasteError, setPasteError] = useState<string | null>(null);
  const seqRef = useRef(0);

  const [graphSource, setGraphSource] = useState<string>('');
  const [askText, setAskText] = useState('What succession or regulatory links sit on this client?');
  const [askAnswer, setAskAnswer] = useState('');
  const [asking, setAsking] = useState(false);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setState({ status: 'loading' });
    try {
      let payload: unknown;
      let source = '';
      try {
        const wealth = await get<any>(`/graph/clients/${clientId}`);
        payload = wealth.data;
        source = String(wealth.data?.source || 'neo4j');
      } catch {
        const result = await endpoints.family.graph(clientId);
        payload = result.data;
        source = 'family-graph';
      }
      if (seq !== seqRef.current) return;
      setGraphSource(source);
      const data = coerceGraphData(payload);
      setState({ status: 'success', data, raw: JSON.stringify(payload, null, 2) });
    } catch (e) {
      if (seq !== seqRef.current) return;
      setState({ status: 'error', error: e });
    }
  }, [clientId]);

  useEffect(() => {
    void load();
    return () => {
      seqRef.current += 1; // invalidate in-flight requests on change/unmount
    };
  }, [load]);

  const applyPaste = () => {
    const { graph, error } = parseCustomGraph(pasteText);
    setPasteError(error);
    if (graph) setCustomGraph(graph);
  };

  const clearCustom = () => {
    setCustomGraph(null);
    setPasteText('');
    setPasteError(null);
  };

  let body: ReactNode;
  if (customGraph) {
    body = (
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Badge variant="outline">Custom graph data</Badge>
          <Button variant="outline" size="sm" onClick={clearCustom}>
            Use live data
          </Button>
        </div>
        <GraphView data={customGraph} height={440} />
      </div>
    );
  } else if (state.status === 'loading') {
    body = (
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-[380px] w-full" />
        <Skeleton className="h-4 w-28" />
      </div>
    );
  } else if (state.status === 'error') {
    const info = errorInfo(state.error);
    body = (
      <div className="rounded-md border border-gray-300 bg-gray-50 p-4">
        <div className="text-sm font-semibold text-gray-900">Could not load family graph</div>
        <p className="mt-1 text-sm text-gray-700">{info.message}</p>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
          {info.status !== undefined && <Badge variant="outline">HTTP {info.status}</Badge>}
          {info.code && <Badge variant="outline">Code: {info.code}</Badge>}
        </div>
        <div className="mt-3">
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Retry
          </Button>
        </div>
      </div>
    );
  } else if (state.data.nodes.length === 0) {
    body = (
      <div className="rounded-md border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
        <div className="text-sm font-semibold text-gray-900">No family graph</div>
        <p className="mt-1 text-sm text-gray-600">
          The live family graph is gated by DEC-06. Enable{' '}
          <code className="rounded bg-gray-200 px-1">FAMILY_DEC06_ENABLED</code> to load household
          structure. You can still visualise any graph using &ldquo;Paste graph data&rdquo; below.
        </p>
      </div>
    );
  } else {
    const data = state.data;
    const raw = state.raw;
    body = (
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{data.nodes.length} nodes</Badge>
            <Badge variant="secondary">{data.links.length} links</Badge>
            <Badge variant="secondary">{data.categories.length} categories</Badge>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <span
                    className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-gray-300 text-xs font-medium text-gray-600"
                    aria-label="About the legend"
                  >
                    ?
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-[220px] text-xs text-gray-600">
                    Node colour shows category and size reflects the source symbolSize. Drag nodes
                    to rearrange, scroll to zoom, drag the background to pan, or use &ldquo;Reset
                    view&rdquo;.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <Button variant="outline" size="sm" onClick={() => void load()}>
            Refresh
          </Button>
        </div>

        <GraphView data={data} height={440} />
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
          <Badge variant="outline">{graphSource === 'neo4j' ? 'Neo4j' : graphSource === 'postgres_fallback' ? 'Local graph' : 'Family graph'}</Badge>
        </div>
        <div className="space-y-2">
          <Textarea rows={2} value={askText} onChange={(e) => setAskText(e.target.value)} />
          <Button
            variant="outline"
            size="sm"
            disabled={asking}
            onClick={() => {
              setAsking(true);
              setAskAnswer('');
              post(`/graph/clients/${clientId}/ask`, { question: askText })
                .then((res) => setAskAnswer(String(res.data?.text || '')))
                .catch((e) => setAskAnswer(e instanceof Error ? e.message : 'The graph question failed'))
                .finally(() => setAsking(false));
            }}
          >
            {asking ? 'Asking…' : 'Ask the graph'}
          </Button>
          {askAnswer && <p className="text-sm text-gray-800 whitespace-pre-wrap">{askAnswer}</p>}
        </div>

        <Separator />

        <details>
          <summary className="cursor-pointer list-none text-sm font-medium text-gray-700">
            Technical details
            <span className="ml-2 text-xs text-gray-400">
              (GET /clients/{clientId}/family-graph)
            </span>
          </summary>
          <div className="mt-3">
            <p className="mb-2 text-xs text-gray-500">
              Raw response for{' '}
              <code className="rounded bg-gray-100 px-1">
                GET /clients/{clientId}/family-graph
              </code>
            </p>
            <ScrollArea className="h-48 w-full rounded-md border border-gray-200 bg-gray-50">
              <pre className="whitespace-pre-wrap break-all p-3 text-[11px] leading-relaxed text-gray-700">
                {raw}
              </pre>
            </ScrollArea>
          </div>
        </details>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {subtitle && <CardDescription>{subtitle}</CardDescription>}
      </CardHeader>

      <CardContent>{body}</CardContent>

      <CardFooter className="flex flex-col items-stretch gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setPasteOpen((v) => !v)}
          aria-expanded={pasteOpen}
        >
          {pasteOpen ? 'Hide paste graph data' : 'Paste graph data'}
        </Button>
        {pasteOpen && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500">
              Paste arbitrary JSON with <code>nodes: [{'{id,name}'}]</code> and{' '}
              <code>links: [{'{source,target}'}]</code>; optional{' '}
              <code>categories: [{'{name}'}]</code>. All link endpoints must resolve to a node id.
              Nothing is persisted.
            </p>
            <Textarea
              value={pasteText}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setPasteText(e.target.value)}
              rows={6}
              className="font-mono text-xs"
              placeholder={
                '{\n  "nodes": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],\n' +
                '  "links": [{"source": "a", "target": "b"}]\n}'
              }
            />
            {pasteError && <p className="text-xs text-gray-800">{pasteError}</p>}
            <div className="flex items-center gap-2">
              <Button size="sm" onClick={applyPaste}>
                Visualise pasted data
              </Button>
              {customGraph && (
                <Button variant="ghost" size="sm" onClick={clearCustom}>
                  Clear custom data
                </Button>
              )}
            </div>
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
