'use client';

import React from 'react';
import { Breadcrumb, Layout } from 'antd';
import { HomeOutlined, SettingOutlined } from '@ant-design/icons';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const { Content } = Layout;

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const getBreadcrumbItems = () => {
    return [
      {
        title: (
          <span>
            <HomeOutlined /> Dashboard
          </span>
        ),
      },
      {
        title: (
          <span>
            <SettingOutlined /> Settings
          </span>
        ),
      },
    ];
  };

  return (
    <ProtectedRoute>
      <Layout className="min-h-screen bg-transparent">
        <Content className="p-6">
          {/* Breadcrumb */}
          <Breadcrumb
            items={getBreadcrumbItems()}
            className="mb-6 text-text-secondary"
          />
          
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Settings & Configuration
            </h1>
            <p className="text-text-secondary">
              Manage your account, preferences, and workspace configurations
            </p>
          </div>

          {/* Settings Content */}
          {children}
        </Content>
      </Layout>
    </ProtectedRoute>
  );
}
