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
import { useCommonNotifications } from '@/contexts/NotificationContext';
import StorageManagement from '@/components/storage/StorageManagement';
import MonitoringDashboard from '@/components/monitoring/MonitoringDashboard';

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
  const [detailsModalVisible, setDetailsModalVisible] = useState(false);
  const [selectedEnvironment, setSelectedEnvironment] = useState<Environment | null>(null);

  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { notifyEnvironmentAction, notifyError, notifySuccess } = useCommonNotifications();

  // Fetch environments with real-time updates
  const { 
    data: environments, 
    isLoading, 
    error,
    refetch 
  } = useQuery({
    queryKey: ['environments'],
    queryFn: async () => {
      try {
        const response = await apiClient.listEnvironments();
        console.log('Environments API response:', response);
        return response.environments || [];
      } catch (error) {
        console.error('Failed to fetch environments:', error);
        throw error;
      }
    },
    refetchInterval: 10000, // Refresh every 10 seconds for real-time updates
    refetchIntervalInBackground: true,
    retry: 3,
    retryDelay: 1000,
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
        notifySuccess(
          'Environment Ready',
          `Environment already exists with ${PRESET_CONFIGS[selectedPreset].label} configuration!`
        );
      } else {
        notifySuccess(
          'Environment Created',
          `Environment created successfully with ${PRESET_CONFIGS[selectedPreset].label} configuration!`
        );
        
        // Show storage info
        if (selectedStorage?.selection_type === 'create_new') {
          notifySuccess(
            'New Workspace Created',
            '✨ New workspace storage created successfully!'
          );
        } else if (selectedStorage?.selection_type === 'existing') {
          notifySuccess(
            'Workspace Connected',
            `📁 Using ${selectedStorage.storage_name}`
          );
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
      notifyError(
        'Launch Failed',
        error.message || 'Failed to launch environment'
      );
      setLaunchProgress(0);
    }
  });

  // Restart environment mutation  
  const restartMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.restartEnvironment(envId);
    },
    onSuccess: async () => {
      notifySuccess(
        'Environment Restarting',
        'Environment is restarting. Please check the Monitoring tab for status updates.'
      );
      // Force immediate refresh
      await refetch();
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: any) => {
      notifyError(
        'Restart Failed',
        error.message || 'Failed to restart environment'
      );
    }
  });

  // Stop environment mutation
  const stopMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.stopEnvironment(envId);
    },
    onSuccess: async () => {
      notifySuccess(
        'Environment Stopping',
        'Environment is stopping. Please refresh to see updated status.'
      );
      // Force immediate refresh
      await refetch();
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: any) => {
      notifyError(
        'Stop Failed',
        error.message || 'Failed to stop environment'
      );
    }
  });

  // Delete environment mutation
  const deleteMutation = useMutation({
    mutationFn: async (envId: string) => {
      console.log('Deleting environment:', envId);
      const result = await apiClient.deleteEnvironment(envId);
      console.log('Delete result:', result);
      return result;
    },
    onSuccess: async () => {
      notifySuccess(
        'Environment Deleted',
        'Environment has been deleted successfully.'
      );
      // Force immediate refresh
      await refetch();
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
    onError: (error: any) => {
      notifyError(
        'Delete Failed',
        error.message || 'Failed to delete environment'
      );
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
          <StorageManagement hideCreateButton={true} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Monitoring" key="monitoring">
          <MonitoringDashboard />
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

      {/* Environment Details Modal */}
      <EnvironmentDetailsModal
        visible={detailsModalVisible}
        environment={selectedEnvironment}
        onClose={() => {
          setDetailsModalVisible(false);
          setSelectedEnvironment(null);
        }}
        onRefresh={refetch}
      />
    </div>
  );
}



// Environment Details Modal Component
interface EnvironmentDetailsModalProps {
  visible: boolean;
  environment: Environment | null;
  onClose: () => void;
  onRefresh: () => void;
}

function EnvironmentDetailsModal({ visible, environment, onClose, onRefresh }: EnvironmentDetailsModalProps) {
  if (!environment) return null;

  const statusConfig = {
    running: { color: 'success', text: 'Running', icon: <CheckCircleOutlined /> },
    pending: { color: 'processing', text: 'Starting', icon: <LoadingOutlined spin /> },
    failed: { color: 'error', text: 'Failed', icon: <ExclamationCircleOutlined /> },
    stopped: { color: 'default', text: 'Stopped', icon: <StopOutlined /> },
  };

  const status = statusConfig[environment.status as keyof typeof statusConfig] || statusConfig.stopped;

  return (
    <Modal
      title={
        <div className="flex items-center space-x-3">
          <RocketOutlined className="text-blue-500" />
          <span>Environment Details</span>
          <Badge status={status.color as any} text={status.text} />
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="refresh" icon={<ReloadOutlined />} onClick={onRefresh}>
          Refresh
        </Button>,
        environment.url && (
          <Button key="access" type="primary" icon={<LinkOutlined />} href={environment.url} target="_blank">
            Access Environment
          </Button>
        ),
        <Button key="close" onClick={onClose}>
          Close
        </Button>,
      ].filter(Boolean)}
      width={800}
    >
      <div className="space-y-6">
        {/* Basic Information */}
        <Card size="small" title="Basic Information">
          <Row gutter={16}>
            <Col span={12}>
              <div className="space-y-3">
                <div>
                  <Text type="secondary">Environment ID</Text>
                  <br />
                  <Text strong className="font-mono">{getDisplayId(environment.id)}</Text>
                </div>
                <div>
                  <Text type="secondary">Full ID</Text>
                  <br />
                  <Text className="text-xs font-mono">{environment.env_id || environment.id}</Text>
                </div>
                <div>
                  <Text type="secondary">Status</Text>
                  <br />
                  <Badge status={status.color as any} text={
                    <span className="flex items-center space-x-1">
                      {status.icon}
                      <span>{status.text}</span>
                    </span>
                  } />
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="space-y-3">
                <div>
                  <Text type="secondary">Created</Text>
                  <br />
                  <Text>{formatDateTime(environment.created_at)}</Text>
                </div>
                <div>
                  <Text type="secondary">Last Updated</Text>
                  <br />
                  <Text>{formatDateTime(environment.updated_at)}</Text>
                </div>
                {environment.url && (
                  <div>
                    <Text type="secondary">Access URL</Text>
                    <br />
                    <Button 
                      type="link" 
                      icon={<LinkOutlined />} 
                      href={environment.url} 
                      target="_blank"
                      className="p-0"
                    >
                      Access Environment
                    </Button>
                  </div>
                )}
              </div>
            </Col>
          </Row>
        </Card>

        {/* Resource Configuration */}
        {environment.resource_config && (
          <Card size="small" title="Resource Configuration">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="CPU Cores"
                  value={environment.resource_config.cpu_limit}
                  precision={1}
                  suffix="cores"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Memory"
                  value={environment.resource_config.memory_limit}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Storage"
                  value={environment.resource_config.storage_size}
                />
              </Col>
            </Row>
          </Card>
        )}

        {/* Pod Information */}
        <Card size="small" title="Pod Information">
          <Row gutter={16}>
            <Col span={12}>
              <div className="space-y-3">
                <div>
                  <Text type="secondary">Pod Name</Text>
                  <br />
                  <Text className="font-mono">{environment.pod_name || 'N/A'}</Text>
                </div>
                <div>
                  <Text type="secondary">Namespace</Text>
                  <br />
                  <Text className="font-mono">{environment.namespace || 'N/A'}</Text>
                </div>
              </div>
            </Col>
            <Col span={12}>
              <div className="space-y-3">
                <div>
                  <Text type="secondary">Image</Text>
                  <br />
                  <Text className="text-xs">{environment.image || 'Default'}</Text>
                </div>
                <div>
                  <Text type="secondary">Port</Text>
                  <br />
                  <Text>{environment.port || 8501}</Text>
                </div>
              </div>
            </Col>
          </Row>
        </Card>

        {/* Additional Information */}
        <Card size="small" title="Additional Information">
          <div className="space-y-2">
            <Text>
              <strong>Environment Type:</strong> Research Computing Environment
            </Text>
            <br />
            <Text>
              <strong>Platform:</strong> Kubernetes-based Streamlit Application
            </Text>
            <br />
            {environment.last_activity && (
              <>
                <Text>
                  <strong>Last Activity:</strong> {formatDateTime(environment.last_activity)}
                </Text>
                <br />
              </>
            )}
            <Text type="secondary">
              This environment provides an isolated computing workspace for your research activities.
            </Text>
          </div>
        </Card>
      </div>
    </Modal>
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
