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
  Switch,
  Empty,
  notification,
  Badge,
} from 'antd';
import {
  MonitorOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
  CloudServerOutlined,
  StopOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { Environment } from '@/types';
import EnvironmentMonitoringCard from './EnvironmentMonitoringCard';

const { Title, Text } = Typography;

export default function MonitoringDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const queryClient = useQueryClient();

  // Fetch environments for monitoring
  const { data: environmentsResponse, isLoading, error, refetch } = useQuery({
    queryKey: ['environments-monitoring'],
    queryFn: async () => {
      try {
        console.log('Fetching monitoring data...');
        const response = await apiClient.listEnvironments();
        return response;
      } catch (error) {
        console.error('Monitoring fetch error:', error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
    refetchIntervalInBackground: true,
    retry: 2,
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

  const handleExportStatus = () => {
    const data = {
      timestamp: new Date().toISOString(),
      environments: environments.map(env => ({
        id: env.id,
        env_id: env.env_id,
        status: env.status,
        created_at: env.created_at,
        resource_config: env.resource_config,
        url: env.url,
      })),
      summary: stats,
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `environment-status-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Critical alerts based on failed environments
  const criticalAlerts = environments.filter(env => 
    env.status === 'failed'
  );

  if (error) {
    return (
      <Alert
        message="Failed to load monitoring data"
        description={error instanceof Error ? error.message : 'An unexpected error occurred'}
        type="error"
        showIcon
        action={
          <Button size="small" danger onClick={() => refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Critical Alerts */}
      {criticalAlerts.length > 0 && (
        <Alert
          banner
          type="error"
          icon={<ExclamationCircleOutlined />}
          message={
            <Space>
              <Text strong>Environment Alert</Text>
              <Badge count={criticalAlerts.length} />
              <Text>{criticalAlerts.length} environment(s) have failed and require attention</Text>
            </Space>
          }
          closable
        />
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <Title level={4} className="mb-0 flex items-center">
          <MonitorOutlined className="mr-2 text-blue-500" />
          Environment Monitoring
        </Title>
        <Space>
          <Switch 
            size="small"
            checked={autoRefresh}
            onChange={setAutoRefresh}
            checkedChildren="Live"
            unCheckedChildren="Paused"
          />
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Refresh
          </Button>
          <Button
            size="small"
            onClick={handleExportStatus}
          >
            Export Status
          </Button>
        </Space>
      </div>

      {/* Environment Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={6}>
          <Card size="small" className="text-center">
            <Statistic
              title="Total Environments"
              value={stats.total}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '24px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" className="text-center">
            <Statistic
              title="Running"
              value={stats.running}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '24px' }}
            />
            <Progress 
              percent={stats.total > 0 ? (stats.running / stats.total) * 100 : 0} 
              strokeColor="#52c41a"
              size="small"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" className="text-center">
            <Statistic
              title="Pending"
              value={stats.pending}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14', fontSize: '24px' }}
            />
            <Progress 
              percent={stats.total > 0 ? (stats.pending / stats.total) * 100 : 0} 
              strokeColor="#faad14"
              size="small"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" className="text-center">
            <Statistic
              title="Issues"
              value={stats.failed + stats.stopped}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: stats.failed > 0 ? '#ff4d4f' : '#8c8c8c', fontSize: '24px' }}
            />
            <Progress 
              percent={stats.total > 0 ? ((stats.failed + stats.stopped) / stats.total) * 100 : 0} 
              strokeColor={stats.failed > 0 ? "#ff4d4f" : "#8c8c8c"}
              size="small"
              showInfo={false}
            />
          </Card>
        </Col>
      </Row>

      {/* Environment Status Cards */}
      <Card title="Environment Status Overview" size="small" loading={isLoading}>
        {environments.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No environments to monitor"
          />
        ) : (
          <Row gutter={[12, 12]}>
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
    </div>
  );
}