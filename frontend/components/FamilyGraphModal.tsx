'use client';

import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface FamilyGraphModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientName: string;
}

export default function FamilyGraphModal({ isOpen, onClose, clientName }: FamilyGraphModalProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (isOpen && chartRef.current) {
      // Initialize chart
      chartInstance.current = echarts.init(chartRef.current);

      // Family graph data
      const graphData = {
        nodes: [
          {
            id: 'patriarch',
            name: 'Patriarch Trust',
            symbolSize: 80,
            value: 120.5,
            category: 0,
            label: { show: true }
          },
          {
            id: 'son1',
            name: 'Gen 2 - Son 1',
            symbolSize: 60,
            value: 35.2,
            category: 1,
            label: { show: true }
          },
          {
            id: 'daughter1',
            name: 'Gen 2 - Daughter 1',
            symbolSize: 60,
            value: 28.8,
            category: 1,
            label: { show: true }
          },
          {
            id: 'son2',
            name: 'Gen 2 - Son 2',
            symbolSize: 60,
            value: 31.5,
            category: 1,
            label: { show: true }
          },
          {
            id: 'edu1',
            name: 'Gen 3 - Education Trust 1',
            symbolSize: 45,
            value: 8.5,
            category: 2,
            label: { show: true }
          },
          {
            id: 'edu2',
            name: 'Gen 3 - Education Trust 2',
            symbolSize: 45,
            value: 7.2,
            category: 2,
            label: { show: true }
          },
          {
            id: 'operating',
            name: 'Operating Company',
            symbolSize: 50,
            value: 9.3,
            category: 3,
            label: { show: true }
          }
        ],
        links: [
          { source: 'patriarch', target: 'son1', value: 1 },
          { source: 'patriarch', target: 'daughter1', value: 1 },
          { source: 'patriarch', target: 'son2', value: 1 },
          { source: 'son1', target: 'edu1', value: 0.5 },
          { source: 'daughter1', target: 'edu2', value: 0.5 },
          { source: 'patriarch', target: 'operating', value: 0.3 }
        ],
        categories: [
          { name: 'Gen 1 - Patriarch' },
          { name: 'Gen 2 - Children' },
          { name: 'Gen 3 - Education' },
          { name: 'Operating Entity' }
        ]
      };

      const option: echarts.EChartsOption = {
        title: {
          text: 'Tan Family Office Structure',
          subtext: 'Total AUM: SGD 120.5M across 7 entities',
          top: 20,
          left: 'center',
          textStyle: {
            fontSize: 24,
            fontWeight: 600
          }
        },
        tooltip: {
          formatter: (params: any) => {
            if (params.dataType === 'node') {
              const name = params.data.name || '';
              const value = params.data.value || 0;
              return `<strong>${name}</strong><br/>AUM: SGD ${value}M<br/>Click for details`;
            } else {
              return 'Graph relationship';
            }
          }
        },
        legend: {
          data: graphData.categories.map(c => c.name),
          top: 70,
          left: 'center',
          textStyle: {
            fontSize: 12
          }
        },
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: graphData.nodes,
            links: graphData.links,
            categories: graphData.categories,
            roam: true,
            label: {
              show: true,
              position: 'right',
              formatter: '{b}',
              fontSize: 11,
              fontWeight: 500
            },
            labelLayout: {
              hideOverlap: true
            },
            emphasis: {
              focus: 'adjacency',
              lineStyle: {
                width: 3
              }
            },
            force: {
              repulsion: 400,
              gravity: 0.1,
              edgeLength: [150, 200],
              layoutAnimation: true
            },
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: 8,
            edgeLabel: {
              show: false
            },
            lineStyle: {
              color: 'source',
              curveness: 0.1,
              width: 2
            },
            itemStyle: {
              borderColor: '#000',
              borderWidth: 2
            }
          }
        ]
      };

      chartInstance.current.setOption(option);

      // Resize handler
      const handleResize = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        chartInstance.current?.dispose();
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* Modal */}
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-2xl w-full max-w-7xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-black text-white rounded-t-lg">
            <div>
              <h2 className="text-xl font-semibold">Family Office Structure</h2>
              <p className="text-sm text-gray-300 mt-1">{clientName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-300 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {/* Chart */}
          <div className="flex-1 overflow-hidden p-6">
            <div ref={chartRef} className="w-full h-full min-h-[600px]" />
          </div>

          {/* Legend & Info */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="font-semibold text-gray-700 mb-1">Entitlement Types</div>
                <div className="text-gray-600">
                  <div>• <strong>Full</strong> - Complete access</div>
                  <div>• <strong>Entity-specific</strong> - Limited to entity</div>
                  <div>• <strong>Education-only</strong> - Education expenses</div>
                  <div>• <strong>Restricted</strong> - Operational only</div>
                </div>
              </div>
              <div>
                <div className="font-semibold text-gray-700 mb-1">Total AUM</div>
                <div className="text-2xl font-bold">SGD 120.5M</div>
              </div>
              <div>
                <div className="font-semibold text-gray-700 mb-1">Entities</div>
                <div className="text-2xl font-bold">7</div>
              </div>
              <div>
                <div className="font-semibold text-gray-700 mb-1">Generations</div>
                <div className="text-2xl font-bold">3</div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end px-6 py-4 border-t border-gray-200 bg-white rounded-b-lg">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-black text-white text-sm font-medium rounded hover:bg-gray-800 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
