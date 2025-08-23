'use client';

import React, { useState } from 'react';
import { Tabs, Card } from 'antd';
import { UserOutlined, SettingOutlined, CodeOutlined, FileOutlined } from '@ant-design/icons';
import ProfileSettings from '@/components/settings/ProfileSettings';
import EnvironmentPreferences from '@/components/settings/EnvironmentPreferences';
import EnvironmentVariables from '@/components/settings/EnvironmentVariables';
import EnvironmentFiles from '@/components/settings/EnvironmentFiles';

export default function SettingsPage() {
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
    <Card className="bg-background-secondary border-border-primary">
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
        className="settings-tabs"
      />
    </Card>
  );
}
