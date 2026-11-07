'use client';

import React from 'react';
import ReactECharts from 'echarts-for-react';

interface PerformanceChartProps {
  data: {
    labels: string[];
    datasets: Array<{
      name: string;
      data: number[];
    }>;
  };
}

export default function PerformanceChart({ data }: PerformanceChartProps) {
  // Safety check for data
  if (!data || !data.datasets || data.datasets.length === 0) {
    return (
      <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#666' }}>No performance data available</div>
      </div>
    );
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach((item: any) => {
          result += `${item.marker} ${item.seriesName}: +${item.value}%<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: data.datasets.map(d => d.name),
      bottom: 10,
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.labels,
      axisLine: {
        lineStyle: { color: '#E5E5E5' }
      },
      axisLabel: {
        color: '#666666',
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '+{value}%',
        color: '#666666',
        fontSize: 11
      },
      splitLine: {
        lineStyle: { color: '#F5F5F5' }
      }
    },
    series: data.datasets.map((dataset, index) => ({
      name: dataset.name,
      type: 'line',
      smooth: true,
      data: dataset.data,
      lineStyle: {
        width: 2,
        color: index === 0 ? '#000000' : '#999999'
      },
      itemStyle: {
        color: index === 0 ? '#000000' : '#999999'
      },
      areaStyle: index === 0 ? {
        color: 'rgba(0, 0, 0, 0.05)'
      } : undefined,
      ...(index === 1 && {
        lineStyle: {
          type: 'dashed',
          width: 2,
          color: '#999999'
        }
      })
    }))
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: '250px' }}
      opts={{ renderer: 'svg' }}
    />
  );
}
