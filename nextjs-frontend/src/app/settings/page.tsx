'use client';

import React, { useState } from 'react';
import { Tabs, Card, Typography } from 'antd';
import { UserOutlined, CodeOutlined, FileOutlined } from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ProfileSettings from '@/components/settings/ProfileSettings';
import EnvironmentVariables from '@/components/settings/EnvironmentVariables';
import EnvironmentFiles from '@/components/settings/EnvironmentFiles';


const { Title, Text } = Typography;

function SettingsContent() {
  const [activeTab, setActiveTab] = useState('profile');

  return (
    <MainLayout>
      <div className="space-y-4">
        {/* Compact Header */}
        <div className="flex justify-between items-center">
          <div>
            <Title level={2} style={{ margin: '0 0 4px 0', fontSize: '24px' }}>Settings</Title>
            <Text style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              Manage your profile, environment variables, and configuration files
            </Text>
          </div>
        </div>

        {/* Compact Settings Interface */}
        <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="default"
            className="professional-tabs"
            items={[
              {
                key: 'profile',
                label: (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UserOutlined />
                    <span>Profile</span>
                  </span>
                ),
                children: <ProfileSettings />,
              },
              {
                key: 'environment-variables',
                label: (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CodeOutlined />
                    <span>Environment Variables</span>
                  </span>
                ),
                children: <EnvironmentVariables />,
              },
              {
                key: 'environment-files',
                label: (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileOutlined />
                    <span>Environment Files</span>
                  </span>
                ),
                children: <EnvironmentFiles />,
              },
            ]}
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
