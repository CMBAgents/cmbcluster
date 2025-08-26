'use client';

import { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Statistic, 
  Alert,
  Tabs,
  Descriptions,
  Badge,
  Divider,
  Progress,
  Spin,
  Empty,
  Tag
} from 'antd';
import { 
  ArrowLeftOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
  RedoOutlined,
  LinkOutlined,
  MonitorOutlined,
  SettingOutlined,
  FileTextOutlined,
  EnvironmentOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Environment } from '@/types';
import { apiClient } from '@/lib/api-client';
import { formatDateTime, getStatusColor, capitalize, getDisplayId } from '@/lib/utils';

const { Title, Text } = Typography;

interface EnvironmentDetailsProps {
  envId: string;
}

export default function EnvironmentDetails({ envId }: EnvironmentDetailsProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const queryClient = useQueryClient();

  // Fetch environment details
  const { 
    data: environment, 
    isLoading, 
    error,
    refetch 
  } = useQuery({
    queryKey: ['environment', envId],
    queryFn: async () => {
      try {
        console.log('Fetching environment details for ID:', envId);
        const response = await apiClient.getEnvironmentById(envId);
        console.log('Environment details API response:', response);
        return response.environment || response.data || response;
      } catch (error) {
        console.error('Failed to fetch environment details:', error);
        throw error;
      }
    },
    refetchInterval: 15000, // Refresh every 15 seconds
    refetchIntervalInBackground: true,
    retry: 3,
    retryDelay: 1000,
  });

  // Restart environment mutation
  const restartMutation = useMutation({
    mutationFn: async () => {
      return await apiClient.restartEnvironment(envId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment', envId] });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    }
  });

  // Stop environment mutation
  const stopMutation = useMutation({
    mutationFn: async () => {
      return await apiClient.stopEnvironment(envId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment', envId] });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    }
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (error || !environment) {
    return (
      <Alert
        message="Environment Not Found"
        description="The environment could not be found or you don't have access to it."
        type="error"
        showIcon
        action={
          <Button onClick={() => window.history.back()}>
            Go Back
          </Button>
        }
      />
    );
  }

  const statusConfig = {
    running: { color: 'success', text: 'Running' },
    pending: { color: 'processing', text: 'Starting' },
    failed: { color: 'error', text: 'Failed' },
    stopped: { color: 'default', text: 'Stopped' },
  };

  // Handle both direct environment object and wrapped response
  const envData = environment && 'environment' in environment ? environment.environment : environment;
  const status = statusConfig[envData?.status as keyof typeof statusConfig] || statusConfig.stopped;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => window.history.back()}
          >
            Back
          </Button>
          <div>
            <Title level={2} className="mb-1">
              Environment {getDisplayId(envData?.env_id || envData?.id)}
            </Title>
            <Space>
              <Badge status={status.color as any} text={status.text} />
              <Text type="secondary">•</Text>
              <Text type="secondary">
                Created {formatDateTime(envData?.created_at)}
              </Text>
            </Space>
          </div>
        </div>
        
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Refresh
          </Button>
          
          {envData?.url && (
            <Button
              type="primary"
              icon={<LinkOutlined />}
              href={envData?.url}
              target="_blank"
            >
              Access Environment
            </Button>
          )}
          
          <Button
            icon={<RedoOutlined />}
            onClick={() => restartMutation.mutate()}
            loading={restartMutation.isPending}
          >
            Restart
          </Button>
          
          <Button
            icon={<StopOutlined />}
            danger
            onClick={() => stopMutation.mutate()}
            loading={stopMutation.isPending}
          >
            Stop
          </Button>
        </Space>
      </div>

      {/* Environment Details Tabs */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane 
          tab={<span><MonitorOutlined /> Overview</span>} 
          key="overview"
        >
          <EnvironmentOverview environment={envData} />
        </Tabs.TabPane>
        
        <Tabs.TabPane 
          tab={<span><FileTextOutlined /> Logs</span>} 
          key="logs"
        >
          <EnvironmentLogs envId={envId} />
        </Tabs.TabPane>
        
        <Tabs.TabPane 
          tab={<span><SettingOutlined /> Configuration</span>} 
          key="configuration"
        >
          <EnvironmentConfiguration environment={envData} />
        </Tabs.TabPane>
        
        <Tabs.TabPane 
          tab={<span><EnvironmentOutlined /> Variables</span>} 
          key="variables"
        >
          <EnvironmentVariables envId={envId} />
        </Tabs.TabPane>
        
        <Tabs.TabPane 
          tab={<span><MonitorOutlined /> Monitoring</span>} 
          key="monitoring"
        >
          <EnvironmentMonitoring environment={environment} />
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}

// Environment Overview Component
interface EnvironmentOverviewProps {
  environment: Environment;
}

function EnvironmentOverview({ environment }: EnvironmentOverviewProps) {
  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Status"
              value={capitalize(envData?.status || 'unknown')}
              valueStyle={{ 
                color: envData?.status === 'running' ? '#52c41a' : 
                       envData?.status === 'pending' ? '#faad14' : '#f5222d' 
              }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Uptime"
              value={envData?.created_at ? 
                Math.floor((Date.now() - new Date(envData.created_at).getTime()) / (1000 * 60 * 60 * 24)) 
                : 0}
              suffix="days"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU Cores"
              value={envData?.resource_config?.cpu_limit || 'N/A'}
              suffix={envData?.resource_config?.cpu_limit ? 'cores' : ''}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Memory"
              value={envData?.resource_config?.memory_limit || 'N/A'}
            />
          </Card>
        </Col>
      </Row>

      {/* Environment Information */}
      <Card title="Environment Information">
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Environment ID">
            <Text code>{envData?.env_id || envData?.id}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Display ID">
            <Text code>{getDisplayId(envData?.env_id || envData?.id)}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <Badge 
              status={envData?.status === 'running' ? 'success' : 
                     envData?.status === 'pending' ? 'processing' : 'error'} 
              text={capitalize(envData?.status || 'unknown')} 
            />
          </Descriptions.Item>
          <Descriptions.Item label="Created">
            {formatDateTime(envData?.created_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Last Activity">
            {formatDateTime(envData?.last_activity || envData?.updated_at)}
          </Descriptions.Item>
          <Descriptions.Item label="Access URL">
            {envData?.url ? (
              <a href={envData.url} target="_blank" rel="noopener noreferrer">
                {envData.url}
              </a>
            ) : 'Not available'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Resource Configuration */}
      {envData?.resource_config && (
        <Card title="Resource Configuration">
          <Row gutter={16}>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="CPU Allocation"
                  value={envData.resource_config.cpu_limit}
                  suffix="cores"
                  precision={1}
                />
                <Progress 
                  percent={75} 
                  size="small" 
                  format={() => '75% used'}
                  className="mt-2"
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="Memory Allocation"
                  value={envData.resource_config.memory_limit}
                />
                <Progress 
                  percent={60} 
                  size="small" 
                  format={() => '60% used'}
                  className="mt-2"
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="Storage Allocation"
                  value={envData.resource_config.storage_size}
                />
                <Progress 
                  percent={45} 
                  size="small" 
                  format={() => '45% used'}
                  className="mt-2"
                />
              </Card>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
}

// Environment Logs Component
interface EnvironmentLogsProps {
  envId: string;
}

function EnvironmentLogs({ envId }: EnvironmentLogsProps) {
  const [logs, setLogs] = useState<string[]>([
    '[2024-08-23 10:30:15] Environment initialization started',
    '[2024-08-23 10:30:20] Allocating resources...',
    '[2024-08-23 10:30:25] Setting up networking...',
    '[2024-08-23 10:30:30] Installing dependencies...',
    '[2024-08-23 10:30:45] Environment ready for use',
  ]);

  return (
    <Card title="Environment Logs" 
          extra={
            <Space>
              <Button size="small" icon={<ReloadOutlined />}>
                Refresh
              </Button>
              <Button size="small">
                Download
              </Button>
            </Space>
          }
    >
      <div className="bg-black text-green-400 p-4 rounded font-mono text-sm max-h-96 overflow-y-auto">
        {logs.map((log, index) => (
          <div key={index} className="mb-1">
            {log}
          </div>
        ))}
      </div>
    </Card>
  );
}

// Environment Configuration Component
interface EnvironmentConfigurationProps {
  environment: Environment;
}

function EnvironmentConfiguration({ environment }: EnvironmentConfigurationProps) {
  return (
    <div className="space-y-6">
      <Card title="Current Configuration">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Environment ID">
            {envData?.env_id || envData?.id}
          </Descriptions.Item>
          <Descriptions.Item label="CPU Limit">
            {envData?.resource_config?.cpu_limit || 'Not configured'} cores
          </Descriptions.Item>
          <Descriptions.Item label="Memory Limit">
            {envData?.resource_config?.memory_limit || 'Not configured'}
          </Descriptions.Item>
          <Descriptions.Item label="Storage Size">
            {envData?.resource_config?.storage_size || 'Not configured'}
          </Descriptions.Item>
          <Descriptions.Item label="Access URL">
            {envData?.url || 'Not available'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Network Settings">
        <Empty description="Network configuration will be displayed here" />
      </Card>

      <Card title="Security Settings">
        <Empty description="Security configuration will be displayed here" />
      </Card>
    </div>
  );
}

// Environment Variables Component
interface EnvironmentVariablesProps {
  envId: string;
}

function EnvironmentVariables({ envId }: EnvironmentVariablesProps) {
  const mockEnvVars = [
    { key: 'PYTHON_PATH', value: '/usr/local/bin/python3' },
    { key: 'NODE_ENV', value: 'production' },
    { key: 'DATABASE_URL', value: '***hidden***' },
  ];

  return (
    <Card title="Environment Variables"
          extra={
            <Button type="primary" size="small">
              Add Variable
            </Button>
          }
    >
      <div className="space-y-2">
        {mockEnvVars.map((envVar, index) => (
          <div key={index} className="flex justify-between items-center p-3 border rounded">
            <div>
              <Text strong>{envVar.key}</Text>
              <Text type="secondary" className="ml-4">=</Text>
              <Text code className="ml-2">{envVar.value}</Text>
            </div>
            <Space>
              <Button size="small">Edit</Button>
              <Button size="small" danger>Delete</Button>
            </Space>
          </div>
        ))}
      </div>
    </Card>
  );
}

// Environment Monitoring Component  
interface EnvironmentMonitoringProps {
  environment: Environment;
}

function EnvironmentMonitoring({ environment }: EnvironmentMonitoringProps) {
  return (
    <div className="space-y-6">
      <Row gutter={16}>
        <Col span={12}>
          <Card title="CPU Usage">
            <div className="text-center">
              <Progress
                type="circle"
                percent={75}
                format={() => '75%'}
                strokeColor="#52c41a"
              />
              <div className="mt-4">
                <Text type="secondary">Current: 1.5 / 2.0 cores</Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Memory Usage">
            <div className="text-center">
              <Progress
                type="circle"
                percent={60}
                format={() => '60%'}
                strokeColor="#1890ff"
              />
              <div className="mt-4">
                <Text type="secondary">Current: 2.4GB / 4GB</Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="Storage Usage">
        <Progress
          percent={45}
          strokeColor="#faad14"
          format={() => '22.5GB / 50GB used'}
        />
      </Card>

      <Card title="Network Activity">
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="Inbound Traffic"
              value={1234.56}
              suffix="MB"
              precision={2}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="Outbound Traffic"
              value={567.89}
              suffix="MB" 
              precision={2}
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
}
