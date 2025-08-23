'use client';

import { Card, Typography, Button, Space } from 'antd';
import { DatabaseOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export default function StorageManagement() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={3} className="mb-1">Storage Management</Title>
          <Text type="secondary">
            Manage your workspace storage buckets
          </Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />}>
            Refresh
          </Button>
          <Button type="primary" icon={<DatabaseOutlined />}>
            Create Storage
          </Button>
        </Space>
      </div>

      {/* Content */}
      <Card>
        <div className="text-center py-12">
          <DatabaseOutlined style={{ fontSize: 48, color: '#718096', marginBottom: 16 }} />
          <Title level={4} type="secondary">Storage Management</Title>
          <Text type="secondary">
            Storage management functionality will be implemented here.
            This will include creating, managing, and accessing workspace storage buckets.
          </Text>
        </div>
      </Card>
    </div>
  );
}
