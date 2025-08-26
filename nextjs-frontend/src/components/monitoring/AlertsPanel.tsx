'use client';

import React, { useMemo } from 'react';
import {
  Card,
  Alert,
  Typography,
  Space,
  Tag,
  Button,
  Row,
  Col,
  Badge,
  Empty,
} from 'antd';
import {
  ExclamationCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseOutlined,
  BellOutlined,
} from '@ant-design/icons';
import type { Environment } from '@/types';

const { Title, Text } = Typography;

interface AlertsPanelProps {
  environments: Environment[];
}

interface AlertItem {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  environmentId: string;
  environmentName: string;
  timestamp: Date;
  severity: 'high' | 'medium' | 'low';
}

export default function AlertsPanel({ environments }: AlertsPanelProps) {
  // Generate alerts based on environment states
  const alerts = useMemo<AlertItem[]>(() => {
    const alertList: AlertItem[] = [];
    
    environments.forEach((env) => {
      const envName = env.env_id?.substring(0, 8) || env.id?.substring(0, 8) || 'Unknown';
      
      // Failed environment alerts
      if (env.status === 'failed') {
        alertList.push({
          id: `${env.id}-failed`,
          type: 'error',
          title: 'Environment Failure',
          message: `Environment ${envName} has failed and requires immediate attention.`,
          environmentId: env.id,
          environmentName: envName,
          timestamp: new Date(),
          severity: 'high',
        });
      }
      
      // Long-running pending environments
      if (env.status === 'pending') {
        const createdAt = new Date(env.created_at);
        const now = new Date();
        const timeDiff = now.getTime() - createdAt.getTime();
        const minutesDiff = Math.floor(timeDiff / (1000 * 60));
        
        if (minutesDiff > 10) {
          alertList.push({
            id: `${env.id}-long-pending`,
            type: 'warning',
            title: 'Environment Delayed',
            message: `Environment ${envName} has been pending for ${minutesDiff} minutes. This may indicate a resource issue.`,
            environmentId: env.id,
            environmentName: envName,
            timestamp: new Date(),
            severity: 'medium',
          });
        }
      }
      
      // Mock resource usage alerts (in real implementation, these would come from actual metrics)
      if (env.status === 'running') {
        const mockCpuUsage = Math.floor(Math.random() * 100);
        const mockMemoryUsage = Math.floor(Math.random() * 100);
        
        if (mockCpuUsage > 90) {
          alertList.push({
            id: `${env.id}-high-cpu`,
            type: 'warning',
            title: 'High CPU Usage',
            message: `Environment ${envName} is experiencing high CPU usage (${mockCpuUsage}%). Consider scaling resources.`,
            environmentId: env.id,
            environmentName: envName,
            timestamp: new Date(),
            severity: 'medium',
          });
        }
        
        if (mockMemoryUsage > 85) {
          alertList.push({
            id: `${env.id}-high-memory`,
            type: 'warning',
            title: 'High Memory Usage',
            message: `Environment ${envName} is using ${mockMemoryUsage}% of available memory. Monitor for potential issues.`,
            environmentId: env.id,
            environmentName: envName,
            timestamp: new Date(),
            severity: 'medium',
          });
        }
      }
      
      // Long-running environment info
      if (env.status === 'running') {
        const createdAt = new Date(env.created_at);
        const now = new Date();
        const hoursDiff = Math.floor((now.getTime() - createdAt.getTime()) / (1000 * 60 * 60));
        
        if (hoursDiff > 24) {
          alertList.push({
            id: `${env.id}-long-running`,
            type: 'info',
            title: 'Long-Running Environment',
            message: `Environment ${envName} has been running for ${hoursDiff} hours. Consider if this is still needed to optimize costs.`,
            environmentId: env.id,
            environmentName: envName,
            timestamp: new Date(),
            severity: 'low',
          });
        }
      }
    });
    
    // Sort by severity and timestamp
    return alertList.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      if (severityOrder[a.severity] !== severityOrder[b.severity]) {
        return severityOrder[b.severity] - severityOrder[a.severity];
      }
      return b.timestamp.getTime() - a.timestamp.getTime();
    });
  }, [environments]);

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <ExclamationCircleOutlined className="text-red-500" />;
      case 'warning':
        return <WarningOutlined className="text-yellow-500" />;
      case 'info':
        return <InfoCircleOutlined className="text-blue-500" />;
      case 'success':
        return <CheckCircleOutlined className="text-green-500" />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'red';
      case 'medium':
        return 'orange';
      case 'low':
        return 'blue';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Alert statistics
  const alertStats = {
    total: alerts.length,
    error: alerts.filter(a => a.type === 'error').length,
    warning: alerts.filter(a => a.type === 'warning').length,
    info: alerts.filter(a => a.type === 'info').length,
  };

  if (alerts.length === 0) {
    return (
      <Card title={
        <Space>
          <CheckCircleOutlined className="text-green-500" />
          System Alerts
          <Badge count={0} showZero />
        </Space>
      }>
        <Empty
          image={<CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />}
          description={
            <div>
              <Title level={5}>All Clear!</Title>
              <Text type="secondary">
                No alerts or issues detected with your environments.
              </Text>
            </div>
          }
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <BellOutlined className="text-blue-500" />
          System Alerts
          <Badge count={alertStats.total} />
        </Space>
      }
      extra={
        <Space>
          {alertStats.error > 0 && (
            <Tag color="red" className="px-2">
              {alertStats.error} Critical
            </Tag>
          )}
          {alertStats.warning > 0 && (
            <Tag color="orange" className="px-2">
              {alertStats.warning} Warning
            </Tag>
          )}
          {alertStats.info > 0 && (
            <Tag color="blue" className="px-2">
              {alertStats.info} Info
            </Tag>
          )}
        </Space>
      }
    >
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {alerts.map((alert) => (
          <Alert
            key={alert.id}
            type={alert.type}
            showIcon
            icon={getAlertIcon(alert.type)}
            message={
              <div className="flex justify-between items-start">
                <div>
                  <Space>
                    <Text strong>{alert.title}</Text>
                    <Tag color={getSeverityColor(alert.severity)}>
                      {alert.severity.toUpperCase()}
                    </Tag>
                    <Tag>
                      {alert.environmentName}
                    </Tag>
                  </Space>
                </div>
                <Text type="secondary" className="text-xs">
                  {formatTimestamp(alert.timestamp)}
                </Text>
              </div>
            }
            description={alert.message}
            action={
              <Space>
                <Button size="small" type="text" icon={<CloseOutlined />}>
                  Dismiss
                </Button>
              </Space>
            }
            className="mb-2"
          />
        ))}
      </div>

      {/* Alert Summary */}
      {alerts.length > 5 && (
        <div className="mt-4 pt-4 border-t">
          <Row gutter={16} className="text-center">
            <Col span={6}>
              <div>
                <Text strong className="block text-lg">{alertStats.total}</Text>
                <Text type="secondary" className="text-xs">Total Alerts</Text>
              </div>
            </Col>
            <Col span={6}>
              <div>
                <Text strong className="block text-lg text-red-500">{alertStats.error}</Text>
                <Text type="secondary" className="text-xs">Critical</Text>
              </div>
            </Col>
            <Col span={6}>
              <div>
                <Text strong className="block text-lg text-orange-500">{alertStats.warning}</Text>
                <Text type="secondary" className="text-xs">Warnings</Text>
              </div>
            </Col>
            <Col span={6}>
              <div>
                <Text strong className="block text-lg text-blue-500">{alertStats.info}</Text>
                <Text type="secondary" className="text-xs">Info</Text>
              </div>
            </Col>
          </Row>
        </div>
      )}
    </Card>
  );
}
