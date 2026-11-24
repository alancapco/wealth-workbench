'use client';

import { useCallback, useEffect, useId, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  symbolSize: number;
  category: number;
  label: { show: boolean };
  entitlement: string | null;
  kind: string | null;
  is_root: boolean;
}

/**
 * d3.forceLink mutates `source` / `target` from ids into node object
 * references, so those fields must accept both shapes.
 */
export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship_type: string;
  value: number;
}

export interface GraphCategory {
  name: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  categories: GraphCategory[];
  root_id: string | null;
}

// Monochrome palette — Capco design system (black / white / gray only).
const PALETTE = ['#111111', '#4b5563', '#9ca3af', '#d1d5db', '#6b7280'] as const;

function categoryColor(index: number): string {
  const i = Number.isFinite(index) ? Math.abs(Math.trunc(index)) : 0;
  return PALETTE[i % PALETTE.length];
}

function nodeRadius(d: GraphNode): number {
  const raw = typeof d.symbolSize === 'number' && d.symbolSize > 0 ? d.symbolSize / 2 : 18;
  return Math.max(12, Math.min(34, raw));
}

type TooltipState =
  | {
      type: 'node';
      x: number;
      y: number;
      name: string;
      category: string;
      kind: string | null;
      entitlement: string | null;
    }
  | {
      type: 'link';
      x: number;
      y: number;
      source: string;
      target: string;
      relationship_type: string;
    };

