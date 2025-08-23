'use client';

import React from 'react';
import {
  Card,
  Typography,
  Tag,
  Space,
  Button,
  Progress,
  Tooltip,
  Row,
  Col,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StopOutlined,
  DatabaseOutlined,
  BugOutlined,
} from '@ant-design/icons';
import type { Environment } from '@/types';

const { Text, Title } = Typography;

interface EnvironmentMonitoringCardProps {
  environment: Environment;
  onRefresh?: () => void;
}

export default function EnvironmentMonitoringCard({ 
  environment, 
  onRefresh 
}: EnvironmentMonitoringCardProps) {
  const formatDateTime = (dateString: string): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return dateString;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return <CheckCircleOutlined className="text-green-500" />;
      case 'pending':
        return <ClockCircleOutlined className="text-yellow-500" />;
      case 'failed':
        return <ExclamationCircleOutlined className="text-red-500" />;
      case 'stopped':
        return <StopOutlined className="text-gray-500" />;
      default:
        return <BugOutlined className="text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'stopped':
        return 'default';
      default:
        return 'default';
    }
  };

  const getCardBorderColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return '#52c41a';
      case 'pending':
        return '#faad14';
      case 'failed':
        return '#ff4d4f';
      case 'stopped':
        return '#d9d9d9';
      default:
        return '#d9d9d9';
    }
  };

  // Mock resource usage data (in a real implementation, this would come from metrics)
  const mockResourceUsage = {
    cpu: Math.floor(Math.random() * 100),
    memory: Math.floor(Math.random() * 100),
    storage: Math.floor(Math.random() * 100),
  };

  const displayId = environment.env_id?.substring(0, 8) || environment.id?.substring(0, 8) || 'unknown';
  const resourceConfig = environment.resource_config;

  return (
    <Card
      size="small"
      className="transition-all hover:shadow-md"
      style={{ borderLeft: `4px solid ${getCardBorderColor(environment.status)}` }}
      actions={[
        <Tooltip title="View Details" key="details">
          <Button 
            type="text" 
            size="small"
            icon={<DatabaseOutlined />}
            onClick={() => window.open(environment.url, '_blank')}
            disabled={!environment.url}
          />
        </Tooltip>,
        <Tooltip title="Refresh Status" key="refresh">
          <Button 
            type="text" 
            size="small"
            icon={<ReloadOutlined />}
            onClick={onRefresh}
          />
        </Tooltip>,
      ]}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon(environment.status)}
          <Title level={5} className="mb-0">
            {displayId}
          </Title>
        </div>
        <Tag color={getStatusColor(environment.status)} className="mb-0">
          {environment.status.toUpperCase()}
        </Tag>
      </div>

      {/* Environment Info */}
      <div className="space-y-2 mb-3">
        <div className="flex justify-between text-sm">
          <Text type="secondary">Created:</Text>
          <Text className="font-mono text-xs">
            {formatDateTime(environment.created_at)}
          </Text>
        </div>
        
        {environment.last_activity && (
          <div className="flex justify-between text-sm">
            <Text type="secondary">Last Activity:</Text>
            <Text className="font-mono text-xs">
              {formatDateTime(environment.last_activity)}
            </Text>
          </div>
        )}

        {environment.url && (
          <div className="flex justify-between text-sm">
            <Text type="secondary">Status:</Text>
            <Text 
              className="text-blue-600 cursor-pointer hover:underline text-xs"
              onClick={() => window.open(environment.url, '_blank')}
            >
              Access Environment
            </Text>
          </div>
        )}
      </div>

      {/* Resource Configuration */}
      {resourceConfig && (
        <div className="mb-3">
          <Text type="secondary" className="text-xs block mb-2">Resource Allocation:</Text>
          <Row gutter={8}>
            <Col span={8}>
              <div className="text-center">
                <Text className="text-xs block">CPU</Text>
                <Text strong className="text-sm">
                  {resourceConfig.cpu_limit || 'N/A'}
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div className="text-center">
                <Text className="text-xs block">Memory</Text>
                <Text strong className="text-sm">
                  {resourceConfig.memory_limit || 'N/A'}
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div className="text-center">
                <Text className="text-xs block">Storage</Text>
                <Text strong className="text-sm">
                  {resourceConfig.storage_size || 'N/A'}
                </Text>
              </div>
            </Col>
          </Row>
        </div>
      )}

      {/* Resource Usage (Mock Data) */}
      {environment.status === 'running' && (
        <div className="space-y-2">
          <Text type="secondary" className="text-xs block">Current Usage:</Text>
          
          <div>
            <div className="flex justify-between text-xs mb-1">
              <Text>CPU</Text>
              <Text>{mockResourceUsage.cpu}%</Text>
            </div>
            <Progress 
              percent={mockResourceUsage.cpu} 
              size="small" 
              strokeColor={mockResourceUsage.cpu > 80 ? '#ff4d4f' : '#52c41a'}
              showInfo={false}
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <Text>Memory</Text>
              <Text>{mockResourceUsage.memory}%</Text>
            </div>
            <Progress 
              percent={mockResourceUsage.memory} 
              size="small"
              strokeColor={mockResourceUsage.memory > 80 ? '#ff4d4f' : '#52c41a'}
              showInfo={false}
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <Text>Storage</Text>
              <Text>{mockResourceUsage.storage}%</Text>
            </div>
            <Progress 
              percent={mockResourceUsage.storage} 
              size="small"
              strokeColor={mockResourceUsage.storage > 80 ? '#ff4d4f' : '#52c41a'}
              showInfo={false}
            />
          </div>
        </div>
      )}

      {/* Alert Indicators */}
      {environment.status === 'running' && (
        mockResourceUsage.cpu > 90 || mockResourceUsage.memory > 90
      ) && (
        <div className="mt-3 p-2 bg-red-50 rounded border border-red-200">
          <div className="flex items-center space-x-1">
            <ExclamationCircleOutlined className="text-red-500 text-xs" />
            <Text className="text-red-600 text-xs">
              High resource usage detected
            </Text>
          </div>
        </div>
      )}

      {environment.status === 'failed' && (
        <div className="mt-3 p-2 bg-red-50 rounded border border-red-200">
          <div className="flex items-center space-x-1">
            <ExclamationCircleOutlined className="text-red-500 text-xs" />
            <Text className="text-red-600 text-xs">
              Environment requires attention
            </Text>
          </div>
        </div>
      )}
    </Card>
  );
}
