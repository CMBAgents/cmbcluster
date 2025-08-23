'use client';

import React from 'react';
import { Card, Col, Row, Input, Button, message, Typography, Avatar } from 'antd';
import { LogoutOutlined, ReloadOutlined, UserOutlined } from '@ant-design/icons';
import { useSession, signOut } from 'next-auth/react';

const { Title, Text, Paragraph } = Typography;

export default function ProfileSettings() {
  const { data: session } = useSession();
  const user = session?.user;

  const handleRefreshProfile = async () => {
    try {
      message.success('Profile information refreshed!');
      // Force re-render by updating session
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

  const sectionStyle: React.CSSProperties = {
    background: 'rgba(26, 31, 46, 0.5)',
    borderRadius: '12px',
    padding: '24px',
    margin: '16px 0',
    borderLeft: '4px solid #4A9EFF',
  };

  const metricCardStyle: React.CSSProperties = {
    background: 'rgba(26, 31, 46, 0.8)',
    borderRadius: '12px',
    padding: '20px',
    textAlign: 'center',
    border: '1px solid #2D3748',
    transition: 'all 0.3s ease',
    height: '100%',
  };

  const statusBadgeStyle: React.CSSProperties = {
    display: 'inline-block',
    padding: '6px 14px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    backgroundColor: 'rgba(72, 187, 120, 0.1)',
    color: '#48BB78',
    border: '1px solid #48BB78',
  };

  return (
    <div className="space-y-6">
      {/* Profile Overview */}
      <div style={sectionStyle}>
        <Title level={3} className="text-white mb-4">
          Profile Information
        </Title>
        <Paragraph className="text-text-secondary mb-6">
          Your profile information is automatically synchronized with your Google account and cannot be modified here.
        </Paragraph>

        <Row gutter={[24, 24]}>
          {/* Account Details */}
          <Col xs={24} md={12}>
            <Card 
              title="Account Details"
              className="h-full bg-background-tertiary border-border-primary"
              headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
            >
              <div className="space-y-4">
                <div className="flex items-center space-x-4 mb-4">
                  <Avatar
                    size={64}
                    src={user?.image}
                    icon={<UserOutlined />}
                    className="border-2 border-primary"
                  />
                  <div>
                    <Text className="text-white text-lg font-semibold block">
                      {user?.name || 'Not available'}
                    </Text>
                    <Text className="text-text-secondary">
                      Google Account
                    </Text>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="text-text-secondary text-sm block mb-1">Full Name</label>
                    <Input
                      value={user?.name || 'Not available'}
                      disabled
                    />
                  </div>
                  
                  <div>
                    <label className="text-text-secondary text-sm block mb-1">Email Address</label>
                    <Input
                      value={user?.email || 'Not available'}
                      disabled
                    />
                  </div>
                </div>
              </div>
            </Card>
          </Col>

          {/* Security Information */}
          <Col xs={24} md={12}>
            <Card 
              title="Security Information"
              className="h-full bg-background-tertiary border-border-primary"
              headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
            >
              <div className="space-y-3">
                <div>
                  <label className="text-text-secondary text-sm block mb-1">User ID</label>
                  <Input
                    value={session?.user?.sub || 'Not available'}
                    disabled
                  />
                </div>
                
                <div>
                  <label className="text-text-secondary text-sm block mb-1">Session Start</label>
                  <Input
                    value={new Date().toLocaleString()}
                    disabled
                  />
                </div>

                <div>
                  <label className="text-text-secondary text-sm block mb-1">Account Type</label>
                  <Input
                    value="Researcher"
                    disabled
                  />
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Account Status */}
      <div style={sectionStyle}>
        <Title level={4} className="text-white mb-4">Account Status</Title>
        
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">Account Status</Title>
              <div style={statusBadgeStyle}>Active</div>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">Authentication</Title>
              <div style={statusBadgeStyle}>Google OAuth</div>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">Access Level</Title>
              <div style={statusBadgeStyle}>Researcher</div>
            </div>
          </Col>
        </Row>
      </div>

      {/* Account Actions */}
      <div style={sectionStyle}>
        <Title level={4} className="text-white mb-4">Account Actions</Title>
        
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Button
              type="default"
              icon={<ReloadOutlined />}
              onClick={handleRefreshProfile}
              className="w-full h-12"
              size="large"
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
              className="w-full h-12"
              size="large"
            >
              Sign Out
            </Button>
          </Col>
        </Row>
      </div>
    </div>
  );
}
