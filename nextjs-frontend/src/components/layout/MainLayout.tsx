'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter, usePathname } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { Environment } from '@/types';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Typography,
  Space,
  Image,
  Switch,
  Badge,
  Popover,
  Alert,
  Empty,
} from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  RocketOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
  BellOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useTheme } from '@/contexts/ThemeContext';

const { Sider, Header, Content } = Layout;
const { Text, Title } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { data: session } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  // Fetch environments for system alerts
  const { data: environmentsResponse } = useQuery({
    queryKey: ['environments-alerts'],
    queryFn: () => apiClient.listEnvironments(),
    refetchInterval: 30000, // Check every 30 seconds
    enabled: !!session,
    retry: 1,
  });

  const environments = environmentsResponse?.environments || [];
  const failedEnvironments = environments.filter(env => env.status === 'failed');

  // Simple navigation handler using Next.js router
  const navigateTo = (path: string) => {
    router.push(path);
  };

  // Handle menu click
  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigateTo(e.key);
  };

  // Menu items - removed monitoring and storage from sidebar
  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/environments',
      icon: <RocketOutlined />,
      label: 'Environments',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  // User dropdown menu - without onClick functions
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign Out',
      danger: true,
    },
  ];

  // Handle user menu click
  const handleUserMenuClick: MenuProps['onClick'] = (e) => {
    if (e.key === 'logout') {
      signOut({ callbackUrl: '/auth/signin' });
    } else if (e.key === 'profile') {
      navigateTo('/profile');
    }
  };

  return (
    <Layout className="min-h-screen">
      {/* Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={280}
        collapsedWidth={80}
        style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur))',
          borderRight: '1px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow)'
        }}
      >
        <div className="p-4">
          {/* Professional Logo Section with CMBAgent branding */}
          <div className="flex items-center justify-center mb-8">
            {!collapsed ? (
              <div className="flex items-center space-x-3">
                <div className="icon-container primary p-2" style={{
                  background: 'var(--glass-bg-secondary)',
                  backdropFilter: 'blur(var(--glass-blur-light))',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-xl)'
                }}>
                  <Image
                    src="/logos/cmbagent-logo.png"
                    alt="CMBAgent"
                    width={24}
                    height={24}
                    preview={false}
                    style={{ filter: 'brightness(1.1)' }}
                  />
                </div>
                <div>
                  <Text style={{ 
                    color: 'var(--text-primary)', 
                    fontWeight: 'var(--font-semibold)',
                    fontSize: 'var(--text-lg)'
                  }}>
                    CMBAgent
                  </Text>
                  <br />
                  <Text style={{ 
                    color: 'var(--text-muted)', 
                    fontSize: 'var(--text-xs)'
                  }}>
                    Research Platform
                  </Text>
                </div>
              </div>
            ) : (
              <div className="icon-container primary p-2" style={{
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-xl)'
              }}>
                <Image
                  src="/logos/cmbagent-logo.png"
                  alt="CMBAgent"
                  width={24}
                  height={24}
                  preview={false}
                  style={{ filter: 'brightness(1.1)' }}
                />
              </div>
            )}
          </div>

          {/* Navigation Menu */}
          <Menu
            mode="inline"
            selectedKeys={[pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)'
            }}
            className="professional-nav-menu"
          />

          {/* Professional User Info - Bottom of sidebar */}
          {!collapsed && session?.user && (
            <div className="absolute bottom-4 left-4 right-4">
              <div className="glass-card p-3" style={{
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-xl)'
              }}>
                <div className="flex items-center space-x-3">
                  <Avatar
                    src={session.user.image}
                    icon={<UserOutlined />}
                    size="small"
                  />
                  <div className="flex-1 min-w-0">
                    <Text style={{ 
                      color: 'var(--text-primary)', 
                      fontSize: 'var(--text-sm)',
                      fontWeight: 'var(--font-medium)'
                    }} className="block truncate">
                      {session.user.name}
                    </Text>
                    <Text style={{ 
                      color: 'var(--text-muted)', 
                      fontSize: 'var(--text-xs)'
                    }} className="block truncate">
                      {session.user.email}
                    </Text>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </Sider>

      <Layout>
        {/* Professional Header */}
        <Header style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur))',
          borderBottom: '1px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div className="flex items-center space-x-4">
            {/* Professional Collapse Toggle */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-xl)',
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                color: 'var(--text-primary)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              className="hover:shadow-md"
            />

            {/* Page Title */}
            <Title level={4} style={{ 
              color: 'var(--text-primary)', 
              margin: 0,
              fontWeight: 'var(--font-semibold)'
            }}>
              {pathname === '/' ? 'Dashboard' :
               pathname === '/environments' ? 'Environments' :
               pathname === '/settings' ? 'Settings' :
               'CMBAgent Cloud'}
            </Title>
          </div>

          <div className="flex items-center space-x-4">
            {/* Professional System Alerts Notification */}
            <Popover
              content={
                <div style={{ width: 300 }}>
                  <div className="mb-3">
                    <Text strong>System Alerts</Text>
                  </div>
                  {failedEnvironments.length > 0 ? (
                    <div className="space-y-2">
                      {failedEnvironments.slice(0, 5).map((env: Environment) => (
                        <Alert
                          key={env.id}
                          message={`Environment ${env.env_id?.substring(0, 8) || env.id?.substring(0, 8)} has failed`}
                          type="error"
                          size="small"
                          showIcon
                          icon={<ExclamationCircleOutlined />}
                          action={
                            <Button 
                              size="small" 
                              type="link"
                              onClick={() => navigateTo('/environments')}
                            >
                              Fix
                            </Button>
                          }
                        />
                      ))}
                      {failedEnvironments.length > 5 && (
                        <Text type="secondary" className="block text-center">
                          +{failedEnvironments.length - 5} more alerts
                        </Text>
                      )}
                    </div>
                  ) : (
                    <Empty 
                      image={Empty.PRESENTED_IMAGE_SIMPLE} 
                      description="No system alerts"
                      className="my-4"
                    />
                  )}
                </div>
              }
              title={null}
              trigger="click"
              placement="bottomRight"
            >
              <Badge count={failedEnvironments.length} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-xl)',
                    background: 'var(--glass-bg-secondary)',
                    backdropFilter: 'blur(var(--glass-blur-light))',
                    border: '1px solid var(--glass-border)',
                    color: 'var(--text-primary)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                  className="hover:shadow-md"
                />
              </Badge>
            </Popover>

            {/* Professional Theme Toggle - matching sign-in page */}
            <button 
              onClick={toggleTheme}
              className="icon-container primary"
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-xl)',
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: 'pointer'
              }}
            >
              {theme === 'dark' ? (
                <SunOutlined style={{ fontSize: '16px', color: 'var(--interactive-primary)' }} />
              ) : (
                <MoonOutlined style={{ fontSize: '16px', color: 'var(--interactive-primary)' }} />
              )}
            </button>

            {/* Professional User Dropdown */}
            {session?.user && (
              <Dropdown
                menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
                placement="bottomRight"
                arrow
                trigger={['click']}
              >
                <Button
                  type="text"
                  style={{
                    background: 'var(--glass-bg-secondary)',
                    backdropFilter: 'blur(var(--glass-blur-light))',
                    border: '1px solid var(--glass-border)',
                    borderRadius: 'var(--radius-xl)',
                    color: 'var(--text-primary)',
                    padding: '8px 16px',
                    height: '40px',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                  className="flex items-center space-x-2 hover:shadow-md"
                >
                  <Avatar
                    src={session.user.image}
                    icon={<UserOutlined />}
                    size="small"
                  />
                  <span className="hidden md:inline" style={{ 
                    color: 'var(--text-primary)',
                    fontWeight: 'var(--font-medium)',
                    fontSize: 'var(--text-sm)'
                  }}>
                    {session.user.name}
                  </span>
                </Button>
              </Dropdown>
            )}
          </div>
        </Header>

        {/* Main Content */}
        <Content className="bg-background-primary p-6 overflow-auto">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
