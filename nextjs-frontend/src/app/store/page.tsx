'use client';

import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { Card, Row, Col, Typography, Button, Space, Empty, Tag, Spin, Modal, Form, Select, Switch, InputNumber, Alert, Radio, Progress } from 'antd';
import {
  ShopOutlined,
  RocketOutlined,
  InfoCircleOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ApplicationImage, StorageItem, StorageSelection } from '@/types';
import React, { useState } from 'react';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

// Preset configurations (same as in EnvironmentManagement)
const PRESET_CONFIGS = {
  minimal: {
    label: 'Minimal',
    cpu_limit: '0.5',
    memory_limit: '1Gi',
    storage_size: '25Gi',
    description: 'Basic setup for light computational tasks',
    color: '#52c41a'
  },
  standard: {
    label: 'Standard',
    cpu_limit: '2',
    memory_limit: '4Gi',
    storage_size: '50Gi',
    description: 'Balanced resources for most research workloads',
    color: '#1890ff'
  },
  performance: {
    label: 'Performance',
    cpu_limit: '4',
    memory_limit: '8Gi',
    storage_size: '100Gi',
    description: 'High-performance setup for intensive computations',
    color: '#f5222d'
  }
};

function ApplicationStoreContent() {
  // Fetch real applications from API
  const { data: applications, isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const response = await apiClient.listApplications();
      return response.data || [];
    }
  });

  // Launch modal state
  const [launchModalVisible, setLaunchModalVisible] = useState(false);
  const [selectedApplicationForLaunch, setSelectedApplicationForLaunch] = useState<ApplicationImage | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<keyof typeof PRESET_CONFIGS>('standard');
  const [customMode, setCustomMode] = useState(false);
  const [selectedStorage, setSelectedStorage] = useState<StorageSelection | null>(null);
  const [launchProgress, setLaunchProgress] = useState(0);
  const [launchStep, setLaunchStep] = useState('');
  const [launching, setLaunching] = useState(false);
  const [form] = Form.useForm();

  // Fetch storage options for the modal
  const { data: storageOptions = [] } = useQuery({
    queryKey: ['storage'],
    queryFn: async () => {
      try {
        const response = await apiClient.listStorage();
        return response.data || [];
      } catch (error) {
        console.error('Failed to fetch storage:', error);
        return [];
      }
    },
    enabled: launchModalVisible
  });

  const handleLaunchEnvironment = (app: ApplicationImage) => {
    setSelectedApplicationForLaunch(app);
    setLaunchModalVisible(true);
  };

  const handleLaunchSubmit = async (values: any) => {
    if (!selectedApplicationForLaunch || !selectedStorage) return;

    setLaunching(true);
    setLaunchProgress(0);
    setLaunchStep('Preparing environment...');

    try {
      // Simulate launch progress
      const steps = [
        'Preparing environment...',
        'Allocating resources...',
        'Setting up storage...',
        'Configuring application...',
        'Starting environment...'
      ];

      for (let i = 0; i < steps.length; i++) {
        setLaunchStep(steps[i]);
        setLaunchProgress((i + 1) * 20);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Create environment
      const environmentData = {
        name: `${selectedApplicationForLaunch.name}-${Date.now()}`,
        application_image_id: selectedApplicationForLaunch.id,
        cpu_limit: parseFloat(customMode ? values.cpu_limit : PRESET_CONFIGS[selectedPreset].cpu_limit),
        memory_limit: customMode ? values.memory_limit : PRESET_CONFIGS[selectedPreset].memory_limit,
        storage_size: customMode ? values.storage_size : PRESET_CONFIGS[selectedPreset].storage_size,
        storage_selection: selectedStorage
      };

      const response = await apiClient.createEnvironment(environmentData);
      
      if (response.status === 'success' || response.status === 'created') {
        setLaunchStep('Environment created successfully!');
        setLaunchProgress(100);
        
        setTimeout(() => {
          setLaunchModalVisible(false);
          setLaunching(false);
          setLaunchProgress(0);
          setLaunchStep('');
          // Optionally redirect to environments page
          window.location.href = '/environments';
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to launch environment:', error);
      setLaunchStep('Launch failed. Please try again.');
      setLaunching(false);
      setTimeout(() => {
        setLaunchProgress(0);
        setLaunchStep('');
      }, 3000);
    }
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

        {/* Loading State */}
        {isLoading && (
          <Card className="glass-card">
            <div className="text-center py-8">
              <Spin size="large" />
              <div className="mt-4">
                <Text className="text-secondary">Loading available research environments...</Text>
              </div>
            </div>
          </Card>
        )}

        {/* Error State */}
        {error && (
          <Card className="glass-card">
            <div className="text-center py-8">
              <Text className="text-error">
                Failed to load applications. Please try again later.
              </Text>
            </div>
          </Card>
        )}

        {/* Applications Grid */}
        {!isLoading && !error && applications && applications.length > 0 ? (
          <div>
            <Title level={3} className="text-primary mb-4">
              Available Research Environments
            </Title>
            <Row gutter={[24, 24]}>
              {applications.map((app: ApplicationImage) => (
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
                        {app.tags?.includes('default') && (
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
                          {app.tags?.map((tag) => (
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
                          onClick={() => handleLaunchEnvironment(app)}
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
        ) : !isLoading && !error && (
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

        {/* Launch Environment Modal */}
        <Modal
          title={
            <Space>
              <RocketOutlined style={{ color: 'var(--interactive-primary)' }} />
              <span>Launch Environment</span>
              {selectedApplicationForLaunch && (
                <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                  • {selectedApplicationForLaunch.name}
                </span>
              )}
            </Space>
          }
          open={launchModalVisible}
          onCancel={() => setLaunchModalVisible(false)}
          footer={null}
          width={480}
          centered
          styles={{
            content: {
              background: 'var(--glass-bg-primary)',
              backdropFilter: 'blur(var(--glass-blur))',
              border: '1px solid var(--glass-border)',
              borderRadius: '12px'
            }
          }}
        >
          {launching && launchProgress > 0 && (
            <div className="mb-3 text-center">
              <Text style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{launchStep}</Text>
              <Progress percent={launchProgress} status="active" size="small" />
            </div>
          )}

          <Form
            form={form}
            layout="vertical"
            onFinish={handleLaunchSubmit}
            initialValues={{
              preset: 'standard',
              cpu_limit: PRESET_CONFIGS[selectedPreset].cpu_limit,
              memory_limit: PRESET_CONFIGS[selectedPreset].memory_limit,
              storage_size: PRESET_CONFIGS[selectedPreset].storage_size,
            }}
          >
            {/* Compact Environment Type Selection */}
            <Form.Item label="Configuration" style={{ marginBottom: '12px' }}>
              <Select 
                value={selectedPreset} 
                onChange={setSelectedPreset}
                style={{ width: '100%' }}
                size="middle"
              >
                {Object.entries(PRESET_CONFIGS).map(([key, config]) => (
                  <Option key={key} value={key}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div 
                        style={{ 
                          width: '8px', 
                          height: '8px', 
                          borderRadius: '50%',
                          backgroundColor: config.color,
                          flexShrink: 0
                        }}
                      />
                      <span style={{ fontWeight: '500' }}>{config.label}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                        {config.cpu_limit}CPU • {config.memory_limit.replace('Gi', 'GB')}
                      </span>
                    </div>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            {/* Show selected application info */}
            {selectedApplicationForLaunch && (
              <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: 'var(--glass-bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <div 
                    style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%',
                      backgroundColor: selectedApplicationForLaunch.category === 'research' ? 'var(--primary-500)' : 
                                     selectedApplicationForLaunch.category === 'ml' ? 'var(--success-500)' : 
                                     'var(--warning-500)',
                      flexShrink: 0
                    }}
                  />
                  <Text style={{ fontWeight: '500', fontSize: '14px' }}>{selectedApplicationForLaunch.name}</Text>
                  <Text style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {selectedApplicationForLaunch.category}
                  </Text>
                </div>
                <Text style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {selectedApplicationForLaunch.summary}
                </Text>
              </div>
            )}

            {/* Compact Custom Configuration Toggle */}
            {customMode && (
              <div style={{ marginBottom: '16px' }}>
                <Row gutter={8}>
                  <Col span={8}>
                    <Form.Item label="CPU" name="cpu_limit" style={{ marginBottom: '8px' }}>
                      <InputNumber
                        min={0.5}
                        max={8}
                        step={0.5}
                        style={{ width: '100%' }}
                        size="small"
                        suffix="cores"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item label="Memory" name="memory_limit" style={{ marginBottom: '8px' }}>
                      <Select size="small" style={{ width: '100%' }}>
                        <Option value="1Gi">1GB</Option>
                        <Option value="2Gi">2GB</Option>
                        <Option value="4Gi">4GB</Option>
                        <Option value="8Gi">8GB</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item label="Storage" name="storage_size" style={{ marginBottom: '8px' }}>
                      <Select size="small" style={{ width: '100%' }}>
                        <Option value="25Gi">25GB</Option>
                        <Option value="50Gi">50GB</Option>
                        <Option value="100Gi">100GB</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              </div>
            )}
            
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <Text style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                {PRESET_CONFIGS[selectedPreset].cpu_limit} CPU • {PRESET_CONFIGS[selectedPreset].memory_limit.replace('Gi', 'GB')} RAM • {PRESET_CONFIGS[selectedPreset].storage_size.replace('Gi', 'GB')} Storage
              </Text>
              <Space>
                <Text style={{ fontSize: '12px' }}>Custom</Text>
                <Switch size="small" checked={customMode} onChange={setCustomMode} />
              </Space>
            </div>

            {/* Compact Storage Selection */}
            <Form.Item label="Workspace" style={{ marginBottom: '16px' }}>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <Radio.Group
                  value={selectedStorage?.selection_type || (storageOptions.length > 0 ? 'existing' : 'create_new')}
                  onChange={(e) => {
                    const type = e.target.value;
                    if (type === 'existing' && storageOptions.length > 0) {
                      setSelectedStorage({
                        selection_type: 'existing',
                        storage_id: storageOptions[0]?.id,
                        storage_name: storageOptions[0]?.display_name
                      });
                    } else if (type === 'create_new') {
                      setSelectedStorage({
                        selection_type: 'create_new',
                        storage_class: 'standard'
                      });
                    }
                  }}
                  style={{ width: '100%' }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {storageOptions.length > 0 && (
                      <Radio value="existing" style={{ fontSize: '14px' }}>
                        📁 Use Existing Workspace ({storageOptions.length} available)
                      </Radio>
                    )}
                    <Radio value="create_new" style={{ fontSize: '14px' }}>
                      ✨ Create New Workspace
                    </Radio>
                  </div>
                </Radio.Group>

                {selectedStorage?.selection_type === 'existing' && storageOptions.length > 0 && (
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    placeholder="Choose workspace"
                    value={selectedStorage.storage_id}
                    onChange={(value) => {
                      const storage = storageOptions.find((s: StorageItem) => s.id === value);
                      if (storage) {
                        setSelectedStorage({
                          selection_type: 'existing',
                          storage_id: value,
                          storage_name: storage.display_name
                        });
                      }
                    }}
                    size="middle"
                  >
                    {storageOptions.map((storage: StorageItem) => (
                      <Option key={storage.id} value={storage.id}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontWeight: '500' }}>{storage.display_name}</span>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                            {storage.storage_class || 'standard'}
                          </span>
                        </div>
                      </Option>
                    ))}
                  </Select>
                )}

                {selectedStorage?.selection_type === 'create_new' && (
                  <div style={{ marginTop: '8px', padding: '12px', background: 'var(--glass-bg-secondary)', borderRadius: '6px', border: '1px solid var(--glass-border)' }}>
                    <Text style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      ✨ A new workspace will be created with standard storage configuration
                    </Text>
                  </div>
                )}
              </Space>
            </Form.Item>

            {/* Compact Warning */}
            {!selectedStorage || selectedStorage.selection_type === 'pending' ? (
              <Alert
                message="Select a workspace to continue"
                type="warning"
                showIcon={false}
                style={{ marginBottom: '16px', padding: '8px 12px', fontSize: '12px' }}
              />
            ) : null}

            {/* Compact Actions */}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '8px' }}>
              <Button onClick={() => setLaunchModalVisible(false)} disabled={launching} size="middle">
                Cancel
              </Button>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={launching}
                icon={<RocketOutlined />}
                disabled={!selectedStorage || selectedStorage.selection_type === 'pending'}
                size="middle"
              >
                {launching ? 'Launching...' : 'Launch'}
              </Button>
            </div>
          </Form>
        </Modal>
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
