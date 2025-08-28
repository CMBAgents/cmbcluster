'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  LoadingOutlined,
  PlusCircleOutlined,
  DatabaseOutlined,
  MonitorOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Environment, StorageSelection, StorageItem, ApplicationImage } from '@/types';
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
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState('environments');
  const [launchModalVisible, setLaunchModalVisible] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<keyof typeof PRESET_CONFIGS>('standard');
  const [customMode, setCustomMode] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedStorage, setSelectedStorage] = useState<StorageSelection | null>(null);
  const [launchProgress, setLaunchProgress] = useState(0);
  const [launchStep, setLaunchStep] = useState('');
  const [selectedApplication, setSelectedApplication] = useState<ApplicationImage | null>(null);
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
        
        // Debug pending environments
        const envs = response.environments || [];
        const pendingEnvs = envs.filter(env => env.status === 'pending');
        if (pendingEnvs.length > 0) {
          console.log('Pending environments detected:', pendingEnvs.map(env => ({
            id: env.id,
            env_id: env.env_id,
            status: env.status,
            created_at: env.created_at
          })));
          
          // Check for environments stuck in pending for more than 5 minutes
          const now = new Date();
          const stuckEnvs = pendingEnvs.filter(env => {
            const createdTime = new Date(env.created_at);
            const diffMinutes = (now.getTime() - createdTime.getTime()) / (1000 * 60);
            return diffMinutes > 5;
          });
          
          if (stuckEnvs.length > 0) {
            console.warn('Environments stuck in pending state for >5 minutes:', stuckEnvs);
          }
        }
        
        return envs;
      } catch (error) {
        console.error('Failed to fetch environments:', error);
        throw error;
      }
    },
    refetchInterval: (data) => {
      // Only refetch frequently if there are pending environments
      // Ensure data is an array before calling .some()
      const hasPendingEnvs = Array.isArray(data) && data.some(env => env.status === 'pending');
      return hasPendingEnvs ? 5000 : 30000; // 5s if pending, 30s otherwise
    },
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

  // Fetch available applications
  const { data: applications } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const response = await apiClient.listApplications();
      return response.data || [];
    }
  });

  // Handle app query parameter (from store page)
  useEffect(() => {
    const appId = searchParams.get('app');
    if (appId && applications) {
      const app = applications.find((app: ApplicationImage) => app.id === appId);
      if (app) {
        setSelectedApplication(app);
        setLaunchModalVisible(true);
      }
    }
  }, [searchParams, applications]);

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
      const result = await apiClient.restartEnvironment(envId);
      return result;
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
      const result = await apiClient.stopEnvironment(envId);
      return result;
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


  // Filter environments based on search and status
  const filteredEnvironments = (environments || []).filter((env) => {
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
        const getStatusBadge = (status: string) => {
          switch (status) {
            case 'running':
              return (
                <span className="status-badge running flex items-center gap-2">
                  <CheckCircleOutlined style={{ fontSize: '12px' }} />
                  Running
                </span>
              );
            case 'pending':
              return (
                <span className="status-badge pending flex items-center gap-2">
                  <LoadingOutlined spin style={{ fontSize: '12px' }} />
                  Starting
                </span>
              );
            case 'failed':
              return (
                <span className="status-badge failed flex items-center gap-2">
                  <ExclamationCircleOutlined style={{ fontSize: '12px' }} />
                  Failed
                </span>
              );
            case 'stopped':
              return (
                <span className="status-badge stopped flex items-center gap-2">
                  <StopOutlined style={{ fontSize: '12px' }} />
                  Stopped
                </span>
              );
            default:
              return (
                <span className="status-badge stopped flex items-center gap-2">
                  <StopOutlined style={{ fontSize: '12px' }} />
                  {capitalize(status)}
                </span>
              );
          }
        };
        
        return getStatusBadge(status);
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
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: Environment) => (
        <Space size="small">
          {record.url && (
            <Tooltip title="Access Environment">
              <Button
                type="link"
                icon={<LinkOutlined />}
                onClick={() => router.push(`/environment/${record.env_id || record.id}`)}
                size="small"
                style={{ padding: '4px 8px' }}
              />
             </Tooltip>
          )}
          
          <Tooltip title="Restart">
            <Button
              icon={<RedoOutlined />}
              size="small"
              onClick={() => handleRestart(record.env_id || record.id)}
              loading={restartMutation.isPending}
              style={{ padding: '4px 8px' }}
            />
          </Tooltip>
          
          <Tooltip title="Stop">
            <Button
              icon={<StopOutlined />}
              size="small"
              danger
              onClick={() => handleStop(record.env_id || record.id)}
              loading={stopMutation.isPending}
              style={{ padding: '4px 8px' }}
            />
          </Tooltip>
          
        </Space>
      ),
    },
  ];

  const runningCount = filteredEnvironments.filter(env => env.status === 'running').length;
  const totalCount = filteredEnvironments.length;
  const pendingCount = filteredEnvironments.filter(env => env.status === 'pending').length;
  const stoppedCount = filteredEnvironments.filter(env => env.status === 'stopped' || env.status === 'failed').length;
  
  // Calculate available slots based on a reasonable limit (e.g., 10 max environments per user)
  const MAX_ENVIRONMENTS = 10;
  const availableSlots = Math.max(0, MAX_ENVIRONMENTS - totalCount);

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
    <div className="space-y-4">
      {/* Compact Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} style={{ margin: '0 0 4px 0', fontSize: '24px' }}>Computing Environments</Title>
          <Text style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Manage and monitor your research environments
          </Text>
        </div>
        <Space>
          <Tooltip title="Refresh">
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
              className="glass-button"
            />
          </Tooltip>
          <Tooltip title="Launch Environment">
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={() => setLaunchModalVisible(true)}
              className="glass-button"
            />
          </Tooltip>
        </Space>
      </div>

      {/* Environment Tabs */}
      <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          size="large"
          className="professional-tabs"
        >
          <Tabs.TabPane 
            tab={
              <span className="flex items-center space-x-2">
                <RocketOutlined />
                <span>Environments</span>
              </span>
            } 
            key="environments"
          >
          {/* Compact Statistics Row */}
          <div className="mb-4">
            <Row gutter={[12, 12]}>
              <Col xs={12} sm={6} lg={6}>
                <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="icon-container primary" style={{ width: '36px', height: '36px', minWidth: '36px' }}>
                      <RocketOutlined style={{ fontSize: '18px' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--interactive-primary)', lineHeight: 1 }}>
                        {totalCount}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.2 }}>
                        Total
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
              <Col xs={12} sm={6} lg={6}>
                <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="icon-container success" style={{ width: '36px', height: '36px', minWidth: '36px' }}>
                      <PlayCircleOutlined style={{ fontSize: '18px' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--success-500)', lineHeight: 1 }}>
                        {runningCount}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.2 }}>
                        Running
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
              <Col xs={12} sm={6} lg={6}>
                <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="icon-container warning" style={{ width: '36px', height: '36px', minWidth: '36px' }}>
                      {pendingCount > 0 ? <LoadingOutlined spin style={{ fontSize: '18px' }} /> : <LoadingOutlined style={{ fontSize: '18px' }} />}
                    </div>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: pendingCount > 0 ? 'var(--warning-500)' : 'var(--text-disabled)', lineHeight: 1 }}>
                        {pendingCount}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.2 }}>
                        Pending
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
              <Col xs={12} sm={6} lg={6}>
                <Card className="glass-card" bodyStyle={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="icon-container error" style={{ width: '36px', height: '36px', minWidth: '36px' }}>
                      <StopOutlined style={{ fontSize: '18px' }} />
                    </div>
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--error-500)', lineHeight: 1 }}>
                        {stoppedCount}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.2 }}>
                        Stopped
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>
          </div>

          {/* Compact Search and Filters */}
          <div className="mb-4" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '12px 0' }}>
            <Search
              placeholder="Search environments..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
              style={{ maxWidth: '300px' }}
              size="middle"
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '140px' }}
              placeholder="Filter status"
              size="middle"
            >
              <Option value="all">All Status</Option>
              <Option value="running">Running</Option>
              <Option value="pending">Pending</Option>
              <Option value="stopped">Stopped</Option>
              <Option value="failed">Failed</Option>
            </Select>
            <div style={{ flex: 1 }} />
            <Text style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              {filteredEnvironments.length} of {environments?.length || 0} environments
            </Text>
          </div>

          {/* Environments Table */}
          <Card className="glass-card" bodyStyle={{ padding: '0' }}>
            <Table
              columns={columns}
              dataSource={filteredEnvironments.map(env => ({ 
                ...env, 
                key: env.env_id || env.id,
                // Ensure both id and env_id are available
                env_id: env.env_id || env.id,
                id: env.id || env.env_id
              }))}
              loading={isLoading}
              size="middle"
              scroll={{ x: 800 }}
              pagination={{
                pageSize: 15,
                size: 'small',
                showSizeChanger: false,
                showQuickJumper: false,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total}`,
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
                  <div style={{ padding: '32px', textAlign: 'center' }}>
                    <div className="icon-container primary mb-4" style={{ width: '48px', height: '48px', margin: '0 auto 16px' }}>
                      <RocketOutlined style={{ fontSize: '24px' }} />
                    </div>
                    <Title level={4} style={{ color: 'var(--text-secondary)', margin: '0 0 8px 0' }}>
                      {searchText || statusFilter !== 'all' ? 'No Results Found' : 'No Environments'}
                    </Title>
                    <Text style={{ color: 'var(--text-tertiary)', fontSize: '14px', display: 'block', marginBottom: '16px' }}>
                      {searchText || statusFilter !== 'all' 
                        ? 'Try adjusting your search or filters'
                        : "Launch your first environment to get started"
                      }
                    </Text>
                    {!searchText && statusFilter === 'all' && (
                      <Tooltip title="Launch Environment">
                        <Button 
                          type="primary" 
                          icon={<RocketOutlined />}
                          onClick={() => setLaunchModalVisible(true)}
                          className="glass-button"
                        />
                      </Tooltip>
                    )}
                  </div>
                ),
              }}
            />
            
            {/* Compact Bulk Actions */}
            {selectedRowKeys.length > 0 && (
              <div className="mt-3 px-4 py-3 glass-card" style={{ background: 'var(--primary-50)', border: '1px solid var(--primary-200)', borderRadius: '8px' }}>
                <div className="flex items-center justify-between">
                  <Text style={{ color: 'var(--primary-700)', fontSize: '14px', fontWeight: '500' }}>
                    {selectedRowKeys.length} selected
                  </Text>
                  <Space size="small">
                    <Tooltip title="Stop Selected">
                      <Button 
                        size="small"
                        icon={<StopOutlined />}
                        onClick={() => {
                          const selectedEnvs = filteredEnvironments.filter(env => 
                            selectedRowKeys.includes(env.env_id || env.id)
                          );
                          selectedEnvs.forEach(env => handleStop(env.env_id || env.id));
                          setSelectedRowKeys([]);
                        }}
                        loading={stopMutation.isPending}
                        danger
                      />
                    </Tooltip>
                    <Tooltip title="Restart Selected">
                      <Button 
                        size="small"
                        icon={<RedoOutlined />}
                        onClick={() => {
                          const selectedEnvs = filteredEnvironments.filter(env => 
                            selectedRowKeys.includes(env.env_id || env.id)
                          );
                          selectedEnvs.forEach(env => handleRestart(env.env_id || env.id));
                          setSelectedRowKeys([]);
                        }}
                        loading={restartMutation.isPending}
                        type="primary"
                      />
                    </Tooltip>
                    <Tooltip title="Clear Selection">
                      <Button size="small" icon={<DeleteOutlined />} onClick={() => setSelectedRowKeys([])} />
                    </Tooltip>
                  </Space>
                </div>
              </div>
            )}
          </Card>
        </Tabs.TabPane>

          <Tabs.TabPane 
            tab={
              <span className="flex items-center space-x-2">
                <DatabaseOutlined />
                <span>Storage</span>
              </span>
            } 
            key="storage"
          >
            <StorageManagement hideCreateButton={true} />
          </Tabs.TabPane>

          <Tabs.TabPane 
            tab={
              <span className="flex items-center space-x-2">
                <MonitorOutlined />
                <span>Monitoring</span>
              </span>
            } 
            key="monitoring"
          >
            <MonitoringDashboard />
          </Tabs.TabPane>
        </Tabs>
      </Card>

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
        applications={applications || []}
        selectedApplication={selectedApplication}
        onApplicationChange={setSelectedApplication}
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
        <Tooltip key="refresh" title="Refresh">
          <Button icon={<ReloadOutlined />} onClick={onRefresh} />
        </Tooltip>,
        environment.url && (
          <Tooltip key="access" title="Access Environment">
            <Button type="primary" icon={<LinkOutlined />} href={environment.url} target="_blank" />
          </Tooltip>
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
                  <Text>{formatDateTime(environment.updated_at || environment.created_at)}</Text>
                </div>
                {environment.url && (
                  <div>
                    <Text type="secondary">Access URL</Text>
                    <br />
                    <Tooltip title="Access Environment">
                      <Button 
                        type="link" 
                        icon={<LinkOutlined />} 
                        href={environment.url} 
                        target="_blank"
                        className="p-0"
                      />
                    </Tooltip>
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

        {/* Application Selection */}
        <Form.Item label="Research Environment" style={{ marginBottom: '12px' }}>
          <Select
            value={selectedApplication?.id || undefined}
            onChange={(appId) => {
              const app = applications?.find((a: ApplicationImage) => a.id === appId);
              onApplicationChange(app || null);
            }}
            placeholder="Select research environment (optional)"
            allowClear
            style={{ width: '100%' }}
            size="middle"
          >
            {applications?.map((app: ApplicationImage) => (
              <Option key={app.id} value={app.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div 
                    style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%',
                      backgroundColor: app.category === 'research' ? 'var(--primary-500)' : 
                                     app.category === 'ml' ? 'var(--success-500)' : 
                                     'var(--warning-500)',
                      flexShrink: 0
                    }}
                  />
                  <span style={{ fontWeight: '500' }}>{app.name}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                    {app.category}
                  </span>
                </div>
              </Option>
            ))}
          </Select>
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

// Compact Storage Selector Component
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