export default function GraphView({ data, height = 440 }: { data: GraphData; height?: number }) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const [tip, setTip] = useState<TooltipState | null>(null);

  // Stable, SSR-safe unique id so multiple GraphViews can coexist on a page.
  const rawId = useId();
  const markerId = `fg${rawId.replace(/[^a-zA-Z0-9]/g, '')}-arrow`;

  const resetView = useCallback(() => {
    const svgEl = svgRef.current;
    const zoom = zoomRef.current;
    if (!svgEl || !zoom) return;
    zoom.transform(d3.select<SVGSVGElement, unknown>(svgEl), d3.zoomIdentity);
  }, []);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    const svgEl = svgRef.current;
    if (!wrapper || !svgEl) return;

    let currentWidth = wrapper.clientWidth || 640;
    const svg = d3
      .select<SVGSVGElement, unknown>(svgEl)
      .attr('width', currentWidth)
      .attr('height', height);
    svg.selectAll('*').remove();

    // Deep-copy: d3 mutates nodes (x/y/vx/vy/fx/fy/index) and rewrites link
    // endpoints into node objects. React props / shared state must stay intact.
    const simNodes: GraphNode[] = data.nodes.map((n) => ({
      ...n,
      label: { show: n.label?.show !== false },
    }));
    const allIds = new Set(simNodes.map((n) => n.id));
    const simLinks: GraphLink[] = data.links
      .map((l) => ({
        ...l,
        source: typeof l.source === 'string' ? l.source : l.source.id,
        target: typeof l.target === 'string' ? l.target : l.target.id,
      }))
      .filter(
        (l) =>
          typeof l.source === 'string' &&
          typeof l.target === 'string' &&
          allIds.has(l.source) &&
          allIds.has(l.target),
      );

    const nodeById = new Map<string, GraphNode>();
    simNodes.forEach((n) => nodeById.set(n.id, n));

    const isRoot = (d: GraphNode): boolean =>
      d.is_root === true || (data.root_id != null && d.id === data.root_id);

    const nodeOf = (ep: string | GraphNode): GraphNode | undefined =>
      typeof ep === 'string' ? nodeById.get(ep) : ep;

    const endpointName = (ep: string | GraphNode): string => {
      const n = nodeOf(ep);
      if (n) return n.name;
      return typeof ep === 'string' ? ep : ep.id;
    };

    // Trim line endpoints to the node edges so the arrow head stays visible.
    const linkEndpoints = (d: GraphLink) => {
      const s = nodeOf(d.source);
      const t = nodeOf(d.target);
      const sx0 = s?.x ?? currentWidth / 2;
      const sy0 = s?.y ?? height / 2;
      const tx0 = t?.x ?? currentWidth / 2;
      const ty0 = t?.y ?? height / 2;
      const dx = tx0 - sx0;
      const dy = ty0 - sy0;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const sr = s ? nodeRadius(s) : 12;
      const tr = (t ? nodeRadius(t) : 12) + 7;
      return {
        x1: sx0 + (dx / dist) * sr,
        y1: sy0 + (dy / dist) * sr,
        x2: tx0 - (dx / dist) * tr,
        y2: ty0 - (dy / dist) * tr,
      };
    };

    const defs = svg.append('defs');
    defs
      .append('marker')
      .attr('id', markerId)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#9ca3af');

    const zoomLayer = svg.append('g').attr('class', 'zoom-layer');

    const linkLines = zoomLayer
      .append('g')
      .attr('class', 'links')
      .selectAll<SVGLineElement, GraphLink>('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', '#9ca3af')
      .attr('stroke-width', 1.5)
      .attr('marker-end', `url(#${markerId})`);

    // Transparent, wider hit-lines make link tooltips easy to trigger.
    const hitLines = zoomLayer
      .append('g')
      .attr('class', 'link-hits')
      .selectAll<SVGLineElement, GraphLink>('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', 'transparent')
      .attr('stroke-width', 12)
      .attr('pointer-events', 'stroke')
      .style('cursor', 'pointer');

    const nodeGroups = zoomLayer
      .append('g')
      .attr('class', 'nodes')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(simNodes)
      .join('g')
      .attr('class', 'node')
      .style('cursor', 'grab');

    nodeGroups
      .append('circle')
      .attr('r', (d) => nodeRadius(d))
      .attr('fill', (d) => categoryColor(d.category))
      .attr('stroke', (d) => (isRoot(d) ? '#111111' : '#ffffff'))
      .attr('stroke-width', (d) => (isRoot(d) ? 3 : 1.5));

    nodeGroups
      .append('text')
      .text((d) => d.name)
      .attr('x', (d) => nodeRadius(d) + 5)
      .attr('y', 4)
      .attr('font-size', 11)
      .attr('fill', '#111827')
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 3)
      .attr('stroke-linejoin', 'round')
      .attr('paint-order', 'stroke')
      .style('display', (d) => (d.label?.show === false ? 'none' : null));

    const positionLines = <P extends d3.BaseType, PD>(
      selection: d3.Selection<SVGLineElement, GraphLink, P, PD>,
    ): void => {
      selection
        .attr('x1', (d) => linkEndpoints(d).x1)
        .attr('y1', (d) => linkEndpoints(d).y1)
        .attr('x2', (d) => linkEndpoints(d).x2)
        .attr('y2', (d) => linkEndpoints(d).y2);
    };

    // Anchor the root near centre with a low-strength X/Y pull.
    const centerForce = d3.forceCenter<GraphNode>(currentWidth / 2, height / 2);
    const forceX = d3
      .forceX<GraphNode>(currentWidth / 2)
      .strength((d) => (isRoot(d) ? 0.08 : 0));
    const forceY = d3
      .forceY<GraphNode>(height / 2)
      .strength((d) => (isRoot(d) ? 0.08 : 0));

    const sim = d3
      .forceSimulation<GraphNode>(simNodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphLink>(simLinks)
          .id((d) => d.id)
          .distance(120),
      )
      .force('charge', d3.forceManyBody<GraphNode>().strength(-420))
      .force('center', centerForce)
      .force(
        'collide',
        d3.forceCollide<GraphNode>().radius((d) => nodeRadius(d) + 18),
      )
      .force('x', forceX)
      .force('y', forceY);

    sim.on('tick', () => {
      positionLines(linkLines);
      positionLines(hitLines);
      nodeGroups.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    const drag = d3
      .drag<SVGGElement, GraphNode>()
      .on('start', (event: any, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event: any, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event: any, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
    nodeGroups.call(drag);

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event: any) => {
        zoomLayer.attr('transform', event.transform.toString());
      });
    svg.call(zoom);
    zoom.transform(svg, d3.zoomIdentity);
    zoomRef.current = zoom;

    const wrapperRect = () => wrapper.getBoundingClientRect();

    nodeGroups
      .on('mousemove', (event: MouseEvent, d) => {
        const rect = wrapperRect();
        setTip({
          type: 'node',
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
          name: d.name,
          category: data.categories[d.category]?.name ?? `Category ${d.category}`,
          kind: d.kind ?? null,
          entitlement: d.entitlement ?? null,
        });
      })
      .on('mouseleave', () => setTip(null));

    hitLines
      .on('mousemove', (event: MouseEvent, d) => {
        const rect = wrapperRect();
        setTip({
          type: 'link',
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
          source: endpointName(d.source),
          target: endpointName(d.target),
          relationship_type: d.relationship_type,
        });
      })
      .on('mouseleave', () => setTip(null));

    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 0;
      if (w <= 0 || Math.abs(w - currentWidth) < 1) return;
      currentWidth = w;
      svg.attr('width', w);
      centerForce.x(w / 2);
      forceX.x(w / 2);
      forceY.y(height / 2);
      sim.alpha(0.3).restart();
    });
    observer.observe(wrapper);

    return () => {
      sim.stop();
      observer.disconnect();
      svg.selectAll('*').remove();
    };
  }, [data, height, markerId]);

  const counts = data.categories.map((c, i) => ({
    name: c.name,
    color: categoryColor(i),
    count: data.nodes.filter((n) => n.category === i).length,
  }));

  return (
    <div ref={wrapperRef} className="relative w-full">
      <svg
        ref={svgRef}
        className="block"
        style={{ width: '100%', height }}
        aria-label="Family graph"
      />

      {tip && (
        <div
          role="tooltip"
          className="pointer-events-none absolute z-10 max-w-xs rounded-md border border-gray-300 bg-white px-3 py-2 text-xs text-gray-700 shadow-lg"
          style={{ left: tip.x, top: tip.y, transform: 'translate(12px, 12px)' }}
        >
          {tip.type === 'node' ? (
            <div className="space-y-0.5">
              <div className="font-semibold text-gray-900">{tip.name}</div>
              <div>Category: {tip.category}</div>
              <div>Kind: {tip.kind ?? '—'}</div>
              <div>Entitlement: {tip.entitlement ?? '—'}</div>
            </div>
          ) : (
            <div className="space-y-0.5">
              <div className="font-semibold text-gray-900">
                {tip.source} → {tip.target}
              </div>
              <div>Relationship: {tip.relationship_type}</div>
            </div>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        {counts.map((c, i) => (
          <span key={i} className="inline-flex items-center gap-1.5 text-xs text-gray-600">
            <span
              className="inline-block h-3 w-3 rounded-sm border border-gray-300"
              style={{ backgroundColor: c.color }}
            />
            {c.name} <span className="text-gray-400">({c.count})</span>
          </span>
        ))}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={resetView}>
          Reset view
        </Button>
        <Badge variant="secondary">
          {data.nodes.length} nodes · {data.links.length} links
        </Badge>
      </div>
    </div>
  );
}
