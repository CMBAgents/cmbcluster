'use client';

import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { Card, Row, Col, Typography, Button, Space, Empty, Tag } from 'antd';
import {
  ShopOutlined,
  RocketOutlined,
  InfoCircleOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  CodeOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

function ApplicationStoreContent() {
  // Mock applications data - this will be fetched from API
  const applications = [
    {
      id: '1',
      name: 'CMBAgent Standard',
      summary: 'Complete cosmology research environment with Python, CMB tools, and data analysis libraries',
      category: 'research',
      icon_url: null,
      tags: ['python', 'cosmology', 'analysis'],
      is_default: true,
    },
    {
      id: '2',
      name: 'Machine Learning Lab',
      summary: 'TensorFlow, PyTorch, and Jupyter environment for ML research and model development',
      category: 'ml',
      icon_url: null,
      tags: ['tensorflow', 'pytorch', 'jupyter'],
      is_default: false,
    },
    {
      id: '3',
      name: 'Data Science Toolkit',
      summary: 'Pandas, NumPy, Matplotlib, and statistical analysis tools for data exploration',
      category: 'data-science',
      icon_url: null,
      tags: ['pandas', 'numpy', 'visualization'],
      is_default: false,
    },
  ];

  const handleLaunchEnvironment = (applicationId: string) => {
    // This will redirect to environment creation with pre-selected application
    window.location.href = `/environments?app=${applicationId}`;
  };

  const handleViewDetails = (applicationId: string) => {
    // Show application details modal or navigate to details page
    console.log('View details for application:', applicationId);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'research':
        return <ExperimentOutlined className="text-primary" />;
      case 'ml':
        return <DatabaseOutlined className="text-success" />;
      case 'data-science':
        return <CodeOutlined className="text-warning" />;
      default:
        return <RocketOutlined className="text-primary" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'research':
        return 'var(--primary-500)';
      case 'ml':
        return 'var(--success-500)';
      case 'data-science':
        return 'var(--warning-500)';
      default:
        return 'var(--primary-500)';
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Store Header */}
        <div className="glass-card p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="icon-container primary p-3">
              <ShopOutlined className="text-2xl text-primary" />
            </div>
            <div>
              <Title level={2} className="text-primary m-0">
                Welcome to Agentic Store
              </Title>
              <Paragraph className="text-secondary text-lg m-0">
                Discover and launch research environments tailored for your computational needs
              </Paragraph>
            </div>
          </div>
        </div>

        {/* Applications Grid */}
        {applications.length > 0 ? (
          <div>
            <Title level={3} className="text-primary mb-4">
              Available Research Environments
            </Title>
            <Row gutter={[24, 24]}>
              {applications.map((app) => (
                <Col xs={24} sm={12} lg={8} key={app.id}>
                  <Card
                    className="glass-card h-full"
                    bodyStyle={{ 
                      padding: '24px',
                      display: 'flex',
                      flexDirection: 'column',
                      height: '100%'
                    }}
                    hoverable
                  >
                    <Space direction="vertical" size={16} className="w-full h-full">
                      {/* Application Icon and Category */}
                      <div className="flex items-center justify-between">
                        <div className="icon-container" style={{
                          backgroundColor: `${getCategoryColor(app.category)}15`,
                          border: `1px solid ${getCategoryColor(app.category)}30`,
                          padding: '12px',
                          borderRadius: 'var(--radius-lg)'
                        }}>
                          {getCategoryIcon(app.category)}
                        </div>
                        {app.is_default && (
                          <Tag className="badge-success">
                            Default
                          </Tag>
                        )}
                      </div>

                      {/* Application Info */}
                      <div className="flex-1">
                        <Title level={4} className="text-primary mb-2">
                          {app.name}
                        </Title>
                        <Paragraph className="text-secondary mb-3">
                          {app.summary}
                        </Paragraph>

                        {/* Tags */}
                        <div className="mb-4">
                          {app.tags.map((tag) => (
                            <Tag 
                              key={tag} 
                              className="mr-1 mb-1"
                              style={{
                                backgroundColor: 'var(--glass-bg-secondary)',
                                border: '1px solid var(--border-primary)',
                                color: 'var(--text-secondary)'
                              }}
                            >
                              {tag}
                            </Tag>
                          ))}
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex space-x-2 w-full">
                        <Button
                          type="primary"
                          icon={<RocketOutlined />}
                          className="flex-1"
                          onClick={() => handleLaunchEnvironment(app.id)}
                        >
                          Launch
                        </Button>
                        <Button
                          icon={<InfoCircleOutlined />}
                          className="glass-button"
                          onClick={() => handleViewDetails(app.id)}
                        >
                          Info
                        </Button>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        ) : (
          <Card className="glass-card">
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <div className="text-center py-8">
                  <Text className="text-secondary">
                    No applications available. Contact your administrator to add research environments.
                  </Text>
                </div>
              }
            />
          </Card>
        )}

        {/* Getting Started Guide */}
        <div>
          <Title level={3} className="text-primary mb-4">
            Getting Started
          </Title>
          <Row gutter={[24, 24]}>
            <Col xs={24} md={8}>
              <Card className="glass-card text-center h-full">
                <Space direction="vertical" size={16}>
                  <div className="icon-container primary p-3">
                    <RocketOutlined className="text-2xl" />
                  </div>
                  <div>
                    <Title level={5} className="text-primary">
                      1. Choose Environment
                    </Title>
                    <Text className="text-secondary">
                      Browse available research environments and select one that fits your needs
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card className="glass-card text-center h-full">
                <Space direction="vertical" size={16}>
                  <div className="icon-container success p-3">
                    <DatabaseOutlined className="text-2xl" />
                  </div>
                  <div>
                    <Title level={5} className="text-primary">
                      2. Configure Resources
                    </Title>
                    <Text className="text-secondary">
                      Select CPU, memory, and storage options based on your computational requirements
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card className="glass-card text-center h-full">
                <Space direction="vertical" size={16}>
                  <div className="icon-container warning p-3">
                    <ExperimentOutlined className="text-2xl" />
                  </div>
                  <div>
                    <Title level={5} className="text-primary">
                      3. Start Research
                    </Title>
                    <Text className="text-secondary">
                      Launch your environment and begin your research with pre-configured tools
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </MainLayout>
  );
}

export default function ApplicationStore() {
  return (
    <ProtectedRoute>
      <ApplicationStoreContent />
    </ProtectedRoute>
  );
}
