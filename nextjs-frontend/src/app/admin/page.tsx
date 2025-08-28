'use client';

import MainLayout from '@/components/layout/MainLayout';
import { useAdmin } from '@/contexts/AdminContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Space, Button, Alert } from 'antd';
import {
  CrownOutlined,
  UsergroupAddOutlined,
  AppstoreOutlined,
  SettingOutlined,
  DashboardOutlined,
  FileTextOutlined,
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

function AdminDashboardContent() {
  const { currentRole, canSwitchToAdmin } = useAdmin();
  const router = useRouter();

  // Redirect if not in admin mode
  useEffect(() => {
    if (!canSwitchToAdmin || currentRole !== 'admin') {
      router.push('/');
    }
  }, [canSwitchToAdmin, currentRole, router]);

  // Don't render if not admin
  if (!canSwitchToAdmin || currentRole !== 'admin') {
    return null;
  }

  const adminStats = [
    {
      title: 'Total Users',
      value: 0, // Will be populated from API
      icon: <UsergroupAddOutlined className="text-primary" />,
      color: 'var(--primary-500)',
    },
    {
      title: 'Applications',
      value: 0, // Will be populated from API
      icon: <AppstoreOutlined className="text-success" />,
      color: 'var(--success-500)',
    },
    {
      title: 'Active Environments',
      value: 0, // Will be populated from API
      icon: <DashboardOutlined className="text-warning" />,
      color: 'var(--warning-500)',
    },
    {
      title: 'System Health',
      value: '100%',
      icon: <SettingOutlined className="text-info" />,
      color: 'var(--info-500)',
    },
  ];

  const quickActions = [
    {
      title: 'User Management',
      description: 'Manage user roles and permissions',
      icon: <UsergroupAddOutlined className="text-primary" />,
      action: '/admin/users',
      className: 'glass-card hover:shadow-lg transition-all',
    },
    {
      title: 'Application Manager',
      description: 'Add and manage container images',
      icon: <AppstoreOutlined className="text-success" />,
      action: '/admin/applications',
      className: 'glass-card hover:shadow-lg transition-all',
    },
    {
      title: 'System Monitoring',
      description: 'Monitor system performance and logs',
      icon: <DashboardOutlined className="text-warning" />,
      action: '/admin/monitoring',
      className: 'glass-card hover:shadow-lg transition-all',
    },
    {
      title: 'Audit Logs',
      description: 'View system and user activity logs',
      icon: <FileTextOutlined className="text-info" />,
      action: '/admin/audit',
      className: 'glass-card hover:shadow-lg transition-all',
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Admin Header */}
        <div className="glass-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="icon-container primary p-3">
              <CrownOutlined className="text-2xl text-primary" />
            </div>
            <div>
              <Title level={2} className="text-primary m-0">
                Admin Dashboard
              </Title>
              <Paragraph className="text-secondary text-lg m-0">
                System administration and management panel
              </Paragraph>
            </div>
          </div>

          <Alert
            message="Admin Mode Active"
            description="You are currently in administrator mode with full system access. Use these tools responsibly."
            type="info"
            showIcon
            className="glass-card"
          />
        </div>

        {/* Admin Statistics */}
        <Row gutter={[24, 24]}>
          {adminStats.map((stat, index) => (
            <Col xs={24} sm={12} md={6} key={index}>
              <Card className="glass-card text-center">
                <Statistic
                  title={
                    <span className="text-secondary font-medium">
                      {stat.title}
                    </span>
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
          <Title level={3} className="text-primary mb-4">
            Admin Tools
          </Title>
          <Row gutter={[24, 24]}>
            {quickActions.map((action, index) => (
              <Col xs={24} sm={12} md={6} key={index}>
                <Card
                  className={action.className}
                  bodyStyle={{ padding: '24px' }}
                  hoverable
                  onClick={() => router.push(action.action)}
                >
                  <Space direction="vertical" size={16} className="w-full text-center">
                    <div className="text-4xl">
                      {action.icon}
                    </div>
                    <div>
                      <Title level={4} className="text-primary mb-2">
                        {action.title}
                      </Title>
                      <Paragraph className="text-secondary m-0">
                        {action.description}
                      </Paragraph>
                    </div>
                    <Button type="primary" className="mt-auto">
                      Open
                    </Button>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </div>

        {/* Recent Activity */}
        <div>
          <Title level={3} className="text-primary mb-4">
            Recent Admin Activity
          </Title>
          <Card className="glass-card">
            <div className="text-center py-8">
              <Paragraph className="text-secondary">
                No recent admin activity to display. Admin actions will appear here.
              </Paragraph>
            </div>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}

export default function AdminDashboard() {
  return <AdminDashboardContent />;
}
