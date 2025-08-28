'use client';

import { useState, useEffect, useMemo } from 'react';
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
  DatabaseOutlined,
  MonitorOutlined,
  CloudServerOutlined,
  FolderOutlined,
  BarChartOutlined,
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

  // Memoize logo to prevent re-rendering
  const logoElement = useMemo(() => (
    <img
      src="/logos/cmbagent-logo.png"
      alt="CMBAgent"
      width={24}
      height={24}
      style={{ 
        filter: 'brightness(1.1)',
        display: 'block',
        objectFit: 'contain',
        pointerEvents: 'none',
        userSelect: 'none'
      }}
      loading="eager"
      decoding="sync"
    />
  ), []);

  // Static menu items to prevent icon reloading
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
      navigateTo('/settings');
    }
  };

  return (
    <Layout className="min-h-screen">
      {/* Enhanced Glassmorphism Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={280}
        collapsedWidth={80}
        className="glass-sidebar"
        style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur-heavy))',
          WebkitBackdropFilter: 'blur(var(--glass-blur-heavy))',
          borderRight: '1px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow)',
          position: 'relative',
          zIndex: 10
        }}
      >
        <div className="p-4">
          {/* Optimized Professional Logo Section - No Image Reloading */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center space-x-3" style={{
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              justifyContent: collapsed ? 'center' : 'flex-start'
            }}>
              <div className="icon-container primary p-2" style={{
                background: 'var(--glass-bg-secondary)',
                backdropFilter: 'blur(var(--glass-blur-light))',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-xl)',
                flexShrink: 0
              }}>
                {logoElement}
              </div>
              <div style={{
                opacity: collapsed ? 0 : 1,
                transform: collapsed ? 'translateX(-10px)' : 'translateX(0)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                overflow: 'hidden',
                width: collapsed ? 0 : 'auto',
                whiteSpace: 'nowrap'
              }}>
                <Text style={{ 
                  color: 'var(--text-primary)', 
                  fontWeight: 'var(--font-semibold)',
                  fontSize: 'var(--text-lg)',
                  display: 'block',
                  lineHeight: 1.2
                }}>
                  CMBAgent 
                  <span style={{ 
                    fontWeight: 'var(--font-normal)',
                    background: `linear-gradient(135deg, var(--interactive-primary), var(--primary-300))`,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    Cloud
                  </span>
                </Text>
                <Text style={{ 
                  color: 'var(--text-muted)', 
                  fontSize: 'var(--text-xs)',
                  display: 'block',
                  lineHeight: 1.2
                }}>
                  Autonomous Research
                </Text>
              </div>
            </div>
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
        {/* Enhanced Glassmorphism Header */}
        <Header className="glass-header" style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur-medium))',
          WebkitBackdropFilter: 'blur(var(--glass-blur-medium))',
          borderBottom: '1px solid var(--glass-border)',
          boxShadow: 'var(--glass-shadow)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'relative',
          zIndex: 20,
          height: '64px'
        }}>
          <div className="flex items-center space-x-4">
            {/* Enhanced Glass Collapse Toggle */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="glass-button"
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-xl)',
                color: 'var(--text-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
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
                  className="glass-button"
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-xl)',
                    color: 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                />
              </Badge>
            </Popover>

            {/* Enhanced Glass Theme Toggle */}
            <button 
              onClick={toggleTheme}
              className="glass-button"
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-xl)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-primary)'
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
                  className="glass-button"
                  style={{
                    color: 'var(--text-primary)',
                    padding: '8px',
                    height: '40px',
                    width: '40px',
                    borderRadius: 'var(--radius-xl)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Avatar
                    src={session.user.image}
                    icon={<UserOutlined />}
                    size="small"
                    style={{
                      border: '1px solid var(--glass-border)',
                      background: 'var(--glass-bg-secondary)'
                    }}
                  />
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
