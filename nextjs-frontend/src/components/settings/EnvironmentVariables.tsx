'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Modal, 
  Form, 
  Typography, 
  Space, 
  Popconfirm,
  message,
  Row,
  Col,
  Tag,
  Tooltip,
  Upload,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  EyeInvisibleOutlined,
  SearchOutlined,
  DownloadOutlined,
  UploadOutlined,
  CodeOutlined,
  BarChartOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface EnvVarRecord {
  key: string;
  value: string;
  visible?: boolean;
}

export default function EnvironmentVariables() {
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const queryClient = useQueryClient();
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<EnvVarRecord | null>(null);
  const [searchText, setSearchText] = useState('');
  const [visibilityState, setVisibilityState] = useState<Record<string, boolean>>({});

  // Fetch environment variables
  const { data: envVarsData, isLoading, error } = useQuery({
    queryKey: ['userEnvVars'],
    queryFn: async () => {
      const response = await apiClient.getUserEnvVars();
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response.env_vars || {};
    },
  });

  // Create environment variable mutation
  const createMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      const response = await apiClient.setUserEnvVar(key, value);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userEnvVars'] });
      message.success('Environment variable added successfully!');
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: (error: Error) => {
      message.error(`Failed to add variable: ${error.message}`);
    },
  });

  // Update environment variable mutation
  const updateMutation = useMutation({
    mutationFn: async ({ oldKey, newKey, value }: { oldKey: string; newKey: string; value: string }) => {
      // If key changed, delete old and create new
      if (oldKey !== newKey) {
        await apiClient.deleteUserEnvVar(oldKey);
      }
      const response = await apiClient.setUserEnvVar(newKey, value);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userEnvVars'] });
      message.success('Environment variable updated successfully!');
      setIsEditModalVisible(false);
      setEditingRecord(null);
      editForm.resetFields();
    },
    onError: (error: Error) => {
      message.error(`Failed to update variable: ${error.message}`);
    },
  });

  // Delete environment variable mutation
  const deleteMutation = useMutation({
    mutationFn: async (key: string) => {
      const response = await apiClient.deleteUserEnvVar(key);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userEnvVars'] });
      message.success('Environment variable deleted successfully!');
    },
    onError: (error: Error) => {
      message.error(`Failed to delete variable: ${error.message}`);
    },
  });

  // Convert envVarsData to table records
  const records: EnvVarRecord[] = envVarsData 
    ? Object.entries(envVarsData).map(([key, value]) => ({
        key,
        value,
        visible: visibilityState[key] || false,
      }))
    : [];

  // Filter records based on search
  const filteredRecords = records.filter(record =>
    record.key.toLowerCase().includes(searchText.toLowerCase()) ||
    record.value.toLowerCase().includes(searchText.toLowerCase())
  );

  const toggleVisibility = (key: string) => {
    setVisibilityState(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleAdd = (values: { key: string; value: string }) => {
    // Validate key format
    if (!/^[A-Za-z_][A-Za-z0-9_\-]*$/.test(values.key)) {
      message.error('Variable name must start with a letter or underscore and contain only letters, numbers, underscores, or dashes.');
      return;
    }

    createMutation.mutate(values);
  };

  const handleEdit = (record: EnvVarRecord) => {
    setEditingRecord(record);
    editForm.setFieldsValue(record);
    setIsEditModalVisible(true);
  };

  const handleUpdate = (values: { key: string; value: string }) => {
    if (!editingRecord) return;

    // Validate key format
    if (!/^[A-Za-z_][A-Za-z0-9_\-]*$/.test(values.key)) {
      message.error('Variable name must start with a letter or underscore and contain only letters, numbers, underscores, or dashes.');
      return;
    }

    updateMutation.mutate({
      oldKey: editingRecord.key,
      newKey: values.key,
      value: values.value,
    });
  };

  const handleDelete = (key: string) => {
    deleteMutation.mutate(key);
  };

  const handleExport = () => {
    if (!envVarsData) return;
    
    const dataStr = JSON.stringify(envVarsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'environment-variables.json';
    link.click();
    URL.revokeObjectURL(url);
    message.success('Environment variables exported successfully!');
  };

  const handleImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedData = JSON.parse(e.target?.result as string);
        
        // Validate imported data
        if (typeof importedData !== 'object' || Array.isArray(importedData)) {
          throw new Error('Invalid format: expected an object with key-value pairs');
        }

        // Import each variable
        Promise.all(
          Object.entries(importedData).map(([key, value]) =>
            apiClient.setUserEnvVar(key, String(value))
          )
        ).then(() => {
          queryClient.invalidateQueries({ queryKey: ['userEnvVars'] });
          message.success(`Imported ${Object.keys(importedData).length} environment variables!`);
        }).catch((error) => {
          message.error(`Failed to import variables: ${error.message}`);
        });
      } catch (error) {
        message.error('Failed to parse JSON file');
      }
    };
    reader.readAsText(file);
    return false; // Prevent upload
  };

  const columns: ColumnsType<EnvVarRecord> = [
    {
      title: 'Variable Name',
      dataIndex: 'key',
      key: 'key',
      sorter: (a, b) => a.key.localeCompare(b.key),
      render: (text) => (
        <Text code style={{ color: 'var(--primary-400)', fontFamily: 'var(--font-mono)' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value, record) => (
        <div className="flex items-center space-x-2">
          <Text className="flex-1" style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 'var(--text-sm)' }}>
            {visibilityState[record.key] 
              ? value 
              : '•'.repeat(Math.min(value.length, 12))
            }
          </Text>
          <Button
            type="text"
            size="small"
            icon={visibilityState[record.key] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            onClick={() => toggleVisibility(record.key)}
            style={{ color: 'var(--text-secondary)' }}
            className="hover:text-primary"
          />
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'value',
      key: 'status',
      render: (value) => (
        <Tag color={value.trim() ? 'success' : 'default'}>
          {value.trim() ? 'Active' : 'Empty'}
        </Tag>
      ),
      filters: [
        { text: 'Active', value: 'active' },
        { text: 'Empty', value: 'empty' },
      ],
      onFilter: (value, record) => 
        value === 'active' ? record.value.trim() !== '' : record.value.trim() === '',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit variable">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              style={{ color: 'var(--primary-400)' }}
              className="hover:text-primary-hover"
            />
          </Tooltip>
          <Popconfirm
            title="Delete variable"
            description={`Are you sure you want to delete "${record.key}"?`}
            onConfirm={() => handleDelete(record.key)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              style={{ color: 'var(--error-400)' }}
              className="hover:text-error-hover"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];


  const activeVars = records.filter(r => r.value.trim()).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header fade-in">
        <h1>Environment Variables</h1>
        <p>Configure environment variables that will be automatically injected into your research environments.</p>
      </div>

      <div className="env-card scale-in">

        {/* Statistics */}
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={24} sm={8}>
            <div className="metric-card fade-in">
              <div className="icon-container primary mb-3 mx-auto" style={{ width: '48px', height: '48px' }}>
                <CodeOutlined style={{ fontSize: '20px' }} />
              </div>
              <Title level={4} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>Total Variables</Title>
              <Title level={2} style={{ color: 'var(--primary-400)', margin: 0 }}>{records.length}</Title>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div className="metric-card fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="icon-container success mb-3 mx-auto" style={{ width: '48px', height: '48px' }}>
                <BarChartOutlined style={{ fontSize: '20px' }} />
              </div>
              <Title level={4} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>Active Variables</Title>
              <Title level={2} style={{ color: 'var(--success-400)', margin: 0 }}>{activeVars}</Title>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div className="metric-card fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="icon-container warning mb-3 mx-auto" style={{ width: '48px', height: '48px' }}>
                <RocketOutlined style={{ fontSize: '20px' }} />
              </div>
              <Title level={4} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>Last Updated</Title>
              <Text style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-lg)', fontWeight: 'var(--font-medium)' }}>
                {new Date().toLocaleDateString()}
              </Text>
            </div>
          </Col>
        </Row>

        <Divider style={{ borderColor: 'var(--border-primary)', margin: 'var(--spacing-2xl) 0' }} />

        {/* Actions Bar */}
        <div className="flex flex-wrap gap-4 mb-6 slide-up" style={{ animationDelay: '0.3s' }}>
          <Input
            placeholder="Search variables..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="max-w-xs input-field"
            style={{
              background: 'var(--glass-bg-secondary)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-lg)'
            }}
          />
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalVisible(true)}
            className="btn-primary"
            style={{
              height: 'auto',
              padding: 'var(--spacing-md) var(--spacing-xl)',
              borderRadius: 'var(--radius-lg)',
              fontWeight: 'var(--font-semibold)'
            }}
          >
            Add Variable
          </Button>
          
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={records.length === 0}
            className="btn-secondary"
            style={{
              height: 'auto',
              padding: 'var(--spacing-md) var(--spacing-xl)',
              borderRadius: 'var(--radius-lg)',
              fontWeight: 'var(--font-medium)'
            }}
          >
            Export
          </Button>
          
          <Upload
            accept=".json"
            beforeUpload={handleImport}
            showUploadList={false}
          >
            <Button 
              icon={<UploadOutlined />}
              className="btn-secondary"
              style={{
                height: 'auto',
                padding: 'var(--spacing-md) var(--spacing-xl)',
                borderRadius: 'var(--radius-lg)',
                fontWeight: 'var(--font-medium)'
              }}
            >
              Import
            </Button>
          </Upload>
        </div>

        {/* Variables Table */}
        <Card className="glass-card slide-up" style={{ animationDelay: '0.4s' }}>
          <Table
            columns={columns}
            dataSource={filteredRecords}
            rowKey="key"
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} variables`,
            }}
            locale={{
              emptyText: searchText 
                ? 'No variables found matching your search'
                : 'No environment variables configured yet'
            }}
          />
        </Card>
      </div>

      {/* Add Variable Modal */}
      <Modal
        title={
          <span className="text-white">
            <CodeOutlined className="mr-2" />
            Add Environment Variable
          </span>
        }
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        className="glass-card"
        style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur))',
          borderRadius: 'var(--radius-3xl)'
        }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAdd}
          className="mt-4"
        >
          <Form.Item
            name="key"
            label={<span className="font-medium" style={{ color: 'var(--text-primary)' }}>Variable Name</span>}
            rules={[
              { required: true, message: 'Please enter a variable name' },
              { 
                pattern: /^[A-Za-z_][A-Za-z0-9_\-]*$/, 
                message: 'Must start with letter/underscore, contain only letters, numbers, underscores, or dashes' 
              },
            ]}
          >
            <Input 
              placeholder="e.g., API_KEY, DATABASE_URL" 
              className="font-mono"
            />
          </Form.Item>
          
          <Form.Item
            name="value"
            label={<span className="font-medium" style={{ color: 'var(--text-primary)' }}>Variable Value</span>}
            rules={[{ required: true, message: 'Please enter a value' }]}
          >
            <TextArea 
              placeholder="Enter the value for this variable"
              rows={3}
              className="font-mono"
            />
          </Form.Item>
          
          <div className="flex justify-end space-x-2">
            <Button onClick={() => {
              setIsModalVisible(false);
              form.resetFields();
            }}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit"
              loading={createMutation.isPending}
            >
              Add Variable
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Edit Variable Modal */}
      <Modal
        title={
          <span className="text-white">
            <EditOutlined className="mr-2" />
            Edit Environment Variable
          </span>
        }
        open={isEditModalVisible}
        onCancel={() => {
          setIsEditModalVisible(false);
          setEditingRecord(null);
          editForm.resetFields();
        }}
        footer={null}
        className="glass-card"
        style={{
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur))',
          borderRadius: 'var(--radius-3xl)'
        }}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
          className="mt-4"
        >
          <Form.Item
            name="key"
            label={<span className="font-medium" style={{ color: 'var(--text-primary)' }}>Variable Name</span>}
            rules={[
              { required: true, message: 'Please enter a variable name' },
              { 
                pattern: /^[A-Za-z_][A-Za-z0-9_\-]*$/, 
                message: 'Must start with letter/underscore, contain only letters, numbers, underscores, or dashes' 
              },
            ]}
          >
            <Input 
              placeholder="e.g., API_KEY, DATABASE_URL" 
              className="font-mono"
            />
          </Form.Item>
          
          <Form.Item
            name="value"
            label={<span className="font-medium" style={{ color: 'var(--text-primary)' }}>Variable Value</span>}
            rules={[{ required: true, message: 'Please enter a value' }]}
          >
            <TextArea 
              placeholder="Enter the value for this variable"
              rows={3}
              className="font-mono"
            />
          </Form.Item>
          
          <div className="flex justify-end space-x-2">
            <Button onClick={() => {
              setIsEditModalVisible(false);
              setEditingRecord(null);
              editForm.resetFields();
            }}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit"
              loading={updateMutation.isPending}
            >
              Update Variable
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Help Section */}
      <Card 
        title={
          <span style={{ 
            color: 'var(--text-primary)', 
            fontSize: 'var(--text-xl)', 
            fontWeight: 'var(--font-semibold)' 
          }}>
            <CodeOutlined style={{ marginRight: 'var(--spacing-sm)' }} />
            Environment Variables Help
          </span>
        }
        className="env-card fade-in"
        style={{ animationDelay: '0.5s' }}
      >
        <div className="space-y-4" style={{ color: 'var(--text-secondary)' }}>
          <div>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>What are Environment Variables?</Title>
            <Text style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Environment variables are key-value pairs that are automatically injected into your research environments. 
              They're commonly used for API keys, database URLs, configuration settings, and secrets.
            </Text>
          </div>
          
          <div>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>Best Practices:</Title>
            <ul className="list-disc list-inside space-y-1" style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <li>Use UPPERCASE names with underscores (e.g., API_KEY, DATABASE_URL)</li>
              <li>Don't store sensitive data in variable names</li>
              <li>Use descriptive names that indicate the variable's purpose</li>
              <li>Test your variables in a development environment first</li>
              <li>Use the visibility toggle to show/hide sensitive values</li>
            </ul>
          </div>
          
          <div>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: 'var(--spacing-sm)' }}>Security Notes:</Title>
            <ul className="list-disc list-inside space-y-1" style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <li>All values are hidden by default for security</li>
              <li>Click the eye icon to temporarily reveal values when needed</li>
              <li>All environment variables are encrypted at rest</li>
              <li>Variables are only accessible within your research environments</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
