'use client';

import React, { useState } from 'react';
import { Tabs, Card, Typography, Badge, Divider } from 'antd';
import { UserOutlined, SettingOutlined, CodeOutlined, FileOutlined, SafetyOutlined, GlobalOutlined } from '@ant-design/icons';
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
        <div className="flex items-center gap-3 py-1">
          <div className="icon-container primary p-2">
            <UserOutlined style={{ fontSize: '14px' }} />
          </div>
          <div className="text-left">
            <div className="font-medium" style={{ color: 'var(--text-primary)' }}>Profile</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Personal information</div>
          </div>
        </div>
      ),
      children: <ProfileSettings />,
    },
    {
      key: 'environment-preferences',
      label: (
        <div className="flex items-center gap-3 py-1">
          <div className="icon-container primary p-2">
            <SettingOutlined style={{ fontSize: '14px' }} />
          </div>
          <div className="text-left">
            <div className="font-medium" style={{ color: 'var(--text-primary)' }}>Preferences</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Environment defaults</div>
          </div>
        </div>
      ),
      children: <EnvironmentPreferences />,
    },
    {
      key: 'environment-variables',
      label: (
        <div className="flex items-center gap-3 py-1">
          <div className="icon-container warning p-2">
            <CodeOutlined style={{ fontSize: '14px' }} />
          </div>
          <div className="text-left">
            <div className="font-medium" style={{ color: 'var(--text-primary)' }}>Variables</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Environment config</div>
          </div>
          <Badge count={3} size="small" style={{ marginLeft: '8px' }} />
        </div>
      ),
      children: <EnvironmentVariables />,
    },
    {
      key: 'environment-files',
      label: (
        <div className="flex items-center gap-3 py-1">
          <div className="icon-container success p-2">
            <FileOutlined style={{ fontSize: '14px' }} />
          </div>
          <div className="text-left">
            <div className="font-medium" style={{ color: 'var(--text-primary)' }}>Files</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Configuration files</div>
          </div>
        </div>
      ),
      children: <EnvironmentFiles />,
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Professional Header */}
        <div className="page-header">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                Settings
              </h1>
              <p className="text-lg mb-4" style={{ color: 'var(--text-secondary)' }}>
                Configure your account, environment preferences, and workspace settings
              </p>
              <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-tertiary)' }}>
                <span className="flex items-center gap-1">
                  <SafetyOutlined style={{ fontSize: '14px' }} />
                  All changes auto-saved
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <GlobalOutlined style={{ fontSize: '14px' }} />
                  Synced across devices
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="flex flex-col gap-2">
                <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Last updated: Today
                </div>
                <div className="flex items-center gap-2">
                  <div className="status-indicator running"></div>
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Settings synced</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Settings Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Settings Navigation */}
          <div className="lg:col-span-1">
            <Card className="glass-card" bodyStyle={{ padding: 'var(--spacing-lg)' }}>
              <h3 className="font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
                Settings Categories
              </h3>
              <div className="space-y-2">
                {tabItems.map((item, index) => (
                  <button
                    key={item.key}
                    onClick={() => setActiveTab(item.key)}
                    className={`w-full text-left p-3 rounded-lg transition-all ${
                      activeTab === item.key 
                        ? 'bg-primary-50 border-primary-200' 
                        : 'hover:bg-gray-50'
                    }`}
                    style={{
                      border: activeTab === item.key 
                        ? '1px solid var(--interactive-primary)' 
                        : '1px solid transparent',
                      background: activeTab === item.key 
                        ? 'var(--primary-50)' 
                        : 'transparent'
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              
              <Divider style={{ margin: 'var(--spacing-lg) 0' }} />
              
              <div className="space-y-3">
                <h4 className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Quick Actions
                </h4>
                <button className="w-full text-left p-2 text-sm rounded-md hover:bg-gray-50 transition-colors" style={{ color: 'var(--text-secondary)' }}>
                  Export Settings
                </button>
                <button className="w-full text-left p-2 text-sm rounded-md hover:bg-gray-50 transition-colors" style={{ color: 'var(--text-secondary)' }}>
                  Import Settings
                </button>
                <button className="w-full text-left p-2 text-sm rounded-md hover:bg-gray-50 transition-colors" style={{ color: 'var(--text-secondary)' }}>
                  Reset to Defaults
                </button>
              </div>
            </Card>
          </div>
          
          {/* Settings Content */}
          <div className="lg:col-span-3">
            <Card className="glass-card" bodyStyle={{ padding: 0 }}>
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {tabItems.find(item => item.key === activeTab)?.key === 'profile' && 'Profile Settings'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-preferences' && 'Environment Preferences'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-variables' && 'Environment Variables'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-files' && 'Environment Files'}
                    </h2>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                      {tabItems.find(item => item.key === activeTab)?.key === 'profile' && 'Manage your personal information and account preferences'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-preferences' && 'Configure default settings for new environments'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-variables' && 'Set environment variables for your computing sessions'}
                      {tabItems.find(item => item.key === activeTab)?.key === 'environment-files' && 'Manage configuration files and templates'}
                    </p>
                  </div>
                </div>
                
                <div className="settings-content">
                  {tabItems.find(item => item.key === activeTab)?.children}
                </div>
              </div>
            </Card>
          </div>
        </div>
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
