'use client';

import { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Statistic, 
  Alert,
  Spin,
  Table,
  Tag,
  Tooltip,
  Select,
  Modal,
  Form,
  InputNumber
} from 'antd';
import { 
  RocketOutlined, 
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
  RestartOutlined,
  ExternalLinkOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Environment } from '@/types';
import { apiClient } from '@/lib/api-client';
import { formatDateTime, getStatusColor, capitalize, getDisplayId } from '@/lib/utils';

const { Title, Text } = Typography;
const { Option } = Select;

interface EnvironmentTableRecord extends Environment {
  key: string;
}

export default function EnvironmentManagement() {
  const [launchModalVisible, setLaunchModalVisible] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState('standard');
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch environments
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
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Launch environment mutation
  const launchMutation = useMutation({
    mutationFn: async (config: any) => {
      return await apiClient.createEnvironment(config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      setLaunchModalVisible(false);
      form.resetFields();
    },
  });

  // Restart environment mutation
  const restartMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.restartEnvironment(envId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
  });

  // Stop environment mutation
  const stopMutation = useMutation({
    mutationFn: async (envId: string) => {
      return await apiClient.stopEnvironment(envId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
  });

  const presetConfigs = {
    light: {
      label: 'Light Analysis',
      description: '1 CPU, 2GB RAM - Simple tasks',
      cpu_limit: 1.0,
      memory_limit: '2Gi',
      storage_size: '10Gi',
    },
    standard: {
      label: 'Standard Research',
      description: '2 CPU, 4GB RAM - Recommended',
      cpu_limit: 2.0,
      memory_limit: '4Gi',
      storage_size: '20Gi',
    },
    heavy: {
      label: 'Heavy Computation',
      description: '4 CPU, 8GB RAM - Intensive tasks',
      cpu_limit: 4.0,
      memory_limit: '8Gi',
      storage_size: '50Gi',
    },
  };

  const handleLaunch = async (values: any) => {
    const preset = presetConfigs[selectedPreset as keyof typeof presetConfigs];
    const config = {
      ...preset,
      ...values,
    };
    
    launchMutation.mutate(config);
  };

  const handleRestart = (envId: string) => {
    Modal.confirm({
      title: 'Restart Environment',
      content: 'Are you sure you want to restart this environment?',
      onOk: () => restartMutation.mutate(envId),
    });
  };

  const handleStop = (envId: string) => {
    Modal.confirm({
      title: 'Stop Environment',
      content: 'Are you sure you want to stop this environment?',
      onOk: () => stopMutation.mutate(envId),
    });
  };

  const columns = [
    {
      title: 'Environment ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Text code className="font-mono">
          {getDisplayId(id)}
        </Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const { color } = getStatusColor(status);
        return (
          <Tag color={status === 'running' ? 'green' : status === 'pending' ? 'orange' : 'red'}>
            {capitalize(status)}
          </Tag>
        );
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatDateTime(date),
    },
    {
      title: 'Resources',
      dataIndex: 'resource_config',
      key: 'resources',
      render: (config: any) => (
        config ? (
          <Text type="secondary">
            {config.cpu_limit} CPU, {config.memory_limit}
          </Text>
        ) : 'N/A'
      ),
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      render: (url: string) => (
        url ? (
          <Button
            type="link"
            icon={<ExternalLinkOutlined />}
            href={url}
            target="_blank"
            size="small"
          >
            Access
          </Button>
        ) : 'N/A'
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: EnvironmentTableRecord) => (
        <Space size="small">
          <Tooltip title="Restart">
            <Button
              icon={<RestartOutlined />}
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
        </Space>
      ),
    },
  ];

  const runningCount = environments?.filter(env => env.status === 'running').length || 0;
  const totalCount = environments?.length || 0;

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
          <Title level={3} className="mb-1">Environment Management</Title>
          <Text type="secondary">
            Manage your research computing environments
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

      {/* Statistics */}
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Environments"
              value={totalCount}
              prefix={<RocketOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Running"
              value={runningCount}
              valueStyle={{ color: '#48BB78' }}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Available"
              value={totalCount - runningCount}
              valueStyle={{ color: '#718096' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Environments Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={environments?.map(env => ({ ...env, key: env.id })) || []}
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          locale={{
            emptyText: (
              <div className="py-12 text-center">
                <RocketOutlined style={{ fontSize: 48, color: '#718096', marginBottom: 16 }} />
                <div>
                  <Title level={4} type="secondary">No Environments</Title>
                  <Text type="secondary">
                    You don't have any environments yet. Launch your first environment to get started!
                  </Text>
                </div>
              </div>
            ),
          }}
        />
      </Card>

      {/* Launch Environment Modal */}
      <Modal
        title="Launch New Environment"
        open={launchModalVisible}
        onCancel={() => setLaunchModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleLaunch}
          initialValues={{
            preset: 'standard',
          }}
        >
          <Form.Item
            label="Environment Type"
            name="preset"
            rules={[{ required: true, message: 'Please select an environment type' }]}
          >
            <Select
              value={selectedPreset}
              onChange={setSelectedPreset}
              size="large"
            >
              {Object.entries(presetConfigs).map(([key, config]) => (
                <Option key={key} value={key}>
                  <div>
                    <div className="font-medium">{config.label}</div>
                    <div className="text-sm text-gray-500">{config.description}</div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="CPU Cores" name="cpu_limit">
                <InputNumber
                  min={0.5}
                  max={8}
                  step={0.5}
                  placeholder="2.0"
                  className="w-full"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Memory" name="memory_limit">
                <Select placeholder="4Gi" className="w-full">
                  <Option value="1Gi">1Gi</Option>
                  <Option value="2Gi">2Gi</Option>
                  <Option value="4Gi">4Gi</Option>
                  <Option value="8Gi">8Gi</Option>
                  <Option value="16Gi">16Gi</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Storage" name="storage_size">
                <Select placeholder="20Gi" className="w-full">
                  <Option value="10Gi">10Gi</Option>
                  <Option value="20Gi">20Gi</Option>
                  <Option value="50Gi">50Gi</Option>
                  <Option value="100Gi">100Gi</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <div className="flex justify-end space-x-2 mt-6">
            <Button onClick={() => setLaunchModalVisible(false)}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={launchMutation.isPending}
              icon={<RocketOutlined />}
            >
              Launch Environment
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
