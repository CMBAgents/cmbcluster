'use client';

import { useSession } from 'next-auth/react';
import { Card, Row, Col, Statistic, Typography, Space, Button, Alert } from 'antd';
import {
  RocketOutlined,
  DatabaseOutlined,
  CloudOutlined,
  UserOutlined,
  PlayCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';

const { Title, Text, Paragraph } = Typography;

export default function DashboardPage() {
  const { data: session } = useSession();

  // Placeholder statistics - these would come from your API
  const stats = [
    {
      title: 'Active Environments',
      value: 3,
      icon: <RocketOutlined className="text-primary" />,
      color: '#4A9EFF',
    },
    {
      title: 'Storage Usage',
      value: '2.3 GB',
      icon: <DatabaseOutlined className="text-green-500" />,
      color: '#52c41a',
    },
    {
      title: 'CPU Usage',
      value: '45%',
      icon: <CloudOutlined className="text-orange-500" />,
      color: '#fa8c16',
    },
    {
      title: 'Active Sessions',
      value: 1,
      icon: <UserOutlined className="text-purple-500" />,
      color: '#722ed1',
    },
  ];

  const quickActions = [
    {
      title: 'Launch Environment',
      description: 'Start a new computational environment',
      icon: <PlayCircleOutlined />,
      action: '/environments/new',
    },
    {
      title: 'Manage Storage',
      description: 'Upload, download, and organize files',
      icon: <DatabaseOutlined />,
      action: '/storage',
    },
    {
      title: 'System Settings',
      description: 'Configure platform preferences',
      icon: <SettingOutlined />,
      action: '/settings',
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="mb-8">
          <Title level={2} className="text-text-primary mb-2">
            Welcome back, {session?.user?.name?.split(' ')[0] || 'User'}! 👋
          </Title>
          <Paragraph className="text-text-secondary text-lg">
            Here's an overview of your CMBAgent Cloud platform. Monitor your environments, 
            manage storage, and access powerful computational resources.
          </Paragraph>
        </div>

        {/* Platform Status Alert */}
        <Alert
          message="Platform Status: All Systems Operational"
          description="All services are running normally. Last updated: Just now"
          type="success"
          showIcon
          className="mb-6"
        />

        {/* Statistics Cards */}
        <Row gutter={[24, 24]} className="mb-8">
          {stats.map((stat, index) => (
            <Col xs={24} sm={12} md={6} key={index}>
              <Card
                className="bg-background-secondary border-border-primary hover:shadow-lg transition-shadow"
                bodyStyle={{ padding: '24px' }}
              >
                <Statistic
                  title={
                    <Text className="text-text-secondary font-medium">
                      {stat.title}
                    </Text>
                  }
                  value={stat.value}
                  prefix={stat.icon}
                  valueStyle={{
                    color: stat.color,
                    fontSize: '28px',
                    fontWeight: 'bold',
                  }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        {/* Quick Actions */}
        <div>
          <Title level={3} className="text-text-primary mb-4">
            Quick Actions
          </Title>
          <Row gutter={[24, 24]}>
            {quickActions.map((action, index) => (
              <Col xs={24} sm={12} md={8} key={index}>
                <Card
                  className="bg-background-secondary border-border-primary hover:shadow-lg transition-all hover:border-primary cursor-pointer h-full"
                  bodyStyle={{ padding: '24px' }}
                  onClick={() => window.location.href = action.action}
                >
                  <Space direction="vertical" size={16} className="w-full">
                    <div className="text-primary text-3xl">
                      {action.icon}
                    </div>
                    <div>
                      <Title level={4} className="text-text-primary mb-2">
                        {action.title}
                      </Title>
                      <Text className="text-text-secondary">
                        {action.description}
                      </Text>
                    </div>
                    <Button type="primary" className="mt-auto">
                      Get Started
                    </Button>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </div>

        {/* Recent Activity Section */}
        <div>
          <Title level={3} className="text-text-primary mb-4">
            Recent Activity
          </Title>
          <Card className="bg-background-secondary border-border-primary">
            <div className="text-center py-8">
              <Text className="text-text-secondary">
                No recent activity to display. Start by launching an environment or uploading files.
              </Text>
            </div>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
