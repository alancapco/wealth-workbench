'use client';

import React from 'react';
import ReactECharts from 'echarts-for-react';

interface AllocationChartProps {
  data: {
    equities: number;
    fixed_income: number;
    cash: number;
  };
}

export default function AllocationChart({ data }: AllocationChartProps) {
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%'
    },
    series: [
      {
        type: 'pie',
        radius: ['60%', '80%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 0,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: data.equities,
            name: 'Equities',
            itemStyle: { color: '#000000' }
          },
          {
            value: data.fixed_income,
            name: 'Fixed Income',
            itemStyle: { color: '#666666' }
          },
          {
            value: data.cash,
            name: 'Cash',
            itemStyle: { color: '#CCCCCC' }
          }
        ]
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: '250px' }}
      opts={{ renderer: 'svg' }}
    />
  );
}
