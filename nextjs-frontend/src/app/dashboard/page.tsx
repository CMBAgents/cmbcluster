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
        {/* Enhanced Professional Welcome Section */}
        <div className="mb-8">
          <div className="glass-card p-6" style={{
            background: 'var(--glass-bg-primary)',
            backdropFilter: 'blur(var(--glass-blur-medium))',
            WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
            border: '1px solid var(--glass-border)',
            borderRadius: 'var(--radius-2xl)',
            boxShadow: 'var(--glass-shadow)'
          }}>
            <div className="flex items-center gap-4 mb-4">
              <div className="glass-button p-3" style={{
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                WebkitBackdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-xl)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <RocketOutlined style={{ fontSize: '24px', color: 'var(--interactive-primary)' }} />
              </div>
              <div>
                <Title level={2} style={{ 
                  color: 'var(--text-primary)', 
                  margin: 0,
                  fontWeight: 'var(--font-semibold)',
                  textShadow: 'var(--text-shadow)'
                }}>
                  Welcome back, {session?.user?.name?.split(' ')[0] || 'User'}! 👋
                </Title>
                <Text style={{ 
                  color: 'var(--text-secondary)', 
                  fontSize: 'var(--text-lg)',
                  textShadow: 'var(--text-shadow-light)'
                }}>
                  Here's your CMBAgent Cloud platform overview
                </Text>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Professional Platform Status */}
        <Alert
          message="Platform Status: All Systems Operational"
          description="All services running normally • Last updated: Just now"
          type="success"
          showIcon
          className="glass-card mb-6"
          style={{
            background: 'var(--glass-bg-secondary)',
            backdropFilter: 'blur(var(--glass-blur-light))',
            WebkitBackdropFilter: 'blur(var(--glass-blur-light))',
            border: '1px solid var(--success-200)',
            borderRadius: 'var(--radius-2xl)',
            boxShadow: 'var(--glass-shadow)'
          }}
        />

        {/* Professional Statistics Cards */}
        <Row gutter={[24, 24]} className="mb-8">
          {stats.map((stat, index) => (
            <Col xs={24} sm={12} md={6} key={index}>
              <Card
                className="glass-card hover:shadow-lg transition-all duration-300"
                bodyStyle={{ padding: '32px' }}
                style={{
                  background: 'var(--glass-bg-primary)',
                  backdropFilter: 'blur(var(--glass-blur-medium))',
                  WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-2xl)',
                  cursor: 'pointer',
                  boxShadow: 'var(--glass-shadow)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                <div className="text-center">
                  <div className="mb-4 mx-auto w-16 h-16 rounded-full flex items-center justify-center" 
                       style={{ 
                         background: `${stat.color}15`, 
                         border: `1px solid ${stat.color}30` 
                       }}>
                    <span style={{ fontSize: '24px', color: stat.color }}>
                      {stat.icon}
                    </span>
                  </div>
                  <Statistic
                    title={
                      <Text style={{ 
                        color: 'var(--text-muted)', 
                        fontSize: 'var(--text-sm)',
                        fontWeight: 'var(--font-medium)'
                      }}>
                        {stat.title}
                      </Text>
                    }
                    value={stat.value}
                    valueStyle={{
                      color: 'var(--text-primary)',
                      fontSize: '36px',
                      fontWeight: 'var(--font-bold)',
                      lineHeight: 1
                    }}
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>

        {/* Professional Quick Actions */}
        <div className="mb-8">
          <Title level={3} style={{ 
            color: 'var(--text-primary)', 
            marginBottom: 'var(--spacing-lg)',
            fontWeight: 'var(--font-semibold)'
          }}>
            Quick Actions
          </Title>
          <Row gutter={[24, 24]}>
            {quickActions.map((action, index) => (
              <Col xs={24} sm={12} md={8} key={index}>
                <Card
                  className="glass-card hover:shadow-xl transition-all duration-300 cursor-pointer group"
                  bodyStyle={{ padding: '32px' }}
                  onClick={() => router.push(action.action)}
                  style={{
                    background: 'var(--glass-bg-primary)',
                    backdropFilter: 'blur(var(--glass-blur-medium))',
                    WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
                    border: '1px solid var(--glass-border)',
                    borderRadius: 'var(--radius-2xl)',
                    height: '100%',
                    boxShadow: 'var(--glass-shadow)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <Space direction="vertical" size={20} style={{ width: '100%' }}>
                    <div className="text-center">
                      <div className="mb-4 mx-auto w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 group-hover:scale-110" 
                           style={{ 
                             background: 'var(--primary-50)', 
                             border: '1px solid var(--primary-200)' 
                           }}>
                        <span style={{ fontSize: '24px', color: 'var(--interactive-primary)' }}>
                          {action.icon}
                        </span>
                      </div>
                      <Title level={4} style={{ 
                        color: 'var(--text-primary)', 
                        marginBottom: 'var(--spacing-sm)',
                        fontWeight: 'var(--font-semibold)'
                      }}>
                        {action.title}
                      </Title>
                      <Text style={{ 
                        color: 'var(--text-secondary)',
                        fontSize: 'var(--text-sm)',
                        lineHeight: 1.5
                      }}>
                        {action.description}
                      </Text>
                    </div>
                    <Button 
                      type="primary" 
                      size="large"
                      className="w-full"
                      style={{
                        background: 'var(--interactive-primary)',
                        borderColor: 'var(--interactive-primary)',
                        borderRadius: 'var(--radius-xl)',
                        fontWeight: 'var(--font-medium)'
                      }}
                    >
                      Get Started
                    </Button>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </div>

        {/* Professional Activity & Stats Grid */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card 
              className="glass-card" 
              style={{
                background: 'var(--glass-bg-primary)',
                backdropFilter: 'blur(var(--glass-blur-medium))',
                WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-2xl)',
                boxShadow: 'var(--glass-shadow)',
                position: 'relative',
                overflow: 'hidden'
              }}
              title={
                <div className="flex items-center justify-between">
                  <Title level={4} style={{ 
                    color: 'var(--text-primary)', 
                    margin: 0,
                    fontWeight: 'var(--font-semibold)'
                  }}>
                    Recent Activity
                  </Title>
                  <Button 
                    type="link" 
                    size="small" 
                    style={{ color: 'var(--interactive-primary)' }}
                  >
                    View All
                  </Button>
                </div>
              }
            >
              <div className="empty-state py-8">
                <div className="text-center">
                  <div className="mb-4 mx-auto w-16 h-16 rounded-full flex items-center justify-center" 
                       style={{ 
                         background: 'var(--bg-tertiary)', 
                         border: '1px solid var(--border-secondary)' 
                       }}>
                    <CloudOutlined style={{ fontSize: '24px', color: 'var(--text-muted)' }} />
                  </div>
                  <Title level={4} style={{ 
                    color: 'var(--text-primary)', 
                    marginBottom: 'var(--spacing-sm)'
                  }}>
                    No Recent Activity
                  </Title>
                  <Text style={{ 
                    color: 'var(--text-secondary)',
                    marginBottom: 'var(--spacing-lg)',
                    display: 'block'
                  }}>
                    Your activity will appear here once you start using the platform.
                  </Text>
                  <Button 
                    type="primary" 
                    onClick={() => router.push('/environments')}
                    style={{
                      background: 'var(--interactive-primary)',
                      borderColor: 'var(--interactive-primary)',
                      borderRadius: 'var(--radius-xl)'
                    }}
                  >
                    Launch Your First Environment
                  </Button>
                </div>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} lg={8}>
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
              <Card 
                className="glass-card" 
                style={{
                  background: 'var(--glass-bg-primary)',
                  backdropFilter: 'blur(var(--glass-blur-medium))',
                  WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-2xl)',
                  boxShadow: 'var(--glass-shadow)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                title={
                  <Title level={4} style={{ 
                    color: 'var(--text-primary)', 
                    margin: 0,
                    fontWeight: 'var(--font-semibold)'
                  }}>
                    System Resources
                  </Title>
                }
              >
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Text style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
                        CPU Usage
                      </Text>
                      <Text style={{ color: 'var(--text-primary)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
                        23%
                      </Text>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius-lg)',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: '23%',
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--success-400), var(--success-500))',
                        borderRadius: 'var(--radius-lg)'
                      }} />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Text style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
                        Memory
                      </Text>
                      <Text style={{ color: 'var(--text-primary)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
                        67%
                      </Text>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius-lg)',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: '67%',
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--warning-400), var(--warning-500))',
                        borderRadius: 'var(--radius-lg)'
                      }} />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Text style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
                        Storage
                      </Text>
                      <Text style={{ color: 'var(--text-primary)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
                        41%
                      </Text>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius-lg)',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: '41%',
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--info-400), var(--info-500))',
                        borderRadius: 'var(--radius-lg)'
                      }} />
                    </div>
                  </div>
                </Space>
              </Card>
              
              <Card 
                className="glass-card" 
                style={{
                  background: 'var(--glass-bg-primary)',
                  backdropFilter: 'blur(var(--glass-blur-medium))',
                  WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-2xl)',
                  boxShadow: 'var(--glass-shadow)',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                title={
                  <Title level={4} style={{ 
                    color: 'var(--text-primary)', 
                    margin: 0,
                    fontWeight: 'var(--font-semibold)'
                  }}>
                    Pro Tips
                  </Title>
                }
              >
                <div style={{
                  padding: 'var(--spacing-lg)',
                  borderRadius: 'var(--radius-xl)',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-secondary)'
                }}>
                  <div className="flex items-start gap-3">
                    <div className="icon-container primary p-2" style={{
                      background: 'var(--primary-50)',
                      border: '1px solid var(--primary-200)',
                      borderRadius: 'var(--radius-lg)',
                      flexShrink: 0
                    }}>
                      <RocketOutlined style={{ fontSize: '14px', color: 'var(--interactive-primary)' }} />
                    </div>
                    <div>
                      <Text style={{ 
                        color: 'var(--text-primary)', 
                        fontSize: 'var(--text-sm)',
                        fontWeight: 'var(--font-medium)',
                        display: 'block',
                        marginBottom: 'var(--spacing-xs)'
                      }}>
                        Quick Start
                      </Text>
                      <Text style={{ 
                        color: 'var(--text-secondary)', 
                        fontSize: 'var(--text-xs)',
                        lineHeight: 1.5
                      }}>
                        Use templates to quickly launch pre-configured environments for your research projects.
                      </Text>
                    </div>
                  </div>
                </div>
                <Button 
                  type="link" 
                  size="small" 
                  style={{ 
                    color: 'var(--interactive-primary)', 
                    padding: '8px 0',
                    height: 'auto'
                  }}
                >
                  Learn More →
                </Button>
              </Card>
            </Space>
          </Col>
        </Row>
      </div>
    </MainLayout>
  );
}
