'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Card, 
  Button, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Statistic, 
  Alert,
  Table,
  Tag,
  Tooltip,
  Select,
  Modal,
  Form,
  InputNumber,
  Tabs,
  Input,
  Switch,
  Slider,
  Divider,
  Progress,
  notification,
  Empty,
  Badge,
  Radio
} from 'antd';
import { 
  RocketOutlined, 
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
  RedoOutlined,
  LinkOutlined,
  SearchOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Environment, StorageSelection, StorageItem } from '@/types';
import { apiClient } from '@/lib/api-client';
import { formatDateTime, getStatusColor, capitalize, getDisplayId } from '@/lib/utils';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface EnvironmentTableRecord extends Environment {
  key: string;
}

// Preset configurations matching config.py exactly
const PRESET_CONFIGS = {
  light: {
    label: 'Light Analysis',
    description: '1 CPU, 2GB RAM - Simple tasks',
    cpu_limit: 1.0,
    memory_limit: '2Gi',
    storage_size: '25Gi',
    color: '#52c41a'
  },
  standard: {
    label: 'Standard Research', 
    description: '2 CPU, 4GB RAM - Recommended',
    cpu_limit: 2.0,
    memory_limit: '4Gi', 
    storage_size: '50Gi',
    color: '#1890ff'
  },
  heavy: {
    label: 'Heavy Computation',
    description: '4 CPU, 8GB RAM - Intensive tasks', 
    cpu_limit: 4.0,
    memory_limit: '8Gi',
    storage_size: '100Gi',
    color: '#ff7a00'
  }
};

