'use client';

import React, { useState } from 'react';
import { Tabs, Card, Typography } from 'antd';
import { UserOutlined, SettingOutlined, CodeOutlined, FileOutlined } from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ProfileSettings from '@/components/settings/ProfileSettings';
import EnvironmentPreferences from '@/components/settings/EnvironmentPreferences';
import EnvironmentVariables from '@/components/settings/EnvironmentVariables';
import EnvironmentFiles from '@/components/settings/EnvironmentFiles';


const { Title, Text } = Typography;

function SettingsContent() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabItems = [
    {
      key: 'profile',
      label: (
        <span>
          <UserOutlined />
          Profile
        </span>
      ),
      children: <ProfileSettings />,
    },
    {
      key: 'environment-preferences',
      label: (
        <span>
          <SettingOutlined />
          Environment Preferences
        </span>
      ),
      children: <EnvironmentPreferences />,
    },
    {
      key: 'environment-variables',
      label: (
        <span>
          <CodeOutlined />
          Environment Variables
        </span>
      ),
      children: <EnvironmentVariables />,
    },
    {
      key: 'environment-files',
      label: (
        <span>
          <FileOutlined />
          Environment Files
        </span>
      ),
      children: <EnvironmentFiles />,
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div>
          <Title level={2} className="text-text-primary mb-2">
            Settings
          </Title>
          <Text className="text-text-secondary">
            Manage your account, environment preferences, and workspace configuration.
          </Text>
        </div>

        {/* Settings Content */}
        <Card className="bg-background-secondary border-border-primary">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            size="large"
            className="settings-tabs"
          />
        </Card>
      </div>
    </MainLayout>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}
