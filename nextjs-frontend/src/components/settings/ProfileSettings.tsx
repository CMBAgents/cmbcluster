'use client';

import React from 'react';
import { Card, Col, Row, Input, Button, message, Typography, Avatar, Badge, Statistic } from 'antd';
import { LogoutOutlined, ReloadOutlined, UserOutlined, CheckCircleOutlined, SafetyOutlined, CrownOutlined } from '@ant-design/icons';
import { useSession, signOut } from 'next-auth/react';

const { Title, Text, Paragraph } = Typography;

export default function ProfileSettings() {
  const { data: session } = useSession();
  const user = session?.user;

  const handleRefreshProfile = async () => {
    try {
      message.success('Profile information refreshed!');
      window.location.reload();
    } catch (error) {
      message.error('Failed to refresh profile');
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut({
        callbackUrl: '/auth/signin',
        redirect: true,
      });
    } catch (error) {
      message.error('Failed to sign out');
    }
  };

  return (
    <div className="space-y-4">
      {/* Profile Overview Card */}
      <Card className="glass-card">
        <div className="flex items-center gap-6 mb-6">
          <Badge dot status="success" offset={[-5, 50]}>
            <Avatar
              size={80}
              src={user?.image}
              icon={<UserOutlined />}
              className="shadow-lg"
              style={{ border: '3px solid var(--primary-500)' }}
            />
          </Badge>
          <div className="flex-1">
            <Title level={2} style={{ margin: 0, color: 'var(--text-primary)' }}>
              {user?.name || 'User'}
            </Title>
            <Text style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>
              {user?.email || 'Not available'}
            </Text>
            <div className="flex items-center gap-2 mt-2">
              <Badge status="success" />
              <Text style={{ color: 'var(--success-600)', fontSize: '12px', fontWeight: '500' }}>
                ACTIVE ACCOUNT
              </Text>
            </div>
          </div>
        </div>

        <Paragraph style={{ color: 'var(--text-secondary)' }}>
          Your profile information is automatically synchronized with your Google account.
        </Paragraph>
      </Card>

      {/* Account Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container success mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <CheckCircleOutlined style={{ fontSize: '24px' }} />
            </div>
            <Statistic
              title="Account Status"
              value="Active"
              valueStyle={{ color: 'var(--success-600)', fontSize: '18px', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container primary mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <SafetyOutlined style={{ fontSize: '24px' }} />
            </div>
            <Statistic
              title="Authentication"
              value="Google OAuth"
              valueStyle={{ color: 'var(--primary-600)', fontSize: '18px', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container warning mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <CrownOutlined style={{ fontSize: '24px' }} />
            </div>
            <Statistic
              title="Access Level"
              value="Researcher"
              valueStyle={{ color: 'var(--warning-600)', fontSize: '18px', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Account Information */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card title="Account Details" className="glass-card">
            <div className="space-y-4">
              <div>
                <Text strong style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginBottom: '4px' }}>
                  FULL NAME
                </Text>
                <Input
                  value={user?.name || 'Not available'}
                  disabled
                  size="large"
                />
              </div>
              <div>
                <Text strong style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginBottom: '4px' }}>
                  EMAIL ADDRESS
                </Text>
                <Input
                  value={user?.email || 'Not available'}
                  disabled
                  size="large"
                />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="Session Information" className="glass-card">
            <div className="space-y-4">
              <div>
                <Text strong style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginBottom: '4px' }}>
                  USER ID
                </Text>
                <Input
                  value={session?.user?.sub || 'Not available'}
                  disabled
                  size="large"
                />
              </div>
              <div>
                <Text strong style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginBottom: '4px' }}>
                  SESSION START
                </Text>
                <Input
                  value={new Date().toLocaleString()}
                  disabled
                  size="large"
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Account Actions */}
      <Card title="Account Actions" className="glass-card">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Button
              type="default"
              icon={<ReloadOutlined />}
              onClick={handleRefreshProfile}
              size="large"
              className="glass-button w-full"
            >
              Refresh Profile
            </Button>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Button
              type="primary"
              danger
              icon={<LogoutOutlined />}
              onClick={handleSignOut}
              size="large"
              className="w-full"
            >
              Sign Out
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
