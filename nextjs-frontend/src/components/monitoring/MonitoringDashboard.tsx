'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Button,
  Tag,
  Alert,
  Statistic,
  Progress,
  Select,
  Switch,
  Divider,
  Empty,
} from 'antd';
import {
  MonitorOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  BarChartOutlined,
  LineChartOutlined,
  DashboardOutlined,
  SettingOutlined,
  ExportOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { Environment } from '@/types';
import EnvironmentMonitoringCard from './EnvironmentMonitoringCard';
import MetricsCharts from './MetricsCharts';
import AlertsPanel from './AlertsPanel';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export default function MonitoringDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [timeRange, setTimeRange] = useState('1h');
  const [selectedEnvironments, setSelectedEnvironments] = useState<string[]>([]);
  const queryClient = useQueryClient();

  // Fetch environments for monitoring
  const { data: environmentsResponse, isLoading, error, refetch } = useQuery({
    queryKey: ['environments-monitoring'],
    queryFn: () => apiClient.listEnvironments(),
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
    refetchIntervalInBackground: true,
  });

  const environments = environmentsResponse?.environments || [];

  // Auto-refresh management
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(() => {
        refetch();
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refetch]);

  // Environment statistics
  const stats = {
    total: environments.length,
    running: environments.filter(e => e.status === 'running').length,
    pending: environments.filter(e => e.status === 'pending').length,
    failed: environments.filter(e => e.status === 'failed').length,
    stopped: environments.filter(e => e.status === 'stopped').length,
  };

  const formatDateTime = (dateString: string): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      running: '#52c41a',
      pending: '#faad14', 
      failed: '#ff4d4f',
      stopped: '#8c8c8c',
      unknown: '#8c8c8c',
    };
    return colors[status as keyof typeof colors] || colors.unknown;
  };

  const handleExportMetrics = () => {
    // Placeholder for metrics export functionality
    const data = {
      timestamp: new Date().toISOString(),
      environments: environments.map(env => ({
        id: env.id,
        status: env.status,
        created_at: env.created_at,
        resource_config: env.resource_config,
      })),
      summary: stats,
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `environment-metrics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <Title level={4} type="danger">
            Failed to load monitoring data
          </Title>
          <Text type="secondary">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </Text>
          <br />
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={() => refetch()} 
            className="mt-4"
          >
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <Card>
        <div className="flex justify-between items-start mb-4">
          <div>
            <Title level={3} className="mb-2 flex items-center">
              <MonitorOutlined className="mr-3 text-blue-500" />
              Environment Monitoring Dashboard
            </Title>
            <Paragraph type="secondary" className="mb-0">
              Real-time monitoring of your research computing environments with health indicators and resource usage.
            </Paragraph>
          </div>
          <Space>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExportMetrics}
            >
              Export Metrics
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              Refresh
            </Button>
          </Space>
        </div>

        {/* Monitoring Controls */}
        <Row gutter={16} align="middle" className="mb-4">
          <Col>
            <Space align="center">
              <Text strong>Auto-refresh:</Text>
              <Switch 
                checked={autoRefresh}
                onChange={setAutoRefresh}
                checkedChildren={<EyeOutlined />}
                unCheckedChildren={<PauseCircleOutlined />}
              />
            </Space>
          </Col>
          
          {autoRefresh && (
            <Col>
              <Space align="center">
                <Text>Interval:</Text>
                <Select
                  value={refreshInterval}
                  onChange={setRefreshInterval}
                  style={{ width: 100 }}
                  size="small"
                >
                  <Option value={10}>10s</Option>
                  <Option value={30}>30s</Option>
                  <Option value={60}>1m</Option>
                  <Option value={300}>5m</Option>
                </Select>
              </Space>
            </Col>
          )}

          <Col>
            <Space align="center">
              <Text>Time Range:</Text>
              <Select
                value={timeRange}
                onChange={setTimeRange}
                style={{ width: 100 }}
                size="small"
              >
                <Option value="1h">1h</Option>
                <Option value="6h">6h</Option>
                <Option value="24h">24h</Option>
                <Option value="7d">7d</Option>
                <Option value="30d">30d</Option>
              </Select>
            </Space>
          </Col>

          <Col flex="auto">
            <div className="text-right">
              <Text type="secondary" className="text-sm">
                Last updated: {formatDateTime(new Date().toISOString())}
              </Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Statistics Overview */}
      <Card title="Environment Statistics">
        <Row gutter={16}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Environments"
              value={stats.total}
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Running"
              value={stats.running}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress 
              percent={stats.total > 0 ? (stats.running / stats.total) * 100 : 0} 
              strokeColor="#52c41a"
              size="small"
              showInfo={false}
              className="mt-2"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Pending"
              value={stats.pending}
              valueStyle={{ color: '#faad14' }}
            />
            <Progress 
              percent={stats.total > 0 ? (stats.pending / stats.total) * 100 : 0} 
              strokeColor="#faad14"
              size="small"
              showInfo={false}
              className="mt-2"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Issues"
              value={stats.failed + stats.stopped}
              valueStyle={{ color: stats.failed > 0 ? '#ff4d4f' : '#8c8c8c' }}
            />
            <Progress 
              percent={stats.total > 0 ? ((stats.failed + stats.stopped) / stats.total) * 100 : 0} 
              strokeColor={stats.failed > 0 ? "#ff4d4f" : "#8c8c8c"}
              size="small"
              showInfo={false}
              className="mt-2"
            />
          </Col>
        </Row>
      </Card>

      {/* Alerts Panel */}
      <AlertsPanel environments={environments} />

      {/* Environment Grid */}
      <Card title="Environment Health Overview" loading={isLoading}>
        {environments.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <Title level={4}>No Environments to Monitor</Title>
                <Text type="secondary">
                  Create and launch environments to see their monitoring data here.
                </Text>
              </div>
            }
          />
        ) : (
          <Row gutter={[16, 16]}>
            {environments.map((environment) => (
              <Col key={environment.id} xs={24} sm={12} lg={8} xl={6}>
                <EnvironmentMonitoringCard 
                  environment={environment}
                  onRefresh={() => refetch()}
                />
              </Col>
            ))}
          </Row>
        )}
      </Card>

      {/* Metrics Charts */}
      {environments.length > 0 && (
        <MetricsCharts 
          environments={environments.filter(env => 
            selectedEnvironments.length === 0 || selectedEnvironments.includes(env.id)
          )}
          timeRange={timeRange}
        />
      )}

      {/* System Health Status */}
      <Card title="System Health Status">
        <Row gutter={16}>
          <Col span={8}>
            <div className="text-center">
              <div className="text-3xl mb-2">
                {stats.running > 0 ? '🟢' : stats.pending > 0 ? '🟡' : '🔴'}
              </div>
              <Text strong>
                {stats.running > 0 ? 'Healthy' : stats.pending > 0 ? 'Scaling' : 'Critical'}
              </Text>
              <br />
              <Text type="secondary" className="text-sm">
                Overall system status
              </Text>
            </div>
          </Col>
          
          <Col span={8}>
            <div className="text-center">
              <div className="text-3xl mb-2">📊</div>
              <Text strong>
                {((stats.running / Math.max(stats.total, 1)) * 100).toFixed(1)}%
              </Text>
              <br />
              <Text type="secondary" className="text-sm">
                Availability rate
              </Text>
            </div>
          </Col>
          
          <Col span={8}>
            <div className="text-center">
              <div className="text-3xl mb-2">⚡</div>
              <Text strong>
                {autoRefresh ? 'Live' : 'Paused'}
              </Text>
              <br />
              <Text type="secondary" className="text-sm">
                Monitoring status
              </Text>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
