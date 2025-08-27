'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Space, Button, Alert, Spin } from 'antd';
import {
  RocketOutlined,
  DatabaseOutlined,
  CloudOutlined,
  UserOutlined,
  PlayCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import apiClient from '@/lib/api-client';
import { Environment, StorageItem } from '@/types';


const { Title, Text, Paragraph } = Typography;

export default function DashboardPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [storages, setStorages] = useState<StorageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!session) return;
      
      try {
        setLoading(true);
        
        const [envResponse, storageResponse] = await Promise.all([
          apiClient.listEnvironments(),
          apiClient.listUserStorages()
        ]);

        console.log('Dashboard envResponse:', envResponse);
        console.log('Dashboard storageResponse:', storageResponse);

        // Handle environment response - now properly structured
        if (envResponse.status === 'success' && envResponse.environments) {
          setEnvironments(envResponse.environments);
        }

        // Handle storage response - now properly structured
        if (storageResponse.status === 'success' && storageResponse.storages) {
          setStorages(storageResponse.storages);
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError(error instanceof Error ? error.message : 'Failed to load dashboard data');
        // Set empty arrays as fallback to prevent UI issues
        setEnvironments([]);
        setStorages([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [session]);

  // Calculate statistics from real data
  const stats = [
    {
      title: 'Total Environments',
      value: environments.length,
      icon: <RocketOutlined className="text-primary" />,
      color: '#4A9EFF',
    },
    {
      title: 'Running Environments',
      value: environments.filter(env => env.status === 'running').length,
      icon: <PlayCircleOutlined className="text-green-500" />,
      color: '#52c41a',
    },
    {
      title: 'Storage Workspaces',
      value: storages.length,
      icon: <DatabaseOutlined className="text-blue-500" />,
      color: '#1890ff',
    },
    {
      title: 'Active User',
      value: session?.user ? 1 : 0,
      icon: <UserOutlined className="text-purple-500" />,
      color: '#722ed1',
    },
  ];

  const quickActions = [
    {
      title: 'Launch Environment',
      description: 'Start a new computational environment',
      icon: <PlayCircleOutlined />,
      action: '/environments',
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

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <Spin size="large" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <Alert
          message="Dashboard Loading Error"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              Retry
            </Button>
          }
        />
      </MainLayout>
    );
  }

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
                  onClick={() => router.push(action.action)}
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

        {/* Professional Activity Feed */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card className="glass-card" title={
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Recent Activity
                </h3>
                <Button type="link" size="small" style={{ color: 'var(--interactive-primary)' }}>
                  View All
                </Button>
              </div>
            }>
              {recentActivity.length > 0 ? (
                <Timeline className="mt-4">
                  {recentActivity.map((activity, index) => (
                    <Timeline.Item key={index} dot={activity.icon}>
                      <div className="pb-4">
                        <div className="flex items-start justify-between mb-1">
                          <h4 className="font-medium" style={{ color: 'var(--text-primary)' }}>
                            {activity.title}
                          </h4>
                          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            {activity.time}
                          </span>
                        </div>
                        <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>
                          {activity.description}
                        </p>
                        <code className="text-xs px-2 py-1 rounded" style={{ 
                          background: 'var(--bg-tertiary)', 
                          color: 'var(--text-muted)' 
                        }}>
                          {activity.id}
                        </code>
                      </div>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <div className="empty-state py-8">
                  <div className="empty-state-icon">
                    <ClockCircleOutlined />
                  </div>
                  <h3>No Recent Activity</h3>
                  <p>
                    Your activity will appear here once you start using the platform.
                    Try launching an environment or uploading some files to get started.
                  </p>
                  <Button type="primary" onClick={() => router.push('/environments')}>
                    Launch Your First Environment
                  </Button>
                </div>
              )}
            </Card>
          </Col>
          
          <Col xs={24} lg={8}>
            <Card className="glass-card mb-6" title={
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Quick Stats
              </h3>
            }>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>CPU Usage</span>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>23%</span>
                </div>
                <Progress percent={23} strokeColor="var(--success-500)" showInfo={false} />
                
                <div className="flex justify-between items-center">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Memory</span>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>67%</span>
                </div>
                <Progress percent={67} strokeColor="var(--warning-500)" showInfo={false} />
                
                <div className="flex justify-between items-center">
                  <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Storage</span>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>41%</span>
                </div>
                <Progress percent={41} strokeColor="var(--info-500)" showInfo={false} />
              </div>
            </Card>
            
            <Card className="glass-card" title={
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Platform Tips
              </h3>
            }>
              <div className="space-y-3">
                <div className="p-3 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                  <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                    Pro Tip
                  </p>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    Use templates to quickly launch pre-configured environments for your research projects.
                  </p>
                </div>
                <Button type="link" size="small" style={{ color: 'var(--interactive-primary)', padding: 0 }}>
                  Learn More
                </Button>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </MainLayout>
  );
}
