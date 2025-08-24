'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter, usePathname } from 'next/navigation';
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
} from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  RocketOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
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

  // Simple navigation handler using Next.js router
  const navigateTo = (path: string) => {
    router.push(path);
  };

  // Menu items based on Main.py structure
  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => navigateTo('/'),
    },
    {
      key: '/environments',
      icon: <RocketOutlined />,
      label: 'Environments',
      onClick: () => navigateTo('/environments'),
    },
    {
      key: '/storage',
      icon: <DatabaseOutlined />,
      label: 'Storage',
      onClick: () => navigateTo('/storage'),
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: 'Monitoring',
      onClick: () => navigateTo('/monitoring'),
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => navigateTo('/settings'),
    },
  ];

  // User dropdown menu
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => navigateTo('/profile'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign Out',
      danger: true,
      onClick: () => signOut({ callbackUrl: '/auth/signin' }),
    },
  ];

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
               pathname === '/storage' ? 'Storage' :
               pathname === '/monitoring' ? 'Monitoring' :
               pathname === '/settings' ? 'Settings' :
               'CMBAgent Cloud'}
            </Title>
          </div>

          <div className="flex items-center space-x-4">
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
                menu={{ items: userMenuItems }}
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
