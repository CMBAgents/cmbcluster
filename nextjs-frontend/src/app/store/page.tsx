'use client';

import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { Card, Row, Col, Typography, Button, Space, Empty, Tag, Spin, Form, Image } from 'antd';
import {
  ShopOutlined,
  RocketOutlined,
  InfoCircleOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ApplicationImage, StorageItem, StorageSelection } from '@/types';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCommonNotifications } from '@/contexts/NotificationContext';
import { getImageUrlSync } from '@/lib/image-utils';

const { Title, Paragraph, Text } = Typography;

// Import LaunchEnvironmentModal component from environment management
// We'll copy it here to use the same well-tested modal
import { Modal, Switch, InputNumber, Select, Alert, Radio, Progress } from 'antd';
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
  const router = useRouter();
  const [imageKey, setImageKey] = useState(0); // Key to force image re-render

  // Pre-fetch API config to ensure images load correctly
  useEffect(() => {
    const preloadApiConfig = async () => {
      try {
        const response = await fetch('/api/config');
        if (response.ok) {
          const config = await response.json();
          // Store in window for immediate access
          if (typeof window !== 'undefined') {
            (window as any).__RUNTIME_CONFIG__ = config;
          }
          // Trigger image re-render after config is loaded
          setImageKey(prev => prev + 1);
        }
      } catch (error) {
        console.warn('Failed to preload API config:', error);
      }
    };
    preloadApiConfig();
  }, []);

  // Fetch real applications from API
  const { data: applications, isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const response = await apiClient.listApplications();

      // Handle different response formats
      if (response.status === 'success' && response.data) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response.applications) {
        return response.applications;
      } else {
        console.warn('Unexpected response format:', response);
        return [];
      }
    }
  });

  // Launch modal state
  const [launchModalVisible, setLaunchModalVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<ApplicationImage | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<keyof typeof PRESET_CONFIGS>('standard');
  const [customMode, setCustomMode] = useState(false);
  const [selectedStorage, setSelectedStorage] = useState<StorageSelection | null>(null);
  const [launchProgress, setLaunchProgress] = useState(0);
  const [launchStep, setLaunchStep] = useState('');
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { notifyEnvironmentAction, notifyError, notifySuccess } = useCommonNotifications();

  // Fetch storage options (same pattern as environment page)
  const { data: storageOptions } = useQuery({
    queryKey: ['storages'],
    queryFn: async () => {
      const response = await apiClient.listUserStorages();
      return response.storages || [];
    }
  });

  // Auto-select default storage option when modal opens
  React.useEffect(() => {
    if (launchModalVisible && (!selectedStorage || selectedStorage.selection_type === 'pending')) {
      if (storageOptions.length > 0) {
        // Auto-select first existing workspace
        setSelectedStorage({
          selection_type: 'existing',
          storage_id: storageOptions[0].id,
          storage_name: storageOptions[0].display_name
        });
      } else {
        // Auto-select create new with default storage class
        setSelectedStorage({
          selection_type: 'create_new',
          storage_class: 'standard'
        });
      }
    }
  }, [launchModalVisible, storageOptions, selectedStorage]);

  // Launch environment mutation with progress tracking (same as environment page)
  const launchMutation = useMutation({
    mutationFn: async (config: any) => {
      setLaunchStep('Validating configuration...');
      setLaunchProgress(25);
      
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setLaunchStep('Launching environment...');
      setLaunchProgress(75);
      
      const result = await apiClient.createEnvironment(config);
      setLaunchProgress(100);
      
      return result;
    },
    onSuccess: (result) => {
      setLaunchStep('Launch successful!');
      
      if (result.status === 'existing') {
        notifySuccess(
          'Environment Ready',
          `Environment already exists with ${PRESET_CONFIGS[selectedPreset].label} configuration!`
        );
      } else {
        notifySuccess(
          'Environment Created',
          `Environment created successfully with ${PRESET_CONFIGS[selectedPreset].label} configuration!`
        );
      }
      
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      setLaunchModalVisible(false);
      form.resetFields();
      setLaunchProgress(0);
      setLaunchStep('');
      
      // Redirect to environments page using Next.js router
      setTimeout(() => {
        router.push('/environments');
      }, 1500);
    },
    onError: (error: any) => {
      setLaunchStep('Launch failed!');
      console.error('Store environment launch failed:', error);
      
      // Extract detailed error message
      let errorMessage = 'Failed to launch environment';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      notifyError(
        'Launch Failed',
        errorMessage
      );
      setLaunchProgress(0);
    }
  });

  const handleLaunchEnvironment = (app: ApplicationImage) => {
    setSelectedApplication(app);
    setLaunchModalVisible(true);
  };

  const handleLaunch = async (values: any) => {
    const preset = PRESET_CONFIGS[selectedPreset];
    
    let config: any = {
      cpu_limit: preset.cpu_limit,
      memory_limit: preset.memory_limit,
      storage_size: preset.storage_size
    };

    if (customMode) {
      config = {
        cpu_limit: values.cpu_limit || preset.cpu_limit,
        memory_limit: values.memory_limit || preset.memory_limit,
        storage_size: values.storage_size || preset.storage_size
      };
    }

    // Add storage information
    if (selectedStorage && selectedStorage.selection_type !== 'pending') {
      if (selectedStorage.selection_type === 'existing') {
        config.storage_id = selectedStorage.storage_id;
        config.create_new_storage = false;
      } else if (selectedStorage.selection_type === 'create_new') {
        config.storage_id = null;
        config.create_new_storage = true;
        if (selectedStorage.storage_class) {
          config.storage_class = selectedStorage.storage_class;
        }
      }
    }

    // Add selected application
    if (selectedApplication) {
      config.application_id = selectedApplication.id;
    }
    
    launchMutation.mutate(config);
  };

  const handleViewDetails = (applicationId: string) => {
    const app = applications?.data?.find(a => a.id === applicationId);
    if (app) {
      Modal.info({
        title: app.name,
        content: (
          <div>
            <p><strong>Summary:</strong> {app.summary}</p>
            <p><strong>Category:</strong> {app.category}</p>
            <p><strong>Image:</strong> {app.image_path}</p>
            <p><strong>Port:</strong> {app.port}</p>
            {app.tags && app.tags.length > 0 && (
              <p><strong>Tags:</strong> {app.tags.map(tag => (
                <Tag key={tag} style={{ margin: '2px' }}>{tag}</Tag>
              ))}</p>
            )}
          </div>
        ),
        width: 600,
      });
    }
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
              {process.env.NODE_ENV === 'development' && (
                <div className="mt-4 text-left">
                  <Text className="text-xs text-gray-500">
                    <strong>Debug info:</strong> {JSON.stringify(error, null, 2)}
                  </Text>
                </div>
              )}
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
                    className="glass-card h-full overflow-hidden store-app-card"
                    bodyStyle={{ 
                      padding: '0',
                      display: 'flex',
                      flexDirection: 'column',
                      height: '100%'
                    }}
                    hoverable
                  >
                    <div className="h-full flex flex-col">
                      {/* Image Section - 30% of card */}
                      <div className="relative" style={{ height: '180px', overflow: 'hidden', borderRadius: '8px' }}>
                        {app.icon_url ? (
                          <Image
                            key={`${app.id}-${imageKey}`}
                            src={getImageUrlSync(app.icon_url)}
                            alt={app.name}
                            className="w-full h-full store-app-image"
                            style={{
                              objectFit: 'cover',
                              objectPosition: 'center',
                              backgroundColor: '#f8f9fa',
                              borderRadius: '8px'
                            }}
                            preview={false}
                            fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                          />
                        ) : (
                          <div 
                            className="w-full h-full flex items-center justify-center"
                            style={{
                              background: `linear-gradient(135deg, ${getCategoryColor(app.category)}15, ${getCategoryColor(app.category)}25)`,
                              border: `1px solid ${getCategoryColor(app.category)}30`
                            }}
                          >
                            <div className="text-center">
                              <div className="text-5xl mb-2" style={{ color: getCategoryColor(app.category) }}>
                                {getCategoryIcon(app.category)}
                              </div>
                              <div className="text-xs text-gray-500">
                                {app.category}
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Category Badge */}
                        <div className="absolute top-2 right-2">
                          {app.tags?.includes('default') && (
                            <Tag className="badge-success" size="small">
                              Default
                            </Tag>
                          )}
                        </div>
                      </div>

                      {/* Content Section - 70% of card */}
                      <div className="flex-1 p-4 flex flex-col">
                        {/* Application Info */}
                        <div className="flex-1">
                          <Title level={4} className="text-primary mb-2 leading-tight">
                            {app.name}
                          </Title>
                          <Paragraph className="text-secondary mb-3 text-sm leading-relaxed">
                            {app.summary}
                          </Paragraph>

                          {/* Tags */}
                          <div className="mb-4">
                            <div className="flex flex-wrap gap-1">
                              {app.tags?.slice(0, 3).map((tag) => (
                                <Tag 
                                  key={tag} 
                                  size="small"
                                  style={{
                                    backgroundColor: 'var(--glass-bg-secondary)',
                                    border: '1px solid var(--border-primary)',
                                    color: 'var(--text-secondary)',
                                    fontSize: '11px'
                                  }}
                                >
                                  {tag}
                                </Tag>
                              ))}
                              {app.tags && app.tags.length > 3 && (
                                <Tag size="small" style={{ fontSize: '11px' }}>+{app.tags.length - 3}</Tag>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex space-x-2 w-full mt-auto">
                          <Button
                            type="primary"
                            icon={<RocketOutlined />}
                            className="w-full"
                            size="middle"
                            onClick={() => handleLaunchEnvironment(app)}
                          >
                            Launch
                          </Button>
                        </div>
                      </div>
                    </div>
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
                  {process.env.NODE_ENV === 'development' && (
                    <div className="mt-4 text-left">
                      <Text className="text-xs text-gray-500">
                        <strong>Debug info:</strong> API call succeeded but returned empty array. 
                        Applications data: {JSON.stringify(applications)}
                      </Text>
                    </div>
                  )}
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

        {/* Launch Environment Modal - Using Environment Page Modal */}
        <LaunchEnvironmentModal
          visible={launchModalVisible}
          onCancel={() => {
            setLaunchModalVisible(false);
            setLaunchProgress(0);
            setLaunchStep('');
          }}
          onLaunch={handleLaunch}
          presetConfigs={PRESET_CONFIGS}
          selectedPreset={selectedPreset}
          onPresetChange={setSelectedPreset}
          customMode={customMode}
          onCustomModeChange={setCustomMode}
          selectedStorage={selectedStorage}
          onStorageChange={setSelectedStorage}
          storageOptions={storageOptions || []}
          launchProgress={launchProgress}
          launchStep={launchStep}
          loading={launchMutation.isPending}
          form={form}
          applications={[]} // Will be provided by the modal itself
          selectedApplication={selectedApplication}
          onApplicationChange={setSelectedApplication}
        />
      </div>
    </MainLayout>
  );
}

// Launch Environment Modal Component (copied from environment management)
interface LaunchEnvironmentModalProps {
  visible: boolean;
  onCancel: () => void;
  onLaunch: (values: any) => void;
  presetConfigs: typeof PRESET_CONFIGS;
  selectedPreset: keyof typeof PRESET_CONFIGS;
  onPresetChange: (preset: keyof typeof PRESET_CONFIGS) => void;
  customMode: boolean;
  onCustomModeChange: (custom: boolean) => void;
  selectedStorage: StorageSelection | null;
  onStorageChange: (storage: StorageSelection | null) => void;
  storageOptions: StorageItem[];
  launchProgress: number;
  launchStep: string;
  loading: boolean;
  form: any;
  // Application-related props
  applications: ApplicationImage[];
  selectedApplication: ApplicationImage | null;
  onApplicationChange: (application: ApplicationImage | null) => void;
}

function LaunchEnvironmentModal({
  visible,
  onCancel,
  onLaunch,
  presetConfigs,
  selectedPreset,
  onPresetChange,
  customMode,
  onCustomModeChange,
  selectedStorage,
  onStorageChange,
  storageOptions,
  launchProgress,
  launchStep,
  loading,
  form,
  applications,
  selectedApplication,
  onApplicationChange,
}: LaunchEnvironmentModalProps) {
  const preset = presetConfigs[selectedPreset];

  return (
    <Modal
      title={
        <Space>
          <RocketOutlined style={{ color: 'var(--interactive-primary)' }} />
          <span>Launch Environment</span>
          {selectedApplication && (
            <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              • {selectedApplication.name}
            </span>
          )}
        </Space>
      }
      open={visible}
      onCancel={onCancel}
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
      {loading && launchProgress > 0 && (
        <div className="mb-3 text-center">
          <Text style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{launchStep}</Text>
          <Progress percent={launchProgress} status="active" size="small" />
        </div>
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={onLaunch}
        initialValues={{
          preset: 'standard',
          cpu_limit: preset.cpu_limit,
          memory_limit: preset.memory_limit,
          storage_size: preset.storage_size,
        }}
      >
        {/* Compact Environment Type Selection */}
        <Form.Item label="Configuration" style={{ marginBottom: '12px' }}>
          <Select 
            value={selectedPreset} 
            onChange={onPresetChange}
            style={{ width: '100%' }}
            size="middle"
          >
            {Object.entries(presetConfigs).map(([key, config]) => (
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

        {/* Application Selection - Show selected application from store */}
        <Form.Item label="Research Environment" style={{ marginBottom: '12px' }}>
          <div style={{ 
            padding: '12px', 
            backgroundColor: 'var(--glass-bg-secondary)', 
            borderRadius: 'var(--radius-sm)', 
            border: '1px solid var(--glass-border)' 
          }}>
            {selectedApplication ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div 
                  style={{ 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary-500)',
                    flexShrink: 0
                  }}
                />
                <span style={{ fontWeight: '500' }}>{selectedApplication.name}</span>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                  {selectedApplication.category}
                </span>
              </div>
            ) : (
              <span style={{ color: 'var(--text-secondary)' }}>No application selected</span>
            )}
          </div>
          {selectedApplication && (
            <div style={{ marginTop: '8px', padding: '8px', backgroundColor: 'var(--glass-bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
              <Text style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {selectedApplication.summary}
              </Text>
            </div>
          )}
        </Form.Item>

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
            {preset.cpu_limit} CPU • {preset.memory_limit.replace('Gi', 'GB')} RAM • {preset.storage_size.replace('Gi', 'GB')} Storage
          </Text>
          <Space>
            <Text style={{ fontSize: '12px' }}>Custom</Text>
            <Switch size="small" checked={customMode} onChange={onCustomModeChange} />
          </Space>
        </div>

        {/* Compact Storage Selection */}
        <Form.Item label="Workspace" style={{ marginBottom: '16px' }}>
          <CompactStorageSelector
            storageOptions={storageOptions}
            selectedStorage={selectedStorage}
            onStorageChange={onStorageChange}
          />
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
          <Button onClick={onCancel} disabled={loading} size="middle">
            Cancel
          </Button>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading}
            icon={<RocketOutlined />}
            disabled={!selectedStorage || selectedStorage.selection_type === 'pending'}
            size="middle"
          >
            {loading ? 'Launching...' : 'Launch'}
          </Button>
        </div>
      </Form>
    </Modal>
  );
}

// Compact Storage Selector Component (copied from environment management)
function CompactStorageSelector({ storageOptions, selectedStorage, onStorageChange }: {
  storageOptions: StorageItem[];
  selectedStorage: StorageSelection | null;
  onStorageChange: (storage: StorageSelection | null) => void;
}) {
  // Auto-select default option when component loads
  React.useEffect(() => {
    if (!selectedStorage || selectedStorage.selection_type === 'pending') {
      if (storageOptions.length > 0) {
        // Auto-select first existing workspace
        onStorageChange({
          selection_type: 'existing',
          storage_id: storageOptions[0].id,
          storage_name: storageOptions[0].display_name
        });
      } else {
        // Auto-select create new with default storage class
        onStorageChange({
          selection_type: 'create_new',
          storage_class: 'standard'
        });
      }
    }
  }, [storageOptions, selectedStorage, onStorageChange]);

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="small">
      <Radio.Group
        value={selectedStorage?.selection_type || (storageOptions.length > 0 ? 'existing' : 'create_new')}
        onChange={(e) => {
          const type = e.target.value;
          if (type === 'existing' && storageOptions.length > 0) {
            onStorageChange({
              selection_type: 'existing',
              storage_id: storageOptions[0]?.id,
              storage_name: storageOptions[0]?.display_name
            });
          } else if (type === 'create_new') {
            onStorageChange({
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
            const storage = storageOptions.find(s => s.id === value);
            if (storage) {
              onStorageChange({
                selection_type: 'existing',
                storage_id: value,
                storage_name: storage.display_name
              });
            }
          }}
          size="middle"
        >
          {storageOptions.map((storage) => (
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
  );
}

export default function ApplicationStore() {
  return (
    <ProtectedRoute>
      <ApplicationStoreContent />
    </ProtectedRoute>
  );
}
