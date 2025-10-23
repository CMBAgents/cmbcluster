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
  Divider,
  Alert
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
  const [filePreview, setFilePreview] = useState<string>('');
  const [isGcpKey, setIsGcpKey] = useState(false);

  // Fetch user files
  const { data: filesData, isLoading, error } = useQuery({
    queryKey: ['userFiles'],
    queryFn: async () => {
      const response = await apiClient.listUserFiles();
      // API returns array directly for user files
      return Array.isArray(response) ? response : [];
    },
  });

  // Upload file mutation
  const uploadMutation = useMutation({
    mutationFn: async (values: {
      file: File;
      file_type: string;
      environment_variable_name: string;
      container_path?: string;
    }) => {
      // Basic validation
      if (values.file.size > 1024 * 1024) {
        throw new Error('File size exceeds 1MB limit');
      }

  

      const response = await apiClient.uploadUserFile(
        values.file,
        values.file_type,
        values.environment_variable_name,
        values.container_path
      );
      
      
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
      console.error('Upload error:', error);
      console.error('Upload error details:', {
        message: error.message,
        name: error.name,
        stack: error.stack,
        cause: (error as any)?.cause,
        response: (error as any)?.response
      });
      
      let errorMessage = error.message;
      if ((error as any)?.response?.data?.error) {
        errorMessage = (error as any).response.data.error;
      } else if ((error as any)?.response?.statusText) {
        errorMessage = `${(error as any).response.status}: ${(error as any).response.statusText}`;
      }
      
      message.error(`Failed to upload file: ${errorMessage}`);
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
      return response;
    },
    onSuccess: (data, fileId) => {
      // Find the file to get its name
      const file = filesData?.find(f => f.id === fileId);
      const filename = file?.file_name || 'download.json';
      
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
    file.file_name.toLowerCase().includes(searchText.toLowerCase()) ||
    file.file_type.toLowerCase().includes(searchText.toLowerCase()) ||
    (file.environment_variable_name && 
     file.environment_variable_name.toLowerCase().includes(searchText.toLowerCase()))
  );

  // Handle file selection and validation
  const handleFileChange = async (info: any) => {
    let newFileList = [...info.fileList];
    
    // Limit to one file
    newFileList = newFileList.slice(-1);
    
    if (newFileList.length > 0) {
      const file = newFileList[0].originFileObj;
      
      // Validate file size
      if (file.size > 1024 * 1024) {
        message.error('File size exceeds 1MB limit');
        newFileList = [];
        setFilePreview('');
        setIsGcpKey(false);
      } else {
        try {
          // Read file content for preview and validation
          const content = await file.text();
          const jsonContent = JSON.parse(content);
          
          // Detect GCP service account - check for all required fields
          const requiredGcpFields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
          ];
          
          const isGcp = (
            jsonContent.type === 'service_account' &&
            requiredGcpFields.every(field => field in jsonContent && jsonContent[field])
          );
          
         
          
          setIsGcpKey(isGcp);
          setFilePreview(JSON.stringify(jsonContent, null, 2));
          
          // Auto-update form if GCP key is detected
          if (isGcp) {
           
          } else {
            form.setFieldsValue({
              file_type: 'custom_json',
              container_path: `/mnt/user-files/${file.name}`
            });
          }
          
        } catch (e) {
          message.error('Invalid JSON file');
          newFileList = [];
          setFilePreview('');
          setIsGcpKey(false);
        }
      }
    } else {
      setFilePreview('');
      setIsGcpKey(false);
    }
    
    setFileList(newFileList);
  };

  const handleUpload = (values: {
    file_type: string;
    environment_variable_name: string;
    container_path?: string;
  }) => {
   

    if (fileList.length === 0) {
      console.error('No files selected');
      message.error('Please select a file to upload');
      return;
    }

    const file = fileList[0].originFileObj as File;
  

    if (!file) {
      console.error('File object is null or undefined');
      message.error('Invalid file selected');
      return;
    }
    
    const trimmedEnvVar = values.environment_variable_name?.trim();
    
    // Environment variable name is required
    if (!trimmedEnvVar) {
      console.error('Environment variable name is empty');
      message.error('Environment variable name is required');
      return;
    }
    
    // Check for duplicate environment variable names
    const existingEnvVar = files.find(f => f.environment_variable_name === trimmedEnvVar);
    if (existingEnvVar) {
      console.error('Duplicate environment variable:', trimmedEnvVar);
      message.error(`Environment variable "${trimmedEnvVar}" already exists for file "${existingEnvVar.file_name}"`);
      return;
    }

    // Auto-detect GCP service account based on file_type
    let autoContainerPath = values.container_path;
    if (values.file_type === 'gcp_service_account' && !autoContainerPath) {
      autoContainerPath = '/app/secrets/gcp_service_account.json';
    } else if (values.file_type === 'custom_json' && !autoContainerPath) {
      autoContainerPath = `/mnt/user-files/${file.name}`;
    }

    const finalContainerPath = autoContainerPath || values.container_path;

    // Check for duplicate container paths
    if (finalContainerPath) {
      const existingPath = files.find(f => f.container_path === finalContainerPath);
      if (existingPath) {
        console.error('Duplicate container path:', finalContainerPath);
        message.error(`Container path "${finalContainerPath}" already exists for file "${existingPath.file_name}"`);
        return;
      }
    }

    const uploadData = {
      file,
      file_type: values.file_type,
      environment_variable_name: trimmedEnvVar,
      container_path: finalContainerPath,
    };

 

    uploadMutation.mutate(uploadData);
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

    const trimmedEnvVar = values.environment_variable_name?.trim();
    
    // Check for duplicate environment variable names (excluding current file)
    if (trimmedEnvVar) {
      const existingEnvVar = files.find(f => 
        f.environment_variable_name === trimmedEnvVar && f.id !== editingRecord.id
      );
      if (existingEnvVar) {
        message.error(`Environment variable "${trimmedEnvVar}" already exists for file "${existingEnvVar.file_name}"`);
        return;
      }
    }

    // Check for duplicate container paths (excluding current file)
    if (values.container_path?.trim()) {
      const existingPath = files.find(f => 
        f.container_path === values.container_path && f.id !== editingRecord.id
      );
      if (existingPath) {
        message.error(`Container path "${values.container_path}" already exists for file "${existingPath.file_name}"`);
        return;
      }
    }

    updateMutation.mutate({
      fileId: editingRecord.id,
      environment_variable_name: trimmedEnvVar,
      container_path: values.container_path?.trim(),
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
      case 'custom_json': return 'blue';
      case 'gcp_service_account': return 'green';
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
      dataIndex: 'file_name',
      key: 'file_name',
      sorter: (a, b) => a.file_name.localeCompare(b.file_name),
      render: (text, record) => (
        <div className="flex items-center space-x-2">
          {getFileTypeIcon(record.file_type)}
          <Text strong>{text}</Text>
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
        { text: 'JSON', value: 'custom_json' },
        { text: 'GCP', value: 'gcp_service_account' },
      ],
      onFilter: (value, record) => record.file_type === value,
    },
    {
      title: 'Environment Variable',
      dataIndex: 'environment_variable_name',
      key: 'environment_variable_name',
      render: (name) => name ? (
        <Text code style={{ color: 'var(--success-600)', fontFamily: 'monospace', fontSize: '12px' }}>
          {name}
        </Text>
      ) : (
        <Text style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Not set</Text>
      ),
    },
    {
      title: 'Container Path',
      dataIndex: 'container_path',
      key: 'container_path',
      render: (path) => path ? (
        <Text code style={{ color: 'var(--warning-600)', fontFamily: 'monospace', fontSize: '12px' }}>
          {path}
        </Text>
      ) : (
        <Text style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Default</Text>
      ),
    },
    {
      title: 'Size',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size) => (
        <Text style={{ color: 'var(--text-secondary)' }}>
          {formatFileSize(size)}
        </Text>
      ),
      sorter: (a, b) => a.file_size - b.file_size,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <Text style={{ color: 'var(--text-secondary)' }}>
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
            />
          </Tooltip>
          <Tooltip title="Edit file settings">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete file"
            description={`Are you sure you want to delete "${record.file_name}"?`}
            onConfirm={() => handleDelete(record.id)}
            okText="Delete"
            cancelText="Cancel"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              danger
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const totalSize = files.reduce((sum, file) => sum + file.file_size, 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="glass-card">
        <div className="flex justify-between items-start mb-4">
          <div>
            <Title level={3} style={{ margin: 0, color: 'var(--text-primary)' }}>
              Environment Files
            </Title>
            <Text style={{ color: 'var(--text-secondary)' }}>
              Upload and manage configuration files for your research environments
            </Text>
          </div>
          <Tooltip title="Upload File">
            <Button
              type="primary"
              shape="circle"
              icon={<PlusOutlined />}
              onClick={() => setIsModalVisible(true)}
              className="glass-button"
            />
          </Tooltip>
        </div>

        <Paragraph style={{ color: 'var(--text-secondary)', marginBottom: 0 }}>
          Files can be mounted as environment variables or at specific container paths in your environments.
        </Paragraph>
      </Card>

      {/* Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container primary mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <FileOutlined style={{ fontSize: '24px' }} />
            </div>
            <Title level={2} style={{ margin: 0, color: 'var(--primary-600)' }}>
              {files.length}
            </Title>
            <Text style={{ color: 'var(--text-secondary)' }}>Total Files</Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container success mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <UploadOutlined style={{ fontSize: '24px' }} />
            </div>
            <Title level={2} style={{ margin: 0, color: 'var(--success-600)' }}>
              {formatFileSize(totalSize)}
            </Title>
            <Text style={{ color: 'var(--text-secondary)' }}>Total Size</Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="glass-card text-center">
            <div className="icon-container warning mb-3" style={{ width: '48px', height: '48px', margin: '0 auto' }}>
              <InfoCircleOutlined style={{ fontSize: '24px' }} />
            </div>
            <Title level={2} style={{ margin: 0, color: 'var(--warning-600)' }}>
              {Array.from(new Set(files.map(f => f.file_type))).length}
            </Title>
            <Text style={{ color: 'var(--text-secondary)' }}>File Types</Text>
          </Card>
        </Col>
      </Row>

      {/* Search and Files Table */}
      <Card className="glass-card">
        <div className="flex justify-between items-center mb-4">
          <Title level={4} style={{ margin: 0, color: 'var(--text-primary)' }}>
            Uploaded Files
          </Title>
          <Input
            placeholder="Search files..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 240 }}
            allowClear
          />
        </div>

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

      {/* Upload File Modal */}
      <Modal
        title="Upload Environment File"
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpload}
          className="mt-4"
        >
          <Form.Item
            label="Select File"
            required
          >
            <Upload
              fileList={fileList}
              onChange={handleFileChange}
              beforeUpload={() => false}
              maxCount={1}
              accept=".json"
            >
              <Button icon={<UploadOutlined />} className="w-full">
                Click to Upload JSON File (Max 1MB)
              </Button>
            </Upload>
            
            {/* File size warning */}
            <Text type="secondary" className="text-xs block mt-1">
              💡 File size limit: 1MB. Only JSON files are supported.
            </Text>

            {/* File preview */}
            {filePreview && (
              <div className="mt-3">
                <Text strong>File Preview:</Text>
                {isGcpKey && (
                  <Alert
                    message="GCP Service Account Detected"
                    description="This appears to be a Google Cloud Platform service account key. Form fields have been auto-populated."
                    type="info"
                    showIcon
                    className="mb-2"
                  />
                )}
                <pre style={{ 
                  background: 'var(--bg-secondary)', 
                  padding: '8px', 
                  borderRadius: '4px', 
                  fontSize: '12px', 
                  overflow: 'auto', 
                  maxHeight: '128px', 
                  color: 'var(--text-secondary)' 
                }}>
                  {filePreview.substring(0, 500)}{filePreview.length > 500 ? '...' : ''}
                </pre>
              </div>
            )}
          </Form.Item>

          <Form.Item
            name="file_type"
            label="File Type"
            rules={[{ required: true, message: 'Please select a file type' }]}
          >
            <Select placeholder="Select file type">
              <Option value="custom_json">JSON - Configuration data</Option>
              <Option value="gcp_service_account">GCP - Google Cloud credentials</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="environment_variable_name"
            label="Environment Variable Name"
            rules={[
              { required: true, message: 'Environment variable name is required' },
              { whitespace: true, message: 'Environment variable name cannot be empty' }
            ]}
            help="The environment variable name for accessing the file in containers"
          >
            <Input 
              placeholder="e.g., GOOGLE_APPLICATION_CREDENTIALS" 
              className="font-mono"
            />
          </Form.Item>

          <Form.Item
            name="container_path"
            label="Container Path (Optional)"
            help="If specified, the file will be mounted at this path in the container"
          >
            <Input 
              placeholder="e.g., /app/config/credentials.json" 
              className="font-mono"
            />
          </Form.Item>
          
          <div className="flex justify-end space-x-2">
            <Tooltip title="Cancel upload">
              <Button 
                shape="circle"
                icon={<DeleteOutlined />}
                onClick={() => {
                  setIsModalVisible(false);
                  form.resetFields();
                  setFileList([]);
                }}
              />
            </Tooltip>
            <Tooltip title="Upload file">
              <Button 
                type="primary" 
                shape="circle"
                icon={<UploadOutlined />}
                htmlType="submit"
                loading={uploadMutation.isPending}
                disabled={fileList.length === 0}
              />
            </Tooltip>
          </div>
        </Form>
      </Modal>

      {/* Edit File Modal */}
      <Modal
        title="Edit File Settings"
        open={isEditModalVisible}
        onCancel={() => {
          setIsEditModalVisible(false);
          setEditingRecord(null);
          editForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdate}
          className="mt-4"
        >
          {editingRecord && (
            <div className="mb-4 p-3 glass-card">
              <Text strong>File: {editingRecord.file_name}</Text>
              <br />
              <Text style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                Type: {editingRecord.file_type.toUpperCase()} • 
                Size: {formatFileSize(editingRecord.file_size)}
              </Text>
            </div>
          )}

          <Form.Item
            name="environment_variable_name"
            label="Environment Variable Name (Optional)"
            help="If specified, the file path will be available as this environment variable"
          >
            <Input 
              placeholder="e.g., GOOGLE_APPLICATION_CREDENTIALS" 
              className="font-mono"
            />
          </Form.Item>

          <Form.Item
            name="container_path"
            label="Container Path (Optional)"
            help="If specified, the file will be mounted at this path in the container"
          >
            <Input 
              placeholder="e.g., /app/config/credentials.json" 
              className="font-mono"
            />
          </Form.Item>
          
          <div className="flex justify-end space-x-2">
            <Tooltip title="Cancel changes">
              <Button 
                shape="circle"
                icon={<DeleteOutlined />}
                onClick={() => {
                  setIsEditModalVisible(false);
                  setEditingRecord(null);
                  editForm.resetFields();
                }}
              />
            </Tooltip>
            <Tooltip title="Save changes">
              <Button 
                type="primary" 
                shape="circle"
                icon={<EditOutlined />}
                htmlType="submit"
                loading={updateMutation.isPending}
              />
            </Tooltip>
          </div>
        </Form>
      </Modal>

      {/* Help Section */}
      <Card title="Help & Information" className="glass-card">
        <Row gutter={[24, 16]}>
          <Col xs={24} md={8}>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>
              What are Environment Files?
            </Title>
            <Text style={{ color: 'var(--text-secondary)' }}>
              Configuration files and credentials that are automatically made available in your research environments.
            </Text>
          </Col>
          
          <Col xs={24} md={8}>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>
              File Types
            </Title>
            <div className="space-y-1">
              <Text style={{ color: 'var(--text-secondary)', display: 'block' }}>
                <strong>JSON:</strong> Configuration data
              </Text>
              <Text style={{ color: 'var(--text-secondary)', display: 'block' }}>
                <strong>GCP:</strong> Google Cloud credentials
              </Text>
            </div>
          </Col>
          
          <Col xs={24} md={8}>
            <Title level={5} style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>
              Usage Options
            </Title>
            <div className="space-y-1">
              <Text style={{ color: 'var(--text-secondary)', display: 'block' }}>
                <strong>Environment Variable:</strong> File path via env var
              </Text>
              <Text style={{ color: 'var(--text-secondary)', display: 'block' }}>
                <strong>Container Path:</strong> File at specific location
              </Text>
              <Text style={{ color: 'var(--text-secondary)', display: 'block' }}>
                <strong>Both:</strong> Available through both methods
              </Text>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
}
