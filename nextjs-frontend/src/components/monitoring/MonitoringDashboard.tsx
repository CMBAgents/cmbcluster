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
    <div className="space-y-6">
      {/* Professional Critical Alerts */}
      {criticalAlerts.length > 0 && (
        <Alert
          message="Critical System Alert"
          description={`${criticalAlerts.length} environment${criticalAlerts.length > 1 ? 's have' : ' has'} failed and require immediate attention`}
          type="error"
          showIcon
          action={
            <Button size="small" danger onClick={() => refetch()}>
              Investigate
            </Button>
          }
          className="mb-6"
        />
      )}

      {/* Professional Header */}
      <div className="page-header">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="icon-container primary p-2">
                <MonitorOutlined style={{ fontSize: '18px' }} />
              </div>
              <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                Environment Monitoring
              </h2>
            </div>
            <p className="text-lg mb-4" style={{ color: 'var(--text-secondary)' }}>
              Real-time monitoring and health status of your computing environments
            </p>
            <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-tertiary)' }}>
              <span className="flex items-center gap-1">
                <div className={`status-indicator ${autoRefresh ? 'running' : 'stopped'}`}></div>
                {autoRefresh ? 'Live monitoring active' : 'Monitoring paused'}
              </span>
              <span>•</span>
              <span>Updates every {refreshInterval}s</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--glass-bg-secondary)' }}>
              <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Live Updates</span>
              <Switch 
                checked={autoRefresh}
                onChange={setAutoRefresh}
                size="small"
              />
            </div>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
              className="btn-secondary"
            >
              Refresh
            </Button>
            <Button
              onClick={handleExportStatus}
              className="btn-primary"
            >
              Export Status
            </Button>
          </div>
        </div>
      </div>

      {/* Professional Statistics Grid */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card" bodyStyle={{ padding: 0 }}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="icon-container primary p-3">
                  <CloudServerOutlined style={{ fontSize: '20px' }} />
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full text-primary-600 bg-primary-50">
                    Total
                  </span>
                </div>
              </div>
              <div className="mb-2">
                <h3 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {stats.total}
                </h3>
                <p className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Total Environments
                </p>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                Active monitoring targets
              </p>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card" bodyStyle={{ padding: 0 }}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="icon-container success p-3">
                  <CheckCircleOutlined style={{ fontSize: '20px' }} />
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full text-success-600 bg-success-50">
                    Healthy
                  </span>
                </div>
              </div>
              <div className="mb-2">
                <h3 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {stats.running}
                </h3>
                <p className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Running Now
                </p>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {stats.total > 0 ? Math.round((stats.running / stats.total) * 100) : 0}% uptime
              </p>
              <div className="mt-3">
                <Progress 
                  percent={stats.total > 0 ? (stats.running / stats.total) * 100 : 0}
                  showInfo={false}
                  strokeColor="var(--success-500)"
                  trailColor="var(--success-50)"
                  strokeWidth={4}
                />
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card" bodyStyle={{ padding: 0 }}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="icon-container warning p-3">
                  <ClockCircleOutlined style={{ fontSize: '20px' }} />
                </div>
                <div className="text-right">
                  {stats.pending > 0 && (
                    <span className="text-xs font-semibold px-2 py-1 rounded-full text-warning-600 bg-warning-50">
                      Starting
                    </span>
                  )}
                </div>
              </div>
              <div className="mb-2">
                <h3 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {stats.pending}
                </h3>
                <p className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Pending Launch
                </p>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {stats.pending > 0 ? 'Environments starting up' : 'All ready'}
              </p>
              <div className="mt-3">
                <Progress 
                  percent={stats.pending > 0 ? 75 : 0}
                  showInfo={false}
                  strokeColor="var(--warning-500)"
                  trailColor="var(--warning-50)"
                  strokeWidth={4}
                />
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card" bodyStyle={{ padding: 0 }}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className={`icon-container ${stats.failed > 0 ? 'error' : 'primary'} p-3`}>
                  <ExclamationCircleOutlined style={{ fontSize: '20px' }} />
                </div>
                <div className="text-right">
                  {stats.failed > 0 && (
                    <span className="text-xs font-semibold px-2 py-1 rounded-full text-error-600 bg-error-50">
                      Alert
                    </span>
                  )}
                </div>
              </div>
              <div className="mb-2">
                <h3 className="text-2xl font-bold mb-1" style={{ 
                  color: stats.failed > 0 ? 'var(--error-500)' : 'var(--text-primary)'
                }}>
                  {stats.failed + stats.stopped}
                </h3>
                <p className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Issues Found
                </p>
              </div>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {stats.failed > 0 ? 'Requires attention' : 'All systems normal'}
              </p>
              <div className="mt-3">
                <Progress 
                  percent={stats.total > 0 ? ((stats.failed + stats.stopped) / stats.total) * 100 : 0}
                  showInfo={false}
                  strokeColor={stats.failed > 0 ? "var(--error-500)" : "var(--neutral-400)"}
                  trailColor={stats.failed > 0 ? "var(--error-50)" : "var(--neutral-100)"}
                  strokeWidth={4}
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Professional Environment Status Overview */}
      <Card className="glass-card" loading={isLoading}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Environment Status Overview
            </h3>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Real-time health monitoring for all active environments
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <div className="status-indicator running"></div>
            <span>Live monitoring</span>
            <span className="mx-2">•</span>
            <span>Last update: Just now</span>
          </div>
        </div>
        
        {environments.length === 0 ? (
          <div className="empty-state py-12">
            <div className="empty-state-icon">
              <MonitorOutlined />
            </div>
            <h3>No Environments to Monitor</h3>
            <p>
              Launch your first environment to start monitoring its health and performance metrics.
            </p>
          </div>
        ) : (
          <Row gutter={[24, 24]}>
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