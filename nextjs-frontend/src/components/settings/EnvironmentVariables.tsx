'use client';

import React, { useState } from 'react';
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
  Empty
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  EyeInvisibleOutlined,
  SearchOutlined,
  CodeOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

interface EnvVarRecord {
  key: string;
  value: string;
  visible?: boolean;
}

export default function EnvironmentVariables() {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<EnvVarRecord | null>(null);
  const [searchText, setSearchText] = useState('');
  const [visibilityState, setVisibilityState] = useState<Record<string, boolean>>({});

  // Fetch environment variables
  const { data: envVarsData, isLoading } = useQuery({
    queryKey: ['userEnvVars'],
    queryFn: async () => {
      const response = await apiClient.getUserEnvVars();
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response.env_vars || {};
    },
  });

  // Create/Update environment variable mutation
  const saveMutation = useMutation({
    mutationFn: async ({ key, value, oldKey }: { key: string; value: string; oldKey?: string }) => {
      if (oldKey && oldKey !== key) {
        await apiClient.deleteUserEnvVar(oldKey);
      }
      const response = await apiClient.setUserEnvVar(key, value);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userEnvVars'] });
      message.success(`Environment variable ${editingRecord ? 'updated' : 'added'} successfully!`);
      setIsModalVisible(false);
      setEditingRecord(null);
      form.resetFields();
    },
    onError: (error: Error) => {
      message.error(`Failed to save variable: ${error.message}`);
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

  const handleEdit = (record: EnvVarRecord) => {
    setEditingRecord(record);
    form.setFieldsValue({
      key: record.key,
      value: record.value
    });
    setIsModalVisible(true);
  };

  const handleSave = async (values: { key: string; value: string }) => {
    saveMutation.mutate({
      key: values.key,
      value: values.value,
      oldKey: editingRecord?.key
    });
  };

  const columns: ColumnsType<EnvVarRecord> = [
    {
      title: 'Variable Name',
      dataIndex: 'key',
      key: 'key',
      width: '30%',
      sorter: (a, b) => a.key.localeCompare(b.key),
      render: (text: string) => (
        <Text style={{ fontFamily: 'mono', fontSize: '13px', color: 'var(--text-primary)' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      width: '40%',
      render: (text: string, record: EnvVarRecord) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Text 
            style={{ 
              fontFamily: 'mono', 
              fontSize: '13px', 
              color: 'var(--text-secondary)',
              maxWidth: '200px',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {visibilityState[record.key] ? text : '•'.repeat(Math.min(text.length, 20))}
          </Text>
          <Button
            type="text"
            size="small"
            icon={visibilityState[record.key] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            onClick={() => toggleVisibility(record.key)}
            style={{ color: 'var(--text-tertiary)' }}
          />
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: '30%',
      render: (_, record: EnvVarRecord) => (
        <Space size="small">
          <Tooltip title="Edit">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              style={{ color: 'var(--text-secondary)' }}
            />
          </Tooltip>
          <Popconfirm
            title="Delete variable?"
            description="This action cannot be undone."
            onConfirm={() => deleteMutation.mutate(record.key)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true, size: 'small' }}
            cancelButtonProps={{ size: 'small' }}
          >
            <Tooltip title="Delete">
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                danger
                loading={deleteMutation.isPending}
                style={{ color: 'var(--error-500)' }}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Header Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Input
            placeholder="Search variables..."
            prefix={<SearchOutlined style={{ color: 'var(--text-tertiary)' }} />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: '250px' }}
            size="middle"
          />
          <Text style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            {filteredRecords.length} variable{filteredRecords.length !== 1 ? 's' : ''}
          </Text>
        </div>
        <Tooltip title="Add Variable">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalVisible(true)}
            className="glass-button"
          />
        </Tooltip>
      </div>

      {/* Variables Table */}
      <Card className="glass-card" bodyStyle={{ padding: '0' }}>
        <Table
          columns={columns}
          dataSource={filteredRecords}
          loading={isLoading}
          pagination={{
            pageSize: 10,
            size: 'small',
            showSizeChanger: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total}`,
          }}
          size="middle"
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div style={{ textAlign: 'center' }}>
                    <div className="icon-container primary mb-3" style={{ width: '40px', height: '40px', margin: '0 auto 12px' }}>
                      <CodeOutlined style={{ fontSize: '20px' }} />
                    </div>
                    <Text style={{ color: 'var(--text-secondary)' }}>
                      {searchText ? 'No variables match your search' : 'No environment variables configured'}
                    </Text>
                  </div>
                }
              />
            ),
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingRecord ? 'Edit Environment Variable' : 'Add Environment Variable'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingRecord(null);
          form.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          style={{ marginTop: '16px' }}
        >
          <Form.Item
            name="key"
            label="Variable Name"
            rules={[
              { required: true, message: 'Variable name is required' },
              { pattern: /^[A-Z][A-Z0-9_]*$/, message: 'Use UPPERCASE letters, numbers, and underscores only' }
            ]}
          >
            <Input 
              placeholder="e.g., API_KEY, DATABASE_URL"
              style={{ fontFamily: 'mono' }}
            />
          </Form.Item>
          
          <Form.Item
            name="value"
            label="Variable Value"
            rules={[{ required: true, message: 'Variable value is required' }]}
          >
            <Input.TextArea
              placeholder="Enter the value for this environment variable"
              rows={3}
              style={{ fontFamily: 'mono' }}
            />
          </Form.Item>
          
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '24px' }}>
            <Button onClick={() => {
              setIsModalVisible(false);
              setEditingRecord(null);
              form.resetFields();
            }}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={saveMutation.isPending}
            >
              {editingRecord ? 'Update' : 'Add'} Variable
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}