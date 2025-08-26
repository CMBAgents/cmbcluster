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
  theme,
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

const { Sider, Header, Content } = Layout;
const { Text, Title } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const { data: session } = useSession();
  const router = useRouter();
  const pathname = usePathname();

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

  const handleThemeToggle = (checked: boolean) => {
    setDarkMode(checked);
    // Here you would implement theme switching logic
    // For now, we'll keep it as a placeholder
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
        className="bg-[#1f1f1f] border-r border-border-primary"
        theme="dark"
      >
        <div className="p-4">
          {/* Logo Section */}
          <div className="flex items-center justify-center mb-8">
            {!collapsed ? (
              <div className="flex items-center space-x-3">
                <div className="cambridge-logo-container">
                  <Image
                    src="/logos/cambridge-logo.png"
                    alt="Cambridge"
                    width={40}
                    height={20}
                    className="filter invert brightness-150 contrast-200 saturate-0 hue-rotate-180"
                    preview={false}
                  />
                </div>
                <Image
                  src="/logos/infosys-logo.png"
                  alt="Infosys"
                  width={40}
                  height={20}
                  preview={false}
                />
              </div>
            ) : (
              <div className="cambridge-logo-container">
                <Image
                  src="/logos/cambridge-logo.png"
                  alt="Cambridge"
                  width={32}
                  height={16}
                  className="filter invert brightness-150 contrast-200 saturate-0 hue-rotate-180"
                  preview={false}
                />
              </div>
            )}
          </div>

          {/* App Title */}
          {!collapsed && (
            <div className="text-center mb-6">
              <Title level={4} className="text-white mb-1">
                CMBAgent Cloud
              </Title>
              <Text type="secondary" className="text-xs">
                Autonomous Research Platform
              </Text>
            </div>
          )}

          {/* Navigation Menu */}
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            className="bg-transparent border-r-0"
          />

          {/* User Info - Bottom of sidebar */}
          {!collapsed && session?.user && (
            <div className="absolute bottom-4 left-4 right-4">
              <div className="bg-[#262626] rounded-lg p-3">
                <div className="flex items-center space-x-3">
                  <Avatar
                    src={session.user.image}
                    icon={<UserOutlined />}
                    size="small"
                  />
                  <div className="flex-1 min-w-0">
                    <Text className="text-white text-sm block truncate">
                      {session.user.name}
                    </Text>
                    <Text type="secondary" className="text-xs block truncate">
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
        {/* Header */}
        <Header className="bg-[#262730] border-b border-border-primary px-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Collapse Toggle */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="text-text-primary hover:bg-background-tertiary"
            />

            {/* Page Title */}
            <Title level={4} className="text-text-primary mb-0">
              {pathname === '/' ? 'Dashboard' :
               pathname === '/environments' ? 'Environments' :
               pathname === '/settings' ? 'Settings' :
               'CMBAgent Cloud'}
            </Title>
          </div>

          <div className="flex items-center space-x-4">
            {/* System Alerts Notification */}
            <Popover
              content={
                <div style={{ width: 300 }}>
                  <div className="mb-3">
                    <Text strong>System Alerts</Text>
                  </div>
                  {failedEnvironments.length > 0 ? (
                    <div className="space-y-2">
                      {failedEnvironments.slice(0, 5).map((env) => (
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
                  className="text-text-primary hover:bg-background-tertiary"
                />
              </Badge>
            </Popover>

            {/* Theme Toggle */}
            <Space align="center">
              <SunOutlined className="text-text-secondary" />
              <Switch
                checked={darkMode}
                onChange={handleThemeToggle}
                size="small"
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
              />
            </Space>

            {/* User Dropdown */}
            {session?.user && (
              <Dropdown
                menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
                placement="bottomRight"
                arrow
                trigger={['click']}
              >
                <Button
                  type="text"
                  className="flex items-center space-x-2 text-text-primary hover:bg-background-tertiary px-3"
                >
                  <Avatar
                    src={session.user.image}
                    icon={<UserOutlined />}
                    size="small"
                  />
                  <span className="hidden md:inline">{session.user.name}</span>
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
