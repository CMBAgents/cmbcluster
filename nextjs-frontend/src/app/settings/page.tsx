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
        {/* Settings Interface with Minimalistic Tabs */}
        <Card className="glass-card" bodyStyle={{ padding: '0' }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="large"
            className="settings-tabs"
            tabBarStyle={{
              margin: 0,
              padding: '0 24px',
            }}
            items={[
              {
                key: 'profile',
                label: (
                  <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <UserOutlined style={{ fontSize: '16px' }} />
                    <span>Profile</span>
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px' }}>
                    <ProfileSettings />
                  </div>
                ),
              },
              {
                key: 'environment-variables',
                label: (
                  <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <CodeOutlined style={{ fontSize: '16px' }} />
                    <span>Environment Variables</span>
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px' }}>
                    <EnvironmentVariables />
                  </div>
                ),
              },
              {
                key: 'environment-files',
                label: (
                  <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <FileOutlined style={{ fontSize: '16px' }} />
                    <span>Environment Files</span>
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px' }}>
                    <EnvironmentFiles />
                  </div>
                ),
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
