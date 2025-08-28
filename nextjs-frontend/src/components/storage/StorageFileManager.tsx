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
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileTextOutlined,
  CodeOutlined,
  FileImageOutlined,
  FileZipOutlined,
  VideoOutlined,
  AudioOutlined,
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

  // Filter files based on search term and exclude empty files
  const filteredFiles = files.filter(file => {
    // Filter out files with no name or no data
    if (!file.name || file.name.trim() === '' || file.size === 0) {
      return false;
    }
    
    // Apply search filter
    return file.name.toLowerCase().includes(searchTerm.toLowerCase());
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ file, path }: { file: File; path: string }) => {
      console.log('Starting upload for file:', file.name, 'to path:', path);
      const result = await apiClient.uploadFileToStorage(storageId, file, path);
      console.log('Upload API result:', result);
      return result;
    },
    onSuccess: (data, variables) => {
      console.log(`File ${variables.file.name} uploaded successfully:`, data);
      // Trigger refetch after successful upload
      refetch();
    },
    onError: (error: any, variables) => {
      console.error(`File ${variables.file.name} upload failed:`, error);
      message.error(`Failed to upload ${variables.file.name}: ${error.message || 'Unknown error'}`);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (fileName: string) =>
      apiClient.deleteFileFromStorage(storageId, fileName),
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
    if (isFolder) return <FolderOutlined style={{ color: 'var(--primary-600)' }} />;
    
    const ext = fileName.split('.').pop()?.toLowerCase();
    
    // Document files
    if (['pdf'].includes(ext || '')) {
      return <FilePdfOutlined style={{ color: 'var(--error-600)' }} />;
    }
    if (['doc', 'docx'].includes(ext || '')) {
      return <FileWordOutlined style={{ color: 'var(--primary-600)' }} />;
    }
    if (['xls', 'xlsx'].includes(ext || '')) {
      return <FileExcelOutlined style={{ color: 'var(--success-600)' }} />;
    }
    if (['ppt', 'pptx'].includes(ext || '')) {
      return <FilePptOutlined style={{ color: 'var(--warning-600)' }} />;
    }
    if (['txt', 'md', 'readme'].includes(ext || '')) {
      return <FileTextOutlined style={{ color: 'var(--text-primary)' }} />;
    }
    
    // Code files
    if (['js', 'ts', 'py', 'json', 'html', 'css', 'jsx', 'tsx'].includes(ext || '')) {
      return <CodeOutlined style={{ color: 'var(--purple-600)' }} />;
    }
    
    // Image files
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext || '')) {
      return <FileImageOutlined style={{ color: 'var(--success-600)' }} />;
    }
    
    // Archive files
    if (['zip', 'rar', 'tar', 'gz', '7z'].includes(ext || '')) {
      return <FileZipOutlined style={{ color: 'var(--warning-600)' }} />;
    }
    
    // Video files
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext || '')) {
      return <VideoOutlined style={{ color: 'var(--error-600)' }} />;
    }
    
    // Audio files
    if (['mp3', 'wav', 'flac', 'aac'].includes(ext || '')) {
      return <AudioOutlined style={{ color: 'var(--primary-600)' }} />;
    }
    
    // Default file icon
    return <FileOutlined style={{ color: 'var(--text-secondary)' }} />;
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
      console.log('Downloading file:', fileName);
      console.log('Storage ID:', storageId);
      console.log('Current path:', currentPath);
      
      // Use fileName as is, since it already includes the full path from the API
      const fullPath = fileName;
      console.log('Full file path:', fullPath);
      
      const response = await apiClient.downloadFileFromStorage(storageId, fullPath);
      console.log('Download response:', response);
      
      // Check if response is successful (axios response)
      if (response.status !== 200) {
        throw new Error(`Download failed with status: ${response.status}`);
      }
      
      // response.data is the blob for axios with responseType: 'blob'
      const blob = response.data;
      
      // Verify blob has content
      if (!blob || blob.size === 0) {
        throw new Error('Downloaded file is empty');
      }
      
      // Extract just the filename for the download (not the full path)
      const downloadFileName = fileName.split('/').pop() || 'download';
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', downloadFileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success(`Download started: ${downloadFileName}`);
    } catch (error) {
      console.error('Download error:', error);
      if (error instanceof Error && error.message.includes('404')) {
        message.error('File not found. It may have been deleted or moved.');
      } else if (error instanceof Error && error.message.includes('403')) {
        message.error('Access denied. You may not have permission to download this file.');
      } else {
        message.error('Download failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
      }
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
    beforeUpload: (file, fileList) => {
      console.log('beforeUpload called with file:', {
        name: file.name,
        size: file.size,
        type: file.type,
        uid: file.uid || `upload-${Date.now()}-${Math.random()}`
      });
      
      // Create UploadFile object with originFileObj properly set
      const uploadFile: UploadFile = {
        uid: file.uid || `upload-${Date.now()}-${Math.random()}`,
        name: file.name,
        status: 'done',
        size: file.size,
        type: file.type,
        originFileObj: file,
      };
      
      console.log('Created uploadFile object:', uploadFile);
      
      setUploadFiles(prev => {
        const newList = [...prev, uploadFile];
        console.log('Updated uploadFiles list:', newList);
        return newList;
      });
      
      return false; // Prevent default upload
    },
    onRemove: (file) => {
      console.log('onRemove called for file:', file.name);
      setUploadFiles(prev => {
        const newList = prev.filter(f => f.uid !== file.uid);
        console.log('After remove, uploadFiles:', newList);
        return newList;
      });
    },
    fileList: uploadFiles,
  };

  const handleUploadAll = async () => {
    console.log('=== STORAGE FILES FRONTEND DEBUG ===');
    console.log('handleUploadAll called');
    console.log('Current uploadFiles:', uploadFiles);
    console.log('Current path:', currentPath);
    console.log('Storage ID:', storageId);

    if (uploadFiles.length === 0) {
      console.error('No files to upload');
      message.warning('Please select files to upload');
      return;
    }

    let successCount = 0;
    let errorCount = 0;
    const totalFiles = uploadFiles.length;
    const failedFiles: string[] = [];

    console.log(`Starting upload of ${totalFiles} files...`);

    for (const uploadFile of uploadFiles) {
      const file = uploadFile.originFileObj as File;
      console.log(`Processing uploadFile:`, {
        uid: uploadFile.uid,
        name: uploadFile.name,
        hasOriginFile: !!file
      });

      if (file) {
        try {
          console.log(`=== Uploading individual file: ${file.name} ===`);
          console.log('File details:', {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified
          });
          console.log('Upload parameters:', {
            storageId,
            currentPath,
            file: file.name
          });
          
          const result = await uploadMutation.mutateAsync({ file, path: currentPath });
          console.log(`✅ Upload successful for ${file.name}:`, result);
          successCount++;
        } catch (error) {
          console.error(`❌ Upload failed for ${file.name}:`, error);
          errorCount++;
          failedFiles.push(file.name);
        }
      } else {
        console.error(`No file object found for uploadFile:`, uploadFile);
        errorCount++;
        failedFiles.push(uploadFile.name || 'unknown file');
      }
    }

    console.log('Upload summary:', {
      totalFiles,
      successCount,
      errorCount,
      failedFiles
    });

    // Provide detailed feedback
    if (successCount > 0) {
      message.success(`${successCount} of ${totalFiles} file(s) uploaded successfully`);
    }
    if (errorCount > 0) {
      message.error(`${errorCount} of ${totalFiles} file(s) failed to upload: ${failedFiles.join(', ')}`);
    }

    console.log('Refreshing file list...');
    // Always refetch to get the latest file list
    await refetch();
    
    // Close modal and clear state after all uploads are done
    setUploadFiles([]);
    setUploadProgress({});
    setUploadVisible(false);
    console.log('=== END STORAGE FILES FRONTEND DEBUG ===');
  };

  const pathBreadcrumbs = currentPath.split('/').filter(Boolean);

  const columns: ColumnsType<FileObject> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: FileObject) => {
        const pathParts = name.split('/');
        const fileName = pathParts.pop() || '';
        const folderPath = pathParts.length > 0 ? pathParts.join('/') + '/' : '';
        
        return (
          <div 
            className="flex items-center space-x-2 cursor-pointer hover:text-blue-600"
            onDoubleClick={() => handleFileDoubleClick(record)}
          >
            {getFileIcon(name, record.isFolder)}
            <div className="flex flex-col">
              <span className="font-medium">{fileName}</span>
              {folderPath && (
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  <FolderOutlined style={{ fontSize: '10px', marginRight: '4px' }} />
                  {folderPath}
                </span>
              )}
            </div>
            {record.isFolder && <Tag size="small" color="blue">Folder</Tag>}
          </div>
        );
      },
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
            <Tooltip title="Upload Files">
              <Button
                type="primary"
                shape="circle"
                icon={<UploadOutlined />}
                onClick={() => setUploadVisible(true)}
              />
            </Tooltip>
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
        onCancel={() => {
          setUploadVisible(false);
          setUploadFiles([]);
          setUploadProgress({});
        }}
        footer={[
          <Button 
            key="cancel" 
            onClick={() => {
              setUploadVisible(false);
              setUploadFiles([]);
              setUploadProgress({});
            }}
          >
            Cancel
          </Button>,
          <Button
            key="upload"
            type="primary"
            loading={uploadMutation.isPending}
            disabled={uploadFiles.length === 0}
            onClick={handleUploadAll}
          >
            Upload {uploadFiles.length > 0 ? `(${uploadFiles.length})` : ''} Files
          </Button>
        ]}
        width={600}
      >
        <div className="space-y-4">
          <Text type="secondary">
            Upload files to: <Text code>/{currentPath || 'root'}</Text>
          </Text>
          
          <Dragger {...uploadProps} className="upload-area" disabled={uploadMutation.isPending}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">
              {uploadMutation.isPending 
                ? 'Uploading files...' 
                : 'Click or drag files to this area to upload'
              }
            </p>
            <p className="ant-upload-hint">
              {uploadMutation.isPending 
                ? 'Please wait while files are being uploaded.' 
                : 'Support for multiple files. Files will be uploaded to the current directory.'
              }
            </p>
          </Dragger>

          {/* Show selected files */}
          {uploadFiles.length > 0 && !uploadMutation.isPending && (
            <div className="space-y-2">
              <Text strong>Selected Files ({uploadFiles.length}):</Text>
              <div className="max-h-32 overflow-y-auto">
                {uploadFiles.map((file) => (
                  <div key={file.uid} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      {((file.size || 0) / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {uploadMutation.isPending && (
            <div className="text-center">
              <Text type="secondary">Uploading files, please wait...</Text>
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
