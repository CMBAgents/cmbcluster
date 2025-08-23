'use client';

import { Card, Typography, Button, Space } from 'antd';
import { MonitorOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export default function EnvironmentMonitoring() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={3} className="mb-1">Environment Monitoring</Title>
          <Text type="secondary">
            Monitor your research environment status and performance
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />}>
            Refresh Status
          </Button>
        </Space>
      </div>

      {/* Content */}
      <Card>
        <div className="text-center py-12">
          <MonitorOutlined style={{ fontSize: 48, color: '#718096', marginBottom: 16 }} />
          <Title level={4} type="secondary">Environment Monitoring</Title>
          <Text type="secondary">
            Real-time monitoring and performance metrics will be displayed here.
            This includes resource usage, logs, and environment health status.
          </Text>
        </div>
      </Card>
    </div>
  );
}