export default function EnvironmentManagement() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('environments');
  const [launchModalVisible, setLaunchModalVisible] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<keyof typeof PRESET_CONFIGS>('standard');
  const [customMode, setCustomMode] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedStorage, setSelectedStorage] = useState<StorageSelection | null>(null);
  const [launchProgress, setLaunchProgress] = useState(0);
  const [launchStep, setLaunchStep] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);

  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch environments with real-time updates
  const { 
    data: environments, 
    isLoading, 
    error,
    refetch 
  } = useQuery({
    queryKey: ['environments'],
    queryFn: async () => {
      const response = await apiClient.listEnvironments();
      return response.environments || [];
    },
    refetchInterval: 10000, // Refresh every 10 seconds for real-time updates
    refetchIntervalInBackground: true,
  });

  // Fetch storage options
  const { data: storageOptions } = useQuery({
    queryKey: ['storages'],
    queryFn: async () => {
      const response = await apiClient.listUserStorages();
      return response.storages || [];
    }
  });

  // Launch environment mutation with progress tracking
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
        notification.success({
          message: 'Environment Ready',
          description: `Environment already exists with ${PRESET_CONFIGS[selectedPreset].label} configuration!`,
          placement: 'topRight'
        });
      } else {
        notification.success({
          message: 'Environment Created',
          description: `Environment created successfully with ${PRESET_CONFIGS[selectedPreset].label} configuration!`,
          placement: 'topRight'
        });
        
        // Show storage info
        if (selectedStorage?.selection_type === 'create_new') {
          notification.info({
            message: 'New Workspace Created',
            description: '✨ New workspace storage created successfully!',
            placement: 'topRight'
          });
        } else if (selectedStorage?.selection_type === 'existing') {
          notification.info({
            message: 'Workspace Connected',
            description: `📁 Using ${selectedStorage.storage_name}`,
            placement: 'topRight'
          });
        }
      }
      
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      setLaunchModalVisible(false);
      form.resetFields();
      setLaunchProgress(0);
      setLaunchStep('');
    },
    onError: (error: any) => {
      setLaunchStep('Launch failed!');
      notification.error({
        message: 'Launch Failed',
        description: error.message || 'Failed to launch environment',
        placement: 'topRight'
      });
      setLaunchProgress(0);
    }
  });

  // Restart environment mutation  
  const restartMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.restartEnvironment(envId);
    },
    onSuccess: () => {
      notification.success({
        message: 'Environment Restarting',
        description: 'Environment is restarting. Please check the Monitoring tab for status updates.',
        placement: 'topRight'
      });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: any) => {
      notification.error({
        message: 'Restart Failed',
        description: error.message || 'Failed to restart environment',
        placement: 'topRight'
      });
    }
  });

  // Stop environment mutation
  const stopMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.stopEnvironment(envId);
    },
    onSuccess: () => {
      notification.success({
        message: 'Environment Stopping',
        description: 'Environment is stopping. Please refresh to see updated status.',
        placement: 'topRight'
      });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: any) => {
      notification.error({
        message: 'Stop Failed', 
        description: error.message || 'Failed to stop environment',
        placement: 'topRight'
      });
    }
  });

  // Delete environment mutation
  const deleteMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.deleteEnvironment(envId);
    },
    onSuccess: () => {
      notification.success({
        message: 'Environment Deleted',
        description: 'Environment has been deleted successfully.',
        placement: 'topRight'
      });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    }
  });

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
    
    launchMutation.mutate(config);
  };

  const handleRestart = (envId: string) => {
    Modal.confirm({
      title: 'Restart Environment',
      content: 'Are you sure you want to restart this environment? This will stop and recreate the environment.',
      icon: <ExclamationCircleOutlined />,
      okText: 'Restart',
      okType: 'danger',
      onOk: () => restartMutation.mutate(envId),
    });
  };

  const handleStop = (envId: string) => {
    Modal.confirm({
      title: 'Stop Environment',
      content: 'Are you sure you want to stop this environment? This will gracefully shutdown the environment.',
      icon: <ExclamationCircleOutlined />,
      okText: 'Stop',
      okType: 'danger',
      onOk: () => stopMutation.mutate(envId),
    });
  };

  const handleDelete = (envId: string) => {
    Modal.confirm({
      title: 'Delete Environment',
      content: 'Are you sure you want to delete this environment? This action cannot be undone.',
      icon: <ExclamationCircleOutlined />,
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutate(envId),
    });
  };

  // Filter environments based on search and status
  const filteredEnvironments = environments?.filter((env) => {
    const matchesSearch = !searchText || 
      env.id.toLowerCase().includes(searchText.toLowerCase()) ||
      (env.env_id && env.env_id.toLowerCase().includes(searchText.toLowerCase()));
    
    const matchesStatus = statusFilter === 'all' || env.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  }) || [];

  const columns = [
    {
      title: 'Name',
      dataIndex: 'id',
      key: 'id',
      sorter: (a: Environment, b: Environment) => a.id.localeCompare(b.id),
      render: (id: string, record: Environment) => (
        <div>
          <Text strong className="font-mono">
            {getDisplayId(id)}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.env_id && record.env_id !== id ? `Full: ${getDisplayId(record.env_id)}` : ''}
          </Text>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      filters: [
        { text: 'Running', value: 'running' },
        { text: 'Pending', value: 'pending' },
        { text: 'Stopped', value: 'stopped' },
        { text: 'Failed', value: 'failed' },
      ],
      onFilter: (value: any, record: Environment) => record.status === value,
      render: (status: string) => {
        const statusConfig = {
          running: { color: 'success', icon: <CheckCircleOutlined /> },
          pending: { color: 'processing', icon: <LoadingOutlined spin /> },
          failed: { color: 'error', icon: <ExclamationCircleOutlined /> },
          stopped: { color: 'default', icon: <StopOutlined /> },
        };
        
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.stopped;
        
        return (
          <Badge 
            status={config.color as any} 
            text={
              <span>
                {config.icon} {capitalize(status)}
              </span>
            }
          />
        );
      },
    },
    {
      title: 'CPU',
      dataIndex: 'resource_config',
      key: 'cpu',
      render: (config: any) => (
        config?.cpu_limit ? `${config.cpu_limit} cores` : 'N/A'
      ),
      sorter: (a: Environment, b: Environment) => 
        (a.resource_config?.cpu_limit || 0) - (b.resource_config?.cpu_limit || 0),
    },
    {
      title: 'Memory', 
      dataIndex: 'resource_config',
      key: 'memory',
      render: (config: any) => config?.memory_limit || 'N/A',
    },
    {
      title: 'Storage',
      dataIndex: 'resource_config',
      key: 'storage',
      render: (config: any) => config?.storage_size || 'N/A',
    },
    {
      title: 'Created Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatDateTime(date),
      sorter: (a: Environment, b: Environment) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Environment) => (
        <Space size="small">
          {record.url && (
            <Tooltip title="Access Environment">
              <Button
                type="link"
                icon={<LinkOutlined />}
                href={record.url}
                target="_blank"
                size="small"
              />
            </Tooltip>
          )}
          
          <Tooltip title="View Details">
            <Button
              icon={<EyeOutlined />}
              size="small"
              onClick={() => {
                // Navigate to environment details page using Next.js router
                router.push(`/environments/${record.id}`);
              }}
            />
          </Tooltip>
          
          <Tooltip title="Restart">
            <Button
              icon={<RedoOutlined />}
              size="small"
              onClick={() => handleRestart(record.id)}
              loading={restartMutation.isPending}
            />
          </Tooltip>
          
          <Tooltip title="Stop">
            <Button
              icon={<StopOutlined />}
              size="small"
              danger
              onClick={() => handleStop(record.id)}
              loading={stopMutation.isPending}
            />
          </Tooltip>
          
          <Tooltip title="Delete">
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
              onClick={() => handleDelete(record.id)}
              loading={deleteMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const runningCount = filteredEnvironments.filter(env => env.status === 'running').length;
  const totalCount = filteredEnvironments.length;
  const pendingCount = filteredEnvironments.filter(env => env.status === 'pending').length;

  if (error) {
    return (
      <Alert
        message="Error Loading Environments"
        description="Failed to load environments. Please try again."
        type="error"
        showIcon
        action={
          <Button size="small" onClick={() => refetch()}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="mb-1">Research Computing Environments</Title>
          <Text type="secondary">
            Manage your research computing environments with real-time monitoring
          </Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<RocketOutlined />}
            onClick={() => setLaunchModalVisible(true)}
            size="large"
          >
            Launch Environment
          </Button>
        </Space>
      </div>

      {/* Tabs for different views */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane tab="Environments" key="environments">
          {/* Statistics */}
          <Row gutter={16} className="mb-6">
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Environments"
                  value={totalCount}
                  prefix={<RocketOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Running"
                  value={runningCount}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<PlayCircleOutlined />}
                  suffix={`/ ${totalCount}`}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Pending"
                  value={pendingCount}
                  valueStyle={{ color: '#faad14' }}
                  prefix={<LoadingOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Available"
                  value={totalCount - runningCount}
                  valueStyle={{ color: '#d9d9d9' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Search and Filters */}
          <Card className="mb-4">
            <Row gutter={16} align="middle">
              <Col span={8}>
                <Search
                  placeholder="Search environments..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  allowClear
                />
              </Col>
              <Col span={6}>
                <Select
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: '100%' }}
                  placeholder="Filter by status"
                >
                  <Option value="all">All Status</Option>
                  <Option value="running">Running</Option>
                  <Option value="pending">Pending</Option>
                  <Option value="stopped">Stopped</Option>
                  <Option value="failed">Failed</Option>
                </Select>
              </Col>
              <Col span={10}>
                <Text type="secondary">
                  {filteredEnvironments.length} of {environments?.length || 0} environments
                </Text>
              </Col>
            </Row>
          </Card>

          {/* Environments Table */}
          <Card>
            <Table
              columns={columns}
              dataSource={filteredEnvironments.map(env => ({ ...env, key: env.id }))}
              loading={isLoading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} environments`,
              }}
              rowSelection={{
                selectedRowKeys,
                onChange: (keys: React.Key[]) => setSelectedRowKeys(keys as string[]),
                selections: [
                  Table.SELECTION_ALL,
                  Table.SELECTION_INVERT,
                  Table.SELECTION_NONE,
                ],
              }}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      <span>
                        <Title level={4} type="secondary">No Environments Found</Title>
                        <Text type="secondary">
                          {searchText || statusFilter !== 'all' 
                            ? 'No environments match your search criteria'
                            : "You don't have any environments yet. Launch your first environment to get started!"
                          }
                        </Text>
                      </span>
                    }
                  >
                    {!searchText && statusFilter === 'all' && (
                      <Button 
                        type="primary" 
                        icon={<RocketOutlined />}
                        onClick={() => setLaunchModalVisible(true)}
                      >
                        Launch Environment
                      </Button>
                    )}
                  </Empty>
                ),
              }}
            />
            
            {/* Bulk Actions */}
            {selectedRowKeys.length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <Space>
                  <Text strong>{selectedRowKeys.length} environments selected</Text>
                  <Button 
                    size="small" 
                    onClick={() => {
                      selectedRowKeys.forEach(key => handleStop(key));
                      setSelectedRowKeys([]);
                    }}
                    loading={stopMutation.isPending}
                  >
                    Stop All
                  </Button>
                  <Button 
                    size="small" 
                    onClick={() => {
                      selectedRowKeys.forEach(key => handleRestart(key));
                      setSelectedRowKeys([]);
                    }}
                    loading={restartMutation.isPending}
                  >
                    Restart All
                  </Button>
                  <Button size="small" onClick={() => setSelectedRowKeys([])}>
                    Clear Selection
                  </Button>
                </Space>
              </div>
            )}
          </Card>
        </Tabs.TabPane>

        <Tabs.TabPane tab="Storage" key="storage">
          <StorageManagement />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Monitoring" key="monitoring">
          <EnvironmentMonitoring environments={environments || []} />
        </Tabs.TabPane>
      </Tabs>

      {/* Launch Environment Modal */}
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
      />
    </div>
  );
}

// Storage Management Component (placeholder)
function StorageManagement() {
  return (
    <div className="space-y-6">
      <Card>
        <Title level={4}>Storage Management</Title>
        <Text type="secondary">Storage management will be integrated here from the existing StorageManagement component.</Text>
      </Card>
    </div>
  );
}

// Environment Monitoring Component
interface EnvironmentMonitoringProps {
  environments: Environment[];
}

function EnvironmentMonitoring({ environments }: EnvironmentMonitoringProps) {
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [autoRefresh, setAutoRefresh] = useState(true);

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <Title level={4}>System Monitoring</Title>
          <Space>
            <Text type="secondary">Auto-refresh:</Text>
            <Switch checked={autoRefresh} onChange={setAutoRefresh} />
            <Select
              value={refreshInterval}
              onChange={setRefreshInterval}
              style={{ width: 120 }}
            >
              <Option value={5}>5 seconds</Option>
              <Option value={10}>10 seconds</Option>
              <Option value={30}>30 seconds</Option>
              <Option value={60}>1 minute</Option>
            </Select>
          </Space>
        </div>

        <Row gutter={16}>
          {environments.map((env) => (
            <Col span={12} key={env.id} className="mb-4">
              <MonitoringCard environment={env} />
            </Col>
          ))}
        </Row>

        {environments.length === 0 && (
          <Empty description="No environments to monitor" />
        )}
      </Card>
    </div>
  );
}

// Monitoring Card Component
interface MonitoringCardProps {
  environment: Environment;
}

function MonitoringCard({ environment }: MonitoringCardProps) {
  const statusConfig = {
    running: { color: '#52c41a', text: 'Running' },
    pending: { color: '#faad14', text: 'Starting' },
    failed: { color: '#f5222d', text: 'Failed' },
    stopped: { color: '#d9d9d9', text: 'Stopped' },
  };

  const status = statusConfig[environment.status as keyof typeof statusConfig] || statusConfig.stopped;

  return (
    <Card
      size="small"
      title={
        <div className="flex items-center justify-between">
          <span>Environment {getDisplayId(environment.id)}</span>
          <Badge color={status.color} text={status.text} />
        </div>
      }
    >
      <div className="space-y-2">
        <div className="flex justify-between">
          <Text type="secondary">Created:</Text>
          <Text>{formatDateTime(environment.created_at)}</Text>
        </div>
        
        <div className="flex justify-between">
          <Text type="secondary">Last Activity:</Text>
          <Text>{formatDateTime(environment.last_activity || environment.updated_at)}</Text>
        </div>

        {environment.resource_config && (
          <>
            <Divider />
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="CPU"
                  value={environment.resource_config.cpu_limit}
                  suffix="cores"
                  precision={1}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Memory"
                  value={environment.resource_config.memory_limit}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Storage"
                  value={environment.resource_config.storage_size}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
            </Row>
          </>
        )}

        {environment.url && (
          <>
            <Divider />
            <Button
              type="link"
              icon={<LinkOutlined />}
              href={environment.url}
              target="_blank"
              size="small"
            >
              Access Environment
            </Button>
          </>
        )}
      </div>
    </Card>
  );
}

// Launch Environment Modal Component
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
  form
}: LaunchEnvironmentModalProps) {
  const preset = presetConfigs[selectedPreset];

  return (
    <Modal
      title="Launch New Environment"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      {loading && launchProgress > 0 && (
        <Card className="mb-4">
          <div className="text-center">
            <Title level={4}>{launchStep}</Title>
            <Progress percent={launchProgress} status="active" />
          </div>
        </Card>
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
        {/* Environment Type Selection */}
        <Form.Item label="Environment Type" required>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(presetConfigs).map(([key, config]) => (
              <Card
                key={key}
                size="small"
                className={`cursor-pointer border-2 transition-all ${
                  selectedPreset === key 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => onPresetChange(key as keyof typeof presetConfigs)}
              >
                <div className="text-center">
                  <div 
                    className="w-4 h-4 rounded-full mx-auto mb-2"
                    style={{ backgroundColor: config.color }}
                  />
                  <Title level={5} className="mb-1">{config.label}</Title>
                  <Text type="secondary" className="text-xs">
                    {config.description}
                  </Text>
                </div>
              </Card>
            ))}
          </div>
        </Form.Item>

        {/* Custom Configuration Toggle */}
        <Form.Item>
          <div className="flex items-center justify-between">
            <Text strong>Resource Configuration</Text>
            <Space>
              <Text type="secondary">Custom:</Text>
              <Switch checked={customMode} onChange={onCustomModeChange} />
            </Space>
          </div>
        </Form.Item>

        {/* Resource Configuration */}
        <Card size="small" className="mb-4">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item 
                label="CPU Cores" 
                name="cpu_limit"
                rules={[{ required: customMode }]}
              >
                {customMode ? (
                  <Slider
                    min={0.5}
                    max={8}
                    step={0.5}
                    marks={{
                      0.5: '0.5',
                      2: '2',
                      4: '4', 
                      8: '8'
                    }}
                  />
                ) : (
                  <Text strong>{preset.cpu_limit} cores</Text>
                )}
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                label="Memory" 
                name="memory_limit"
                rules={[{ required: customMode }]}
              >
                {customMode ? (
                  <Select>
                    <Option value="1Gi">1GB</Option>
                    <Option value="2Gi">2GB</Option>
                    <Option value="4Gi">4GB</Option>
                    <Option value="8Gi">8GB</Option>
                    <Option value="16Gi">16GB</Option>
                    <Option value="32Gi">32GB</Option>
                  </Select>
                ) : (
                  <Text strong>{preset.memory_limit.replace('Gi', 'GB')}</Text>
                )}
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item 
                label="Storage" 
                name="storage_size"
                rules={[{ required: customMode }]}
              >
                {customMode ? (
                  <Select>
                    <Option value="10Gi">10GB</Option>
                    <Option value="25Gi">25GB</Option>
                    <Option value="50Gi">50GB</Option>
                    <Option value="100Gi">100GB</Option>
                    <Option value="200Gi">200GB</Option>
                    <Option value="500Gi">500GB</Option>
                  </Select>
                ) : (
                  <Text strong>{preset.storage_size.replace('Gi', 'GB')}</Text>
                )}
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Workspace Storage Selection */}
        <Form.Item label="Workspace Storage" required>
          <StorageSelector
            storageOptions={storageOptions}
            selectedStorage={selectedStorage}
            onStorageChange={onStorageChange}
          />
        </Form.Item>

        {/* Launch Warning */}
        {!selectedStorage || selectedStorage.selection_type === 'pending' ? (
          <Alert
            message="Storage Required"
            description="Please select a workspace before launching"
            type="warning"
            showIcon
            className="mb-4"
          />
        ) : null}

        {/* Actions */}
        <div className="flex justify-end space-x-2 mt-6">
          <Button onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading}
            icon={<RocketOutlined />}
            disabled={!selectedStorage || selectedStorage.selection_type === 'pending'}
          >
            {loading ? 'Launching...' : 'Launch Environment'}
          </Button>
        </div>
      </Form>
    </Modal>
  );
}

