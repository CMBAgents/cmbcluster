'use client';

import React from 'react';
import {
  Card,
  Typography,
  Empty,
  Button,
} from 'antd';
import {
  MonitorOutlined,
  RocketOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

export default function MonitoringDashboard() {
  return (
    <div className="monitoring-dashboard">
      <Card className="glass-card">
        <div style={{ textAlign: 'center', padding: '80px 40px' }}>
          <div className="icon-container primary mb-6" style={{ width: '80px', height: '80px', margin: '0 auto 24px' }}>
            <MonitorOutlined style={{ fontSize: '40px' }} />
          </div>
          
          <Title level={2} style={{ color: 'var(--text-primary)', marginBottom: '16px' }}>
            Monitoring Dashboard
          </Title>
          
          <Text style={{ 
            color: 'var(--text-secondary)', 
            fontSize: '16px',
            display: 'block',
            marginBottom: '32px',
            maxWidth: '400px',
            margin: '0 auto 32px'
          }}>
            Advanced monitoring and analytics features will be available here soon. 
            Monitor your environment performance, resource usage, and system health.
          </Text>
          
          <div style={{ marginTop: '40px' }}>
            <Button 
              type="primary" 
              size="large" 
              icon={<RocketOutlined />}
              style={{ marginRight: '12px' }}
            >
              Coming Soon
            </Button>
            <Button size="large">
              View Documentation
            </Button>
          </div>
          
          <div style={{ 
            marginTop: '48px', 
            padding: '24px',
            background: 'var(--glass-bg-secondary)',
            borderRadius: '12px',
            maxWidth: '500px',
            margin: '48px auto 0'
          }}>
            <Text style={{ 
              color: 'var(--text-tertiary)', 
              fontSize: '14px',
              display: 'block',
              lineHeight: '1.6'
            }}>
              Future features will include: Real-time metrics, Resource usage charts, 
              Performance analytics, Alert notifications, and Custom dashboards.
            </Text>
          </div>
        </div>
      </Card>
    </div>
  );
}