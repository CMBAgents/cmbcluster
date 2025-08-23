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
  Upload,
  Select,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  DownloadOutlined,
  UploadOutlined,
  FileOutlined,
  SearchOutlined,
  EyeOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { UserFile } from '@/types';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function EnvironmentFiles() {
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const queryClient = useQueryClient();
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<UserFile | null>(null);
  const [searchText, setSearchText] = useState('');
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // Fetch user files
  const { data: filesData, isLoading, error } = useQuery({
    queryKey: ['userFiles'],
    queryFn: async () => {
      const response = await apiClient.listUserFiles();
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response.data || [];
    },
  });

  // Upload file mutation
  const uploadMutation = useMutation({
    mutationFn: async (values: {
      file: File;
      file_type: string;
      environment_variable_name?: string;
      container_path?: string;
    }) => {
      const response = await apiClient.uploadUserFile(
        values.file,
        values.file_type,
        values.environment_variable_name,
        values.container_path
      );
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userFiles'] });
      message.success('File uploaded successfully!');
      setIsModalVisible(false);
      form.resetFields();
      setFileList([]);
    },
    onError: (error: Error) => {
      message.error(`Failed to upload file: ${error.message}`);
    },
  });

  // Update file mutation
  const updateMutation = useMutation({
    mutationFn: async (values: {
      fileId: string;
      environment_variable_name?: string;
      container_path?: string;
    }) => {
      const response = await apiClient.updateUserFile(values.fileId, {
        environment_variable_name: values.environment_variable_name,
        container_path: values.container_path,
      });
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userFiles'] });
      message.success('File updated successfully!');
      setIsEditModalVisible(false);
      setEditingRecord(null);
      editForm.resetFields();
    },
    onError: (error: Error) => {
      message.error(`Failed to update file: ${error.message}`);
    },
  });

  // Delete file mutation
  const deleteMutation = useMutation({
    mutationFn: async (fileId: string) => {
      const response = await apiClient.deleteUserFile(fileId);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['userFiles'] });
      message.success('File deleted successfully!');
    },
    onError: (error: Error) => {
      message.error(`Failed to delete file: ${error.message}`);
    },
  });

  // Download file mutation
  const downloadMutation = useMutation({
    mutationFn: async (fileId: string) => {
      const response = await apiClient.downloadUserFile(fileId);
      if (response.status === 'error') {
        throw new Error(response.message);
      }
      return response;
    },
    onSuccess: (data, fileId) => {
      // Find the file to get its name
      const file = filesData?.find(f => f.id === fileId);
      const filename = file?.filename || 'download.json';
      
      // Create and trigger download
      const dataStr = JSON.stringify(data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
      message.success('File downloaded successfully!');
    },
    onError: (error: Error) => {
      message.error(`Failed to download file: ${error.message}`);
    },
  });

  const files: UserFile[] = filesData || [];

  // Filter files based on search
  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchText.toLowerCase()) ||
    file.file_type.toLowerCase().includes(searchText.toLowerCase()) ||
    (file.environment_variable_name && 
     file.environment_variable_name.toLowerCase().includes(searchText.toLowerCase()))
  );

  const handleUpload = (values: {
    file_type: string;
    environment_variable_name?: string;
    container_path?: string;
  }) => {
    if (fileList.length === 0) {
      message.error('Please select a file to upload');
      return;
    }

    const file = fileList[0].originFileObj as File;
    uploadMutation.mutate({
      file,
      ...values,
    });
  };

  const handleEdit = (record: UserFile) => {
    setEditingRecord(record);
    editForm.setFieldsValue({
      environment_variable_name: record.environment_variable_name,
      container_path: record.container_path,
    });
    setIsEditModalVisible(true);
  };

  const handleUpdate = (values: {
    environment_variable_name?: string;
    container_path?: string;
  }) => {
    if (!editingRecord) return;

    updateMutation.mutate({
      fileId: editingRecord.id,
      ...values,
    });
  };

  const handleDelete = (fileId: string) => {
    deleteMutation.mutate(fileId);
  };

  const handleDownload = (fileId: string) => {
    downloadMutation.mutate(fileId);
  };

  const getFileTypeColor = (fileType: string) => {
    switch (fileType) {
      case 'json': return 'blue';
      case 'gcp': return 'green';
      case 'config': return 'orange';
      default: return 'default';
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    return <FileOutlined />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const columns: ColumnsType<UserFile> = [
    {
      title: 'File Name',
      dataIndex: 'filename',
      key: 'filename',
      sorter: (a, b) => a.filename.localeCompare(b.filename),
      render: (text, record) => (
        <div className="flex items-center space-x-2">
          {getFileTypeIcon(record.file_type)}
          <Text className="text-white font-medium">{text}</Text>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type) => (
        <Tag color={getFileTypeColor(type)} className="uppercase">
          {type}
        </Tag>
      ),
      filters: [
        { text: 'JSON', value: 'json' },
        { text: 'GCP', value: 'gcp' },
        { text: 'Config', value: 'config' },
      ],
      onFilter: (value, record) => record.file_type === value,
    },
    {
      title: 'Environment Variable',
      dataIndex: 'environment_variable_name',
      key: 'environment_variable_name',
      render: (name) => name ? (
        <Text code className="text-green-400 font-mono text-sm">
          {name}
        </Text>
      ) : (
        <Text className="text-text-secondary italic">Not set</Text>
      ),
    },
    {
      title: 'Container Path',
      dataIndex: 'container_path',
      key: 'container_path',
      render: (path) => path ? (
        <Text code className="text-yellow-400 font-mono text-sm">
          {path}
        </Text>
      ) : (
        <Text className="text-text-secondary italic">Default</Text>
      ),
    },
    {
      title: 'Size',
      dataIndex: 'size_bytes',
      key: 'size_bytes',
      render: (size) => (
        <Text className="text-text-secondary">
          {formatFileSize(size)}
        </Text>
      ),
      sorter: (a, b) => a.size_bytes - b.size_bytes,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <Text className="text-text-secondary">
          {new Date(date).toLocaleDateString()}
        </Text>
      ),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Download file">
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.id)}
              loading={downloadMutation.isPending}
              className="text-blue-400 hover:text-blue-300"
            />
          </Tooltip>
          <Tooltip title="Edit file settings">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              className="text-green-400 hover:text-green-300"
            />
          </Tooltip>
          <Popconfirm
            title="Delete file"
            description={`Are you sure you want to delete "${record.filename}"?`}
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              className="text-red-400 hover:text-red-300"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const sectionStyle: React.CSSProperties = {
    background: 'rgba(26, 31, 46, 0.5)',
    borderRadius: '12px',
    padding: '24px',
    margin: '16px 0',
    borderLeft: '4px solid #4A9EFF',
  };

  const metricCardStyle: React.CSSProperties = {
    background: 'rgba(26, 31, 46, 0.8)',
    borderRadius: '12px',
    padding: '20px',
    textAlign: 'center',
    border: '1px solid #2D3748',
    transition: 'all 0.3s ease',
  };

  const totalSize = files.reduce((sum, file) => sum + file.size_bytes, 0);

  return (
    <div className="space-y-6">
      <div style={sectionStyle}>
        <Title level={3} className="text-white mb-4">
          Environment Files Management
        </Title>
        <Paragraph className="text-text-secondary mb-6">
          Upload and manage files that will be automatically available in your research environments. 
          These files can be mounted as environment variables or at specific container paths.
        </Paragraph>

        {/* Statistics */}
        <Row gutter={[16, 16]} className="mb-6">
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">Total Files</Title>
              <Title level={2} className="text-blue-400 mb-0">{files.length}</Title>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">Total Size</Title>
              <Title level={2} className="text-green-400 mb-0 text-lg">
                {formatFileSize(totalSize)}
              </Title>
            </div>
          </Col>
          
          <Col xs={24} sm={8}>
            <div style={metricCardStyle}>
              <Title level={4} className="text-white mb-2">File Types</Title>
              <Text className="text-text-secondary">
                {Array.from(new Set(files.map(f => f.file_type))).length} different types
              </Text>
            </div>
          </Col>
        </Row>

        <Divider className="border-border-primary" />

        {/* Actions Bar */}
        <div className="flex flex-wrap gap-4 mb-6">
          <Input
            placeholder="Search files..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="max-w-xs"
          />
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsModalVisible(true)}
          >
            Upload File
          </Button>
        </div>

        {/* Files Table */}
        <Card className="bg-background-tertiary border-border-primary">
          <Table
            columns={columns}
            dataSource={filteredFiles}
            rowKey="id"
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} files`,
            }}
            locale={{
              emptyText: searchText 
                ? 'No files found matching your search'
                : 'No files uploaded yet'
            }}
          />
        </Card>
      </div>

      {/* Upload File Modal */}
      <Modal
        title={
          <span className="text-white">
            <UploadOutlined className="mr-2" />
            Upload Environment File
          </span>
        }
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        footer={null}
        className="dark-modal"
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpload}
          className="mt-4"
        >
          <Form.Item
            label={<span className="text-white">Select File</span>}
            required
          >
            <Upload
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              maxCount={1}
              accept=".json,.yaml,.yml,.conf,.config,.txt"
            >
              <Button icon={<UploadOutlined />} className="w-full">
                Click to Upload File
              </Button>
            </Upload>
          </Form.Item>

          <Form.Item
            name="file_type"
            label={<span className="text-white">File Type</span>}
            rules={[{ required: true, message: 'Please select a file type' }]}
          >
            <Select placeholder="Select file type">
              <Option value="json">JSON - Configuration data</Option>
              <Option value="gcp">GCP - Google Cloud credentials</Option>
              <Option value="config">Config - General configuration</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="environment_variable_name"
            label={<span className="text-white">Environment Variable Name (Optional)</span>}
            help="If specified, the file path will be available as this environment variable"
          >
            <Input 
              placeholder="e.g., GOOGLE_APPLICATION_CREDENTIALS" 
              className="font-mono"
            />
          </Form.Item>

          <Form.Item
            name="container_path"
            label={<span className="text-white">Container Path (Optional)</span>}
            help="If specified, the file will be mounted at this path in the container"
          >
            <Input 
              placeholder="e.g., /app/config/credentials.json" 
              className="font-mono"
            />
          </Form.Item>
          
          <div className="flex justify-end space-x-2">
            <Button onClick={() => {
              setIsModalVisible(false);
              form.resetFields();
              setFileList([]);
            }}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit"
              loading={uploadMutation.isPending}
              disabled={fileList.length === 0}
            >
              Upload File
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Edit File Modal */}
      <Modal
        title={
          <span className="text-white">
            <EditOutlined className="mr-2" />
            Edit File Settings
          </span>
        }
        open={isEditModalVisible}
        onCancel={() => {
          setIsEditModalVisible(false);
          setEditingRecord(null);
          editForm.resetFields();
        }}
        footer={null}
        className="dark-modal"
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
          className="mt-4"
        >
          {editingRecord && (
            <div className="mb-4 p-3 bg-gray-800 rounded">
              <Text className="text-white font-medium">File: {editingRecord.filename}</Text>
              <br />
              <Text className="text-text-secondary text-sm">
                Type: {editingRecord.file_type.toUpperCase()} • 
                Size: {formatFileSize(editingRecord.size_bytes)}
              </Text>
            </div>
          )}

          <Form.Item
            name="environment_variable_name"
            label={<span className="text-white">Environment Variable Name (Optional)</span>}
            help="If specified, the file path will be available as this environment variable"
          >
            <Input 
              placeholder="e.g., GOOGLE_APPLICATION_CREDENTIALS" 
              className="font-mono"
            />
          </Form.Item>

          <Form.Item
            name="container_path"
            label={<span className="text-white">Container Path (Optional)</span>}
            help="If specified, the file will be mounted at this path in the container"
          >
            <Input 
              placeholder="e.g., /app/config/credentials.json" 
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
              Update Settings
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Help Section */}
      <Card 
        title="Environment Files Help"
        className="bg-background-tertiary border-border-primary"
        headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
      >
        <div className="space-y-4 text-text-secondary">
          <div>
            <Title level={5} className="text-white mb-2">What are Environment Files?</Title>
            <Text className="text-text-secondary">
              Environment files are configuration files, credentials, and other resources that are automatically 
              made available in your research environments. They can be mounted as environment variables or at 
              specific container paths.
            </Text>
          </div>
          
          <div>
            <Title level={5} className="text-white mb-2">File Types:</Title>
            <ul className="list-disc list-inside space-y-1 text-text-secondary">
              <li><strong>JSON</strong> - Configuration data, API responses, structured data</li>
              <li><strong>GCP</strong> - Google Cloud Platform credentials and service account keys</li>
              <li><strong>Config</strong> - General configuration files (YAML, INI, etc.)</li>
            </ul>
          </div>
          
          <div>
            <Title level={5} className="text-white mb-2">Usage Options:</Title>
            <ul className="list-disc list-inside space-y-1 text-text-secondary">
              <li><strong>Environment Variable</strong> - File path accessible via environment variable</li>
              <li><strong>Container Path</strong> - File mounted at specific location in container</li>
              <li><strong>Both</strong> - File available through both methods</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
