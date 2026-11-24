/**
 * Live OpenAPI introspection. The catalogue is generated from the running
 * backend's own schema, so no endpoint can be missing from the UI and no
 * contract can drift out of date.
 */
import { API_BASE } from './endpoints';

export type HttpMethod = 'get' | 'post' | 'patch' | 'put' | 'delete';

export interface OpenApiParam {
  name: string;
  in: 'path' | 'query' | 'header' | 'cookie';
  required: boolean;
  type: string;
  enum?: string[];
  example?: unknown;
  description?: string;
}

export interface BodyField {
  name: string;
  type: string;
  required: boolean;
  enum?: string[];
  description?: string;
  defaultValue: unknown;
}

export interface OpenApiOperation {
  id: string;
  method: HttpMethod;
  path: string;
  relativePath: string;
  group: string;
  summary: string;
  description: string;
  params: OpenApiParam[];
  bodyFields: BodyField[];
  tags: string[];
}

const GROUP_LABELS: Record<string, string> = {
  session: 'Platform · Identity',
  clients: 'Clients & Relationships',
  'demo-clients': 'Portfolio & Market',
  dashboard: 'Workspace',
  market: 'Portfolio & Market',
  briefs: 'Advice & Execution',
  workflow: 'Advice & Execution',
  workflows: 'Advice & Execution',
  books: 'Engagement',
  priorities: 'Engagement',
  products: 'Advice & Execution',
  actions: 'Advice & Execution',
  messages: 'Engagement',
  calendar: 'Engagement',
  meetings: 'Engagement',
  extractions: 'Engagement',
  memory: 'Clients & Relationships',
  households: 'Clients & Relationships',
  artifacts: 'Platform · Artifacts',
  telemetry: 'Platform · Telemetry',
  admin: 'Platform · Governance',
};

function resolveRef(schema: any, components: any): any {
  if (!schema) return {};
  if (schema.$ref) {
    const name = String(schema.$ref).split('/').pop() || '';
    return components?.schemas?.[name] || {};
  }
  return schema;
}

function scalarDefault(schema: any, name: string): unknown {
  const s = schema || {};
  if (s.default !== undefined) return s.default;
  if (s.example !== undefined) return s.example;
  if (Array.isArray(s.enum) && s.enum.length) return s.enum[0];
  const t = s.type || (s.anyOf ? s.anyOf[0]?.type : '') || '';
  if (t === 'array') return [];
  if (t === 'object' || s.properties) return {};
  if (t === 'boolean') return false;
  if (t === 'integer' || t === 'number') return 0;
  if (s.format === 'uuid') return '00000000-0000-0000-0000-000000000000';
  if (s.format === 'date-time') return new Date().toISOString();
  if (/hash/i.test(name)) return '0'.repeat(64);
  if (/id/i.test(name)) return '';
  return '';
}

function buildBodyFields(schema: any, components: any): BodyField[] {
  const resolved = resolveRef(schema, components);
  const props = resolved?.properties || {};
  const required: string[] = resolved?.required || [];
  return Object.entries(props).map(([name, raw]) => {
    const s = resolveRef(raw, components);
    const t = s.type || (s.anyOf ? s.anyOf[0]?.type : '') || (s.$ref ? 'object' : 'string');
    return {
      name,
      type: String(t),
      required: required.includes(name),
      enum: s.enum,
      description: s.description,
      defaultValue: scalarDefault(s, name),
    };
  });
}

export function defaultBody(fields: BodyField[]): string {
  const obj: Record<string, unknown> = {};
  fields.forEach((f) => {
    obj[f.name] = f.defaultValue;
  });
  return JSON.stringify(obj, null, 2);
}

/**
 * The backend uses a handful of terse, engineering-facing summaries. They are
 * accurate but not readable in an adviser-facing list, so give them plain names.
 */
const SUMMARY_OVERRIDES: Record<string, string> = {
  Live: 'Service availability',
  Ready: 'Readiness check',
  Root: 'Service information',
  'Get Kpis': 'View book KPIs',
  'Get My Day Dashboard': 'View My Day overview',
  'Get Book Stats': 'View book statistics',
  'Get Performance Trend': 'View performance trend',
  'Future Planner': 'Run future planner',
  'Investors Like Me': 'Find investors like me',
};
function tidySummary(summary: string): string {
  return (
    SUMMARY_OVERRIDES[summary] ||
    summary.replace(/\bKpis\b/g, 'KPIs').replace(/\bAum\b/g, 'AUM')
  );
}

/** Human label for operations that carry no OpenAPI summary. */
const VERB_LABELS: Record<string, string> = {
  GET: 'View', POST: 'Create', PATCH: 'Update', PUT: 'Replace', DELETE: 'Remove',
};
function humaniseOperation(method: string, relativePath: string): string {
  const words = relativePath
    .split('/')
    .filter(Boolean)
    .filter((s) => !s.startsWith('{'))
    .slice(-2)
    .join(' ')
    .replace(/[-_]/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .trim();
  return `${VERB_LABELS[method.toUpperCase()] || 'Manage'} ${words || 'record'}`;
}

export async function fetchOpenApi(): Promise<OpenApiOperation[]> {
  const res = await fetch(`${API_BASE}/openapi.json`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Could not load available operations (status ${res.status})`);
  const doc = await res.json();
  const components = doc.components || {};
  const operations: OpenApiOperation[] = [];

  Object.entries(doc.paths || {}).forEach(([path, ops]: [string, any]) => {
    Object.entries(ops).forEach(([method, raw]: [string, any]) => {
      if (!['get', 'post', 'patch', 'put', 'delete'].includes(method)) return;
      const op = raw as any;
      const relativePath = path.replace(/^\/api\/v1/, '');
      const segment = relativePath.split('/').filter(Boolean)[0] || 'root';
      const group = GROUP_LABELS[segment] || `Other · ${segment}`;

      const params: OpenApiParam[] = (op.parameters || []).map((p: any) => ({
        name: p.name,
        in: p.in,
        required: Boolean(p.required),
        type: p.schema?.type || 'string',
        enum: p.schema?.enum,
        example: p.example ?? p.schema?.default,
        description: p.description,
      }));

      const bodySchema = op.requestBody?.content?.['application/json']?.schema;
      const bodyFields = bodySchema ? buildBodyFields(bodySchema, components) : [];

      operations.push({
        id: `${method.toUpperCase()} ${path}`,
        method: method as HttpMethod,
        path,
        relativePath,
        group,
        summary: tidySummary(op.summary || humaniseOperation(method, relativePath)),
        description: op.description || '',
        params,
        bodyFields,
        tags: op.tags || [],
      });
    });
  });

  return operations.sort((a, b) =>
    a.group.localeCompare(b.group) || a.relativePath.localeCompare(b.relativePath),
  );
}

/** Path templates use {name}; substitute from the supplied values. */
export function materialisePath(template: string, values: Record<string, string>): string {
  return template.replace(/\{([^}]+)\}/g, (_, k) => encodeURIComponent(values[k] || ''));
}