// Simple Storage Selector Component
function StorageSelector({ storageOptions, selectedStorage, onStorageChange }: {
  storageOptions: StorageItem[];
  selectedStorage: StorageSelection | null;
  onStorageChange: (storage: StorageSelection | null) => void;
}) {
  return (
    <div className="space-y-4">
      <Radio.Group
        value={selectedStorage?.selection_type || 'pending'}
        onChange={(e) => {
          const type = e.target.value;
          if (type === 'existing') {
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
      >
        <Space direction="vertical">
          <Radio value="existing" disabled={!storageOptions.length}>
            Use Existing Workspace ({storageOptions.length} available)
          </Radio>
          <Radio value="create_new">
            Create New Workspace
          </Radio>
        </Space>
      </Radio.Group>

      {selectedStorage?.selection_type === 'existing' && storageOptions.length > 0 && (
        <Select
          style={{ width: '100%' }}
          placeholder="Select workspace"
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
        >
          {storageOptions.map((storage) => (
            <Option key={storage.id} value={storage.id}>
              {storage.display_name} ({storage.storage_class})
            </Option>
          ))}
        </Select>
      )}

      {selectedStorage?.selection_type === 'create_new' && (
        <Select
          style={{ width: '100%' }}
          placeholder="Select storage class"
          value={selectedStorage.storage_class}
          onChange={(value) => {
            onStorageChange({
              ...selectedStorage,
              storage_class: value
            });
          }}
        >
          <Option value="standard">Standard (Best for frequently accessed data)</Option>
          <Option value="nearline">Nearline (Best for data accessed monthly)</Option>
          <Option value="coldline">Coldline (Best for archival data)</Option>
        </Select>
      )}
    </div>
  );
}
