'use client';

import MainLayout from '@/components/layout/MainLayout';
import { useAdmin } from '@/contexts/AdminContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Typography, 
  Space, 
  Table,
  Alert,
  Progress,
  Tag
} from 'antd';
import {
  MonitorOutlined,
  ServerOutlined,
  UserOutlined,
  RocketOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Title } = Typography;

function SystemMonitoringContent() {
  const { currentRole, canSwitchToAdmin } = useAdmin();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [systemStats, setSystemStats] = useState({
    totalUsers: 0,
    activeEnvironments: 0,
    totalStorage: '0GB',
    cpuUsage: 0,
    memoryUsage: 0
  });

  // Redirect if not admin
  useEffect(() => {
    if (!canSwitchToAdmin || currentRole !== 'admin') {
      router.push('/');
      return;
    }
  }, [canSwitchToAdmin, currentRole, router]);

  // Mock data
  useEffect(() => {
    setTimeout(() => {
      setSystemStats({
        totalUsers: 24,
        activeEnvironments: 7,
        totalStorage: '250GB',
        cpuUsage: 65,
        memoryUsage: 78
      });
      setLoading(false);
    }, 1000);
  }, []);

  const recentActivity = [
    {
      key: '1',
      user: 'user@example.com',
      action: 'Created Environment',
      resource: 'jupyter-env-001',
      timestamp: '2 minutes ago',
      status: 'success'
    },
    {
      key: '2',
      user: '22yash.tiwari@gmail.com',
      action: 'Deleted Environment',
      resource: 'tensorflow-env-005',
      timestamp: '15 minutes ago',
      status: 'success'
    },
    {
      key: '3',
      user: 'researcher@example.com',
      action: 'Environment Failed',
      resource: 'pytorch-env-003',
      timestamp: '1 hour ago',
      status: 'error'
    }
  ];

  const activityColumns = [
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user'
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action'
    },
    {
      title: 'Resource',
      dataIndex: 'resource',
      key: 'resource',
      render: (text: string) => <code className="bg-gray-100 px-2 py-1 rounded">{text}</code>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => (
        <Space>
          <ClockCircleOutlined />
          {text}
        </Space>
      )
    }
  ];

  if (!canSwitchToAdmin || currentRole !== 'admin') {
    return null; // Will redirect
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>
          <MonitorOutlined className="mr-2" />
          System Monitoring
        </Title>
      </div>

      <Alert
        message="System Overview"
        description="Monitor system performance, user activity, and resource usage across the CMBCluster platform."
        type="info"
        showIcon
        className="mb-6"
      />

      {/* System Statistics */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Total Users"
              value={systemStats.totalUsers}
              prefix={<UserOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Active Environments"
              value={systemStats.activeEnvironments}
              prefix={<RocketOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="Storage Used"
              value={systemStats.totalStorage}
              prefix={<ServerOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="glass-card">
            <Statistic
              title="System Health"
              value="Good"
              valueStyle={{ color: '#52c41a' }}
              prefix={<MonitorOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* Resource Usage */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={12}>
          <Card title="CPU Usage" className="glass-card">
            <Progress
              percent={systemStats.cpuUsage}
              status={systemStats.cpuUsage > 80 ? 'exception' : 'active'}
              strokeColor={systemStats.cpuUsage > 80 ? '#ff4d4f' : '#1890ff'}
            />
            <p className="mt-2 text-gray-600">
              Current CPU utilization across all nodes
            </p>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Memory Usage" className="glass-card">
            <Progress
              percent={systemStats.memoryUsage}
              status={systemStats.memoryUsage > 85 ? 'exception' : 'active'}
              strokeColor={systemStats.memoryUsage > 85 ? '#ff4d4f' : '#52c41a'}
            />
            <p className="mt-2 text-gray-600">
              Current memory utilization across all nodes
            </p>
          </Card>
        </Col>
      </Row>

      {/* Recent Activity */}
      <Card title="Recent Activity" className="glass-card">
        <Table
          columns={activityColumns}
          dataSource={recentActivity}
          pagination={false}
          loading={loading}
          size="small"
        />
      </Card>
    </div>
  );
}

export default function SystemMonitoringPage() {
  return (
    <MainLayout>
      <SystemMonitoringContent />
    </MainLayout>
  );
}