'use client';

import React, { useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Select,
  Empty,
  Space,
  Tag,
  Alert,
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  ArrowUpOutlined,
} from '@ant-design/icons';
import type { Environment } from '@/types';

const { Title, Text } = Typography;
const { Option } = Select;

interface MetricsChartsProps {
  environments: Environment[];
  timeRange: string;
  healthData?: any;
}

export default function MetricsCharts({ environments, timeRange, healthData }: MetricsChartsProps) {

  // Show message about real-time metrics
  const hasRealData = healthData?.environment_metrics?.length > 0;
  const realTimeData = useMemo(() => {
    if (!hasRealData) return [];
    
    const now = new Date();
    const avgCpu = healthData.aggregate_cpu_usage || 0;
    const totalMemory = healthData.total_memory_usage_mb || 0;
    const networkIn = (healthData.total_network_rx_mb || 0) * 1024; // MB to KB
    const networkOut = (healthData.total_network_tx_mb || 0) * 1024;
    
    return [{
      time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      fullTime: now,
      cpu: avgCpu,
      memory: totalMemory / Math.max(environments.filter(e => e.status === 'running').length, 1),
      storage: 0, // Not available yet
      networkIn,
      networkOut,
    }];
  }, [healthData, environments, timeRange]);

  const chartHeight = 300;

  // Simple SVG chart component
  const SimpleLineChart = ({ 
    data, 
    dataKey, 
    color = '#1890ff',
    label,
    unit = '%'
  }: {
    data: any[];
    dataKey: string;
    color?: string;
    label: string;
    unit?: string;
  }) => {
    const maxValue = Math.max(...data.map(d => d[dataKey]));
    const minValue = Math.min(...data.map(d => d[dataKey]));
    const range = maxValue - minValue || 1;

    const points = data.map((item, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - ((item[dataKey] - minValue) / range) * 100;
      return `${x},${y}`;
    }).join(' ');

    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <Text strong>{label}</Text>
          <Tag color={color}>
            {data[data.length - 1]?.[dataKey] || 0}{unit}
          </Tag>
        </div>
        <div className="relative bg-gray-50 rounded p-2" style={{ height: chartHeight / 4 }}>
          <svg width="100%" height="100%" className="absolute inset-0">
            <polyline
              fill="none"
              stroke={color}
              strokeWidth="2"
              points={points}
              vectorEffect="non-scaling-stroke"
            />
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                <stop offset="100%" stopColor={color} stopOpacity="0.1" />
              </linearGradient>
            </defs>
            <polygon
              fill={`url(#gradient-${dataKey})`}
              points={`0,100 ${points} 100,100`}
            />
          </svg>
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>Min: {minValue}{unit}</span>
          <span>Max: {maxValue}{unit}</span>
          <span>Avg: {Math.round(data.reduce((sum, item) => sum + item[dataKey], 0) / data.length)}{unit}</span>
        </div>
      </div>
    );
  };

  const ResourceUsageChart = () => (
    <Card 
      title={
        <Space>
          <LineChartOutlined className="text-blue-500" />
          Resource Usage Over Time
        </Space>
      }
      extra={
        <Select defaultValue={timeRange} size="small" style={{ width: 80 }}>
          <Option value="1h">1h</Option>
          <Option value="6h">6h</Option>
          <Option value="24h">24h</Option>
          <Option value="7d">7d</Option>
        </Select>
      }
    >
      {!hasRealData ? (
        <Alert
          message="Real-time Metrics Unavailable"
          description="Metrics collection requires running environments with metrics-server enabled. Start an environment to see live resource usage charts."
          type="info"
          showIcon
        />
      ) : (
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <SimpleLineChart
              data={realTimeData}
              dataKey="cpu"
              color="#1890ff"
              label="CPU Usage"
            />
          </Col>
          <Col span={8}>
            <SimpleLineChart
              data={realTimeData}
              dataKey="memory"
              color="#52c41a"
              label="Memory Usage"
              unit=" MB"
            />
          </Col>
          <Col span={8}>
            <div className="space-y-2">
              <Text strong>Storage Usage</Text>
              <Alert
                message="Storage metrics collection in development"
                type="warning"
                size="small"
              />
            </div>
          </Col>
        </Row>
      )}
    </Card>
  );

  const NetworkChart = () => (
    <Card 
      title={
        <Space>
          <ArrowUpOutlined className="text-green-500" />
          Network I/O
        </Space>
      }
    >
      {!hasRealData ? (
        <Alert
          message="Network Metrics Unavailable"
          description="Start running environments to see network I/O statistics."
          type="info"
          showIcon
        />
      ) : (
        <Row gutter={16}>
          <Col span={12}>
            <SimpleLineChart
              data={realTimeData}
              dataKey="networkIn"
              color="#13c2c2"
              label="Network In"
              unit=" KB/s"
            />
          </Col>
          <Col span={12}>
            <SimpleLineChart
              data={realTimeData}
              dataKey="networkOut"
              color="#eb2f96"
              label="Network Out"
              unit=" KB/s"
            />
          </Col>
        </Row>
      )}
    </Card>
  );

  const EnvironmentDistribution = () => {
    const statusCounts = environments.reduce((acc, env) => {
      acc[env.status] = (acc[env.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusColors = {
      running: '#52c41a',
      pending: '#faad14',
      failed: '#ff4d4f',
      stopped: '#8c8c8c',
    };

    return (
      <Card 
        title={
          <Space>
            <PieChartOutlined className="text-purple-500" />
            Environment Distribution
          </Space>
        }
      >
        <div className="space-y-4">
          {Object.entries(statusCounts).map(([status, count]) => {
            const percentage = (count / environments.length) * 100;
            return (
              <div key={status} className="space-y-2">
                <div className="flex justify-between items-center">
                  <Space>
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: statusColors[status as keyof typeof statusColors] }}
                    />
                    <Text className="capitalize">{status}</Text>
                  </Space>
                  <Text strong>{count} ({percentage.toFixed(1)}%)</Text>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: statusColors[status as keyof typeof statusColors]
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    );
  };

  if (environments.length === 0) {
    return (
      <Card>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div>
              <Title level={4}>No Metrics Available</Title>
              <Text type="secondary">
                Launch environments to see their performance metrics and charts.
              </Text>
            </div>
          }
        />
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Resource Usage Charts */}
      <ResourceUsageChart />

      <Row gutter={16}>
        {/* Network I/O */}
        <Col xs={24} lg={16}>
          <NetworkChart />
        </Col>

        {/* Environment Distribution */}
        <Col xs={24} lg={8}>
          <EnvironmentDistribution />
        </Col>
      </Row>

      {/* Performance Summary */}
      <Card title="Performance Summary">
        <Row gutter={16}>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-500">
                {hasRealData ? Math.round(realTimeData[0]?.cpu || 0) : 0}%
              </div>
              <Text type="secondary">Current CPU</Text>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">
                {hasRealData ? Math.round(realTimeData[0]?.memory || 0) : 0} MB
              </div>
              <Text type="secondary">Current Memory</Text>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-500">
                {hasRealData ? Math.round(realTimeData[0]?.networkIn || 0) : 0} KB/s
              </div>
              <Text type="secondary">Network In</Text>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-500">
                {environments.filter(e => e.status === 'running').length}
              </div>
              <Text type="secondary">Active Environments</Text>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
