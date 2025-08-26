'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Upload,
  Input,
  Space,
  message,
  Modal,
  Typography,
  Progress,
  Card,
  Row,
  Col,
  Tag,
  Tooltip,
  Dropdown,
  Breadcrumb,
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  FileOutlined,
  FolderOutlined,
  SearchOutlined,
  ReloadOutlined,
  InboxOutlined,
  MoreOutlined,
  EditOutlined,
  CopyOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile, UploadProps } from 'antd/es/upload';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

const { Title, Text } = Typography;
const { Dragger } = Upload;
const { Search } = Input;

interface FileObject {
  name: string;
  size: number;
  created: string;
  type?: string;
  isFolder?: boolean;
}

interface StorageFileManagerProps {
  storageId: string;
  storageName: string;
}

export default function StorageFileManager({ storageId, storageName }: StorageFileManagerProps) {
  const [currentPath, setCurrentPath] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadVisible, setUploadVisible] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [previewFile, setPreviewFile] = useState<FileObject | null>(null);
  const queryClient = useQueryClient();

  // Fetch files for current storage and path
  const { data: filesData, isLoading, refetch } = useQuery({
    queryKey: ['storage-files', storageId, currentPath],
    queryFn: () => apiClient.listStorageFiles(storageId, currentPath),
    enabled: !!storageId,
  });

  const files: FileObject[] = filesData?.objects || [];

  // Filter files based on search term
  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: ({ file, path }: { file: File; path: string }) =>
      apiClient.uploadFileToStorage(storageId, file, path),
    onSuccess: () => {
      message.success('File uploaded successfully');
      refetch();
      setUploadProgress({});
    },
    onError: (error: any) => {
      message.error(`Upload failed: ${error.message}`);
      setUploadProgress({});
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (fileName: string) =>
      apiClient.deleteStorageFile(storageId, fileName),
    onSuccess: () => {
      message.success('File deleted successfully');
      refetch();
      setSelectedFiles([]);
    },
    onError: (error: any) => {
      message.error(`Delete failed: ${error.message}`);
    },
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  const getFileIcon = (fileName: string, isFolder?: boolean) => {
    if (isFolder) return <FolderOutlined className="text-blue-500" />;
    
    const ext = fileName.split('.').pop()?.toLowerCase();
    const iconMap: Record<string, string> = {
      pdf: '📄',
      doc: '📝', docx: '📝',
      xls: '📊', xlsx: '📊',
      ppt: '📈', pptx: '📈',
      txt: '📃', md: '📃',
      js: '💻', ts: '💻', py: '💻', json: '💻',
      jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️',
      zip: '📦', rar: '📦', tar: '📦',
      mp4: '🎥', avi: '🎥', mov: '🎥',
      mp3: '🎵', wav: '🎵',
    };
    
    return <span className="text-lg">{iconMap[ext || ''] || '📄'}</span>;
  };

  const handleFileDoubleClick = (file: FileObject) => {
    if (file.isFolder) {
      const newPath = currentPath ? `${currentPath}/${file.name}` : file.name;
      setCurrentPath(newPath);
    } else {
      handleDownload(file.name);
    }
  };

  const handleDownload = async (fileName: string) => {
    try {
      const response = await apiClient.downloadFileFromStorage(storageId, fileName);
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName.split('/').pop() || fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success('Download started');
    } catch (error) {
      message.error('Download failed');
    }
  };

  const handleDelete = (fileName: string) => {
    Modal.confirm({
      title: 'Delete File',
      content: `Are you sure you want to delete "${fileName.split('/').pop()}"?`,
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutate(fileName),
    });
  };

  const handleBulkDelete = () => {
    if (selectedFiles.length === 0) return;
    
    Modal.confirm({
      title: 'Delete Files',
      content: `Are you sure you want to delete ${selectedFiles.length} file(s)?`,
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        for (const fileName of selectedFiles) {
          await deleteMutation.mutateAsync(fileName);
        }
      },
    });
  };

  const uploadProps: UploadProps = {
    multiple: true,
    beforeUpload: (file) => {
      uploadMutation.mutate({ file, path: currentPath });
      return false; // Prevent default upload
    },
    onRemove: (file) => {
      setUploadFiles(prev => prev.filter(f => f.uid !== file.uid));
    },
    fileList: uploadFiles,
  };

  const pathBreadcrumbs = currentPath.split('/').filter(Boolean);

  const columns: ColumnsType<FileObject> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: FileObject) => (
        <div 
          className="flex items-center space-x-2 cursor-pointer hover:text-blue-600"
          onDoubleClick={() => handleFileDoubleClick(record)}
        >
          {getFileIcon(name, record.isFolder)}
          <span>{name.split('/').pop()}</span>
          {record.isFolder && <Tag>Folder</Tag>}
        </div>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size: number, record: FileObject) => 
        record.isFolder ? '-' : formatFileSize(size),
      sorter: (a, b) => (a.size || 0) - (b.size || 0),
      width: 100,
    },
    {
      title: 'Modified',
      dataIndex: 'created',
      key: 'created',
      render: formatDate,
      sorter: (a, b) => new Date(a.created).getTime() - new Date(b.created).getTime(),
      width: 180,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: FileObject) => (
        <Space size="small">
          {!record.isFolder && (
            <>
              <Tooltip title="Download">
                <Button
                  type="text"
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(record.name)}
                />
              </Tooltip>
              <Tooltip title="Preview">
                <Button
                  type="text"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => setPreviewFile(record)}
                />
              </Tooltip>
            </>
          )}
          <Tooltip title="Delete">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.name)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                { key: 'rename', label: 'Rename', icon: <EditOutlined /> },
                { key: 'copy', label: 'Copy', icon: <CopyOutlined /> },
                { key: 'move', label: 'Move', icon: <MoreOutlined /> },
              ]
            }}
            trigger={['click']}
          >
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
      width: 140,
    },
  ];

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <Row gutter={16} align="middle">
        <Col flex="auto">
          <Space>
            <Title level={5} className="mb-0">
              📁 Files in {storageName}
            </Title>
            {pathBreadcrumbs.length > 0 && (
              <Breadcrumb
                items={[
                  { title: 'Root', onClick: () => setCurrentPath('') },
                  ...pathBreadcrumbs.map((part, index) => ({
                    title: part,
                    onClick: () => setCurrentPath(pathBreadcrumbs.slice(0, index + 1).join('/')),
                  })),
                ]}
              />
            )}
          </Space>
        </Col>
        <Col>
          <Space>
            <Search
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: 200 }}
              allowClear
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => refetch()}
              loading={isLoading}
            >
              Refresh
            </Button>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadVisible(true)}
            >
              Upload Files
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Bulk Actions */}
      {selectedFiles.length > 0 && (
        <Card size="small" className="bg-blue-50 border-blue-200">
          <Space>
            <Text strong>{selectedFiles.length} file(s) selected</Text>
            <Button 
              size="small" 
              danger 
              icon={<DeleteOutlined />}
              onClick={handleBulkDelete}
              loading={deleteMutation.isPending}
            >
              Delete Selected
            </Button>
            <Button size="small" onClick={() => setSelectedFiles([])}>
              Clear Selection
            </Button>
          </Space>
        </Card>
      )}

      {/* Files Table */}
      <Table
        columns={columns}
        dataSource={filteredFiles}
        rowKey="name"
        loading={isLoading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} files`,
        }}
        rowSelection={{
          selectedRowKeys: selectedFiles,
          onChange: (selectedRowKeys: React.Key[]) => 
            setSelectedFiles(selectedRowKeys.map(key => String(key))),
          getCheckboxProps: (record) => ({
            disabled: record.isFolder, // Disable checkbox for folders
          }),
        }}
        onRow={(record) => ({
          onDoubleClick: () => handleFileDoubleClick(record),
        })}
        scroll={{ x: 800 }}
        size="small"
      />

      {/* Upload Modal */}
      <Modal
        title="Upload Files"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        footer={null}
        width={600}
      >
        <div className="space-y-4">
          <Text type="secondary">
            Upload files to: <Text code>/{currentPath || 'root'}</Text>
          </Text>
          
          <Dragger {...uploadProps} className="upload-area">
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              Click or drag files to this area to upload
            </p>
            <p className="ant-upload-hint">
              Support for multiple files. Files will be uploaded to the current directory.
            </p>
          </Dragger>

          {/* Upload Progress */}
          {Object.keys(uploadProgress).length > 0 && (
            <div className="space-y-2">
              <Title level={5}>Upload Progress</Title>
              {Object.entries(uploadProgress).map(([fileName, progress]) => (
                <div key={fileName}>
                  <Text className="block text-sm mb-1">{fileName}</Text>
                  <Progress percent={progress} size="small" />
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      {/* File Preview Modal */}
      <Modal
        title={`Preview: ${previewFile?.name.split('/').pop()}`}
        open={!!previewFile}
        onCancel={() => setPreviewFile(null)}
        footer={[
          <Button key="download" onClick={() => previewFile && handleDownload(previewFile.name)}>
            Download
          </Button>,
          <Button key="close" onClick={() => setPreviewFile(null)}>
            Close
          </Button>,
        ]}
        width={800}
      >
        {previewFile && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">
              {getFileIcon(previewFile.name)}
            </div>
            <Title level={4}>{previewFile.name.split('/').pop()}</Title>
            <div className="space-y-2 text-left bg-gray-50 rounded p-4 mt-4">
              <Text><strong>Size:</strong> {formatFileSize(previewFile.size)}</Text>
              <br />
              <Text><strong>Created:</strong> {formatDate(previewFile.created)}</Text>
              <br />
              <Text><strong>Path:</strong> {previewFile.name}</Text>
            </div>
            <Text type="secondary" className="block mt-4">
              Preview not available for this file type. Click Download to view the file.
            </Text>
          </div>
        )}
      </Modal>
    </div>
  );
}
