'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import { Typography, Card, Row, Col, Button, Space, Tag, Progress, message, Spin, Modal, Select, Form, Input } from 'antd';
import { 
  RocketOutlined, 
  PlayCircleOutlined, 
  StopOutlined, 
  ReloadOutlined,
  SettingOutlined,
  CodeOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import apiClient from '@/lib/api-client';
import { Environment, StorageItem } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

function EnvironmentsPage() {
  const { data: session } = useSession();
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [storages, setStorages] = useState<StorageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // Fetch environments
  const fetchEnvironments = async () => {
    try {
      const response = await apiClient.listEnvironments();
      if (response.status === 'success' && response.environments) {
        setEnvironments(response.environments);
      } else {
        setEnvironments([]);
        if (response.message) {
          message.warning(`Failed to load environments: ${response.message}`);
        }
      }
    } catch (error) {
      console.error('Error fetching environments:', error);
      message.error('Failed to load environments');
      setEnvironments([]);
    }
  };

  // Fetch storages for environment creation
  const fetchStorages = async () => {
    try {
      const response = await apiClient.listUserStorages();
      if (response.status === 'success' && response.storages) {
        setStorages(response.storages);
      } else {
        setStorages([]);
      }
    } catch (error) {
      console.error('Error fetching storages:', error);
      setStorages([]);
    }
  };

  // Load data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchEnvironments(), fetchStorages()]);
      setLoading(false);
    };
    
    if (session) {
      loadData();
    }
  }, [session]);

  // Environment actions
  const handleEnvironmentAction = async (envId: string, action: 'restart' | 'stop', environmentName?: string) => {
    setActionLoading(`${action}_${envId}`);
    
    try {
      const response = action === 'restart' 
        ? await apiClient.restartEnvironment(envId)
        : await apiClient.stopEnvironment(envId);
        
      if (response.status === 'success') {
        message.success(`Environment ${action} initiated successfully`);
        await fetchEnvironments(); // Refresh environments
      } else {
        message.error(`Failed to ${action} environment: ${response.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error(`Error ${action}ing environment:`, error);
      message.error(`Failed to ${action} environment`);
    } finally {
      setActionLoading(null);
    }
  };

  const confirmEnvironmentAction = (envId: string, action: 'restart' | 'stop', environmentName?: string) => {
    confirm({
      title: `Are you sure you want to ${action} this environment?`,
      content: environmentName ? `Environment: ${environmentName}` : undefined,
      icon: <ExclamationCircleOutlined />,
      onOk: () => handleEnvironmentAction(envId, action, environmentName),
      okText: action === 'restart' ? 'Restart' : 'Stop',
      cancelText: 'Cancel',
    });
  };

  // Create environment
  const handleCreateEnvironment = async (values: any) => {
    setActionLoading('create');
    
    try {
      const config = {
        cpu_limit: getPresetConfig(values.preset).cpu_limit,
        memory_limit: getPresetConfig(values.preset).memory_limit,
        storage_size: getPresetConfig(values.preset).storage_size,
        storage_id: values.storage_id || undefined,
      };
      
      const response = await apiClient.createEnvironment(config);
      
      if (response.status === 'success' || response.status === 'created') {
        message.success('Environment created successfully!');
        setCreateModalVisible(false);
        form.resetFields();
        await fetchEnvironments(); // Refresh environments
      } else {
        message.error(`Failed to create environment: ${response.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating environment:', error);
      message.error('Failed to create environment');
    } finally {
      setActionLoading(null);
    }
  };

  const getPresetConfig = (preset: string) => {
    const configs: Record<string, any> = {
      'standard': { cpu_limit: 2.0, memory_limit: '4Gi', storage_size: '20Gi' },
      'heavy': { cpu_limit: 4.0, memory_limit: '8Gi', storage_size: '50Gi' },
      'light': { cpu_limit: 1.0, memory_limit: '2Gi', storage_size: '10Gi' },
    };
    return configs[preset] || configs.standard;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'starting': return 'processing';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayCircleOutlined />;
      case 'stopped': return <StopOutlined />;
      case 'starting': return <ReloadOutlined spin />;
      default: return <StopOutlined />;
    }
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return 'N/A';
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <Spin size="large" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex justify-between items-start">
          <div>
            <Title level={2} className="text-text-primary mb-2">
              Your Environments
            </Title>
            <Paragraph className="text-text-secondary">
              Manage your computational environments, launch new instances, and monitor resource usage.
            </Paragraph>
          </div>
          <Button 
            type="primary" 
            size="large" 
            icon={<RocketOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            New Environment
          </Button>
        </div>

        {/* Statistics */}
        {environments.length > 0 && (
          <Row gutter={[16, 16]} className="mb-6">
            <Col span={6}>
              <Card className="bg-background-secondary border-border-primary">
                <div className="text-center">
                  <Text className="text-text-secondary">Total Environments</Text>
                  <div className="text-2xl font-bold text-primary mt-1">{environments.length}</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="bg-background-secondary border-border-primary">
                <div className="text-center">
                  <Text className="text-text-secondary">Running</Text>
                  <div className="text-2xl font-bold text-green-500 mt-1">
                    {environments.filter(e => e.status === 'running').length}
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="bg-background-secondary border-border-primary">
                <div className="text-center">
                  <Text className="text-text-secondary">Stopped</Text>
                  <div className="text-2xl font-bold text-gray-500 mt-1">
                    {environments.filter(e => e.status === 'stopped').length}
                  </div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card className="bg-background-secondary border-border-primary">
                <div className="text-center">
                  <Text className="text-text-secondary">Active Storage</Text>
                  <div className="text-2xl font-bold text-blue-500 mt-1">{storages.length}</div>
                </div>
              </Card>
            </Col>
          </Row>
        )}

        {/* Environment Cards */}
        <Row gutter={[24, 24]}>
          {environments.map((env) => (
            <Col xs={24} lg={8} key={env.id || env.env_id}>
              <Card
                className="bg-background-secondary border-border-primary hover:shadow-lg transition-shadow h-full"
                title={
                  <div className="flex items-center justify-between">
                    <div>
                      <Text strong className="text-text-primary">
                        Environment {(env.env_id || env.id || '').substring(0, 8)}
                      </Text>
                      <br />
                      <Text type="secondary" className="text-sm">
                        Research Environment
                      </Text>
                    </div>
                    <Tag 
                      color={getStatusColor(env.status)} 
                      icon={getStatusIcon(env.status)}
                    >
                      {env.status.toUpperCase()}
                    </Tag>
                  </div>
                }
                actions={[
                  env.url ? (
                    <Button 
                      key="access" 
                      type="link" 
                      icon={<PlayCircleOutlined />}
                      onClick={() => window.open(env.url, '_blank')}
                    >
                      Access
                    </Button>
                  ) : null,
                  <Button 
                    key="restart" 
                    type="link" 
                    icon={<ReloadOutlined />}
                    loading={actionLoading === `restart_${env.env_id || env.id}`}
                    onClick={() => confirmEnvironmentAction(
                      env.env_id || env.id, 
                      'restart',
                      `Environment ${(env.env_id || env.id).substring(0, 8)}`
                    )}
                  >
                    Restart
                  </Button>,
                  <Button 
                    key="stop" 
                    type="link" 
                    icon={<StopOutlined />}
                    loading={actionLoading === `stop_${env.env_id || env.id}`}
                    onClick={() => confirmEnvironmentAction(
                      env.env_id || env.id, 
                      'stop',
                      `Environment ${(env.env_id || env.id).substring(0, 8)}`
                    )}
                  >
                    Stop
                  </Button>,
                ].filter(Boolean)}
              >
                <Space direction="vertical" size={16} className="w-full">
                  {/* Environment Info */}
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Text className="text-text-secondary text-sm">Created</Text>
                      <Text className="text-text-primary text-sm">
                        {formatDateTime(env.created_at)}
                      </Text>
                    </div>
                    <div className="flex justify-between">
                      <Text className="text-text-secondary text-sm">Last Activity</Text>
                      <Text className="text-text-primary text-sm">
                        {formatDateTime(env.last_activity || env.updated_at)}
                      </Text>
                    </div>
                    {env.resource_config && (
                      <>
                        <div className="flex justify-between">
                          <Text className="text-text-secondary text-sm">CPU Limit</Text>
                          <Text className="text-text-primary text-sm">
                            {env.resource_config.cpu_limit} cores
                          </Text>
                        </div>
                        <div className="flex justify-between">
                          <Text className="text-text-secondary text-sm">Memory Limit</Text>
                          <Text className="text-text-primary text-sm">
                            {env.resource_config.memory_limit}
                          </Text>
                        </div>
                      </>
                    )}
                  </div>
                </Space>
              </Card>
            </Col>
          ))}

          {/* Create New Environment Card */}
          <Col xs={24} lg={8}>
            <Card
              className="bg-background-secondary border-border-primary border-dashed hover:shadow-lg transition-all hover:border-primary cursor-pointer h-full"
              bodyStyle={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                minHeight: '300px'
              }}
              onClick={() => setCreateModalVisible(true)}
            >
              <Space direction="vertical" align="center" size={16}>
                <div className="text-6xl text-primary opacity-60">
                  <RocketOutlined />
                </div>
                <Title level={4} className="text-text-primary text-center mb-0">
                  Create New Environment
                </Title>
                <Text className="text-text-secondary text-center">
                  Launch a fresh computational environment tailored to your research needs
                </Text>
                <Button type="primary" size="large">
                  Get Started
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {environments.length === 0 && (
          <Card className="bg-background-secondary border-border-primary text-center py-12">
            <Space direction="vertical" size={16}>
              <RocketOutlined className="text-4xl text-gray-400" />
              <Title level={3} className="text-text-secondary">No Environments</Title>
              <Text className="text-text-secondary">
                You don't have any environments yet. Create your first environment to get started!
              </Text>
              <Button 
                type="primary" 
                size="large" 
                icon={<RocketOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                Create Your First Environment
              </Button>
            </Space>
          </Card>
        )}

        {/* Environment Templates */}
        <div>
          <Title level={3} className="text-text-primary mb-4">
            Popular Templates
          </Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
                onClick={() => {
                  form.setFieldsValue({ preset: 'standard' });
                  setCreateModalVisible(true);
                }}
              >
                <Space align="center">
                  <CodeOutlined className="text-primary text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Standard Research</Text>
                    <br />
                    <Text type="secondary" className="text-xs">2 CPU, 4GB RAM</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
                onClick={() => {
                  form.setFieldsValue({ preset: 'heavy' });
                  setCreateModalVisible(true);
                }}
              >
                <Space align="center">
                  <DatabaseOutlined className="text-green-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Heavy Computation</Text>
                    <br />
                    <Text type="secondary" className="text-xs">4 CPU, 8GB RAM</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
                onClick={() => {
                  form.setFieldsValue({ preset: 'light' });
                  setCreateModalVisible(true);
                }}
              >
                <Space align="center">
                  <RocketOutlined className="text-purple-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Light Analysis</Text>
                    <br />
                    <Text type="secondary" className="text-xs">1 CPU, 2GB RAM</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
                onClick={() => setCreateModalVisible(true)}
              >
                <Space align="center">
                  <SettingOutlined className="text-orange-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Custom</Text>
                    <br />
                    <Text type="secondary" className="text-xs">Configure yourself</Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </div>

        {/* Create Environment Modal */}
        <Modal
          title="Create New Environment"
          open={createModalVisible}
          onCancel={() => {
            setCreateModalVisible(false);
            form.resetFields();
          }}
          footer={null}
          width={600}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateEnvironment}
            initialValues={{ preset: 'standard' }}
          >
            <Form.Item
              name="preset"
              label="Environment Configuration"
              rules={[{ required: true, message: 'Please select a configuration' }]}
            >
              <Select placeholder="Select environment type">
                <Select.Option value="standard">
                  Standard Research - 2 CPU, 4GB RAM
                </Select.Option>
                <Select.Option value="heavy">
                  Heavy Computation - 4 CPU, 8GB RAM
                </Select.Option>
                <Select.Option value="light">
                  Light Analysis - 1 CPU, 2GB RAM
                </Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="storage_id"
              label="Workspace Storage (Optional)"
            >
              <Select 
                placeholder="Select existing storage or create new"
                allowClear
              >
                {storages.map((storage) => (
                  <Select.Option key={storage.id} value={storage.id}>
                    {storage.display_name} ({storage.storage_class})
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <div className="flex justify-end space-x-2">
              <Button 
                onClick={() => {
                  setCreateModalVisible(false);
                  form.resetFields();
                }}
              >
                Cancel
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={actionLoading === 'create'}
                icon={<RocketOutlined />}
              >
                Create Environment
              </Button>
            </div>
          </Form>
        </Modal>
      </div>
    </MainLayout>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <EnvironmentsPage />
    </ProtectedRoute>
  );
}
