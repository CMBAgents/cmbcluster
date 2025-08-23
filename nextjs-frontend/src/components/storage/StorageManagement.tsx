'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Spin,
  Empty,
  message,
  Divider,
  Tag,
  Modal,
  Tabs,
} from 'antd';
import {
  ReloadOutlined,
  PlusOutlined,
  DatabaseOutlined,
  CloudOutlined,
  FileOutlined,
  DeleteOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { StorageItem } from '@/types';
import StorageWorkspaceSelector from './StorageWorkspaceSelector';
import StorageFileManager from './StorageFileManager';
import StorageCreationForm from './StorageCreationForm';
import StorageAnalytics from './StorageAnalytics';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface StorageManagementProps {}

export default function StorageManagement({}: StorageManagementProps) {
  const [selectedStorage, setSelectedStorage] = useState<StorageItem | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});
  const [deleteConfirm, setDeleteConfirm] = useState<Record<string, boolean>>({});
  const queryClient = useQueryClient();

  // Fetch user storages
  const { data: storagesResponse, isLoading, error, refetch } = useQuery({
    queryKey: ['user-storages'],
    queryFn: () => apiClient.listUserStorages(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const storages = storagesResponse?.storages || [];

  // Delete storage mutation
  const deleteMutation = useMutation({
    mutationFn: ({ storageId, force }: { storageId: string; force: boolean }) =>
      apiClient.deleteStorage(storageId, force),
    onSuccess: (data, variables) => {
      if (data.status === 'deleted') {
        message.success('Workspace deleted successfully!');
        queryClient.invalidateQueries({ queryKey: ['user-storages'] });
        setDeleteConfirm(prev => ({ ...prev, [variables.storageId]: false }));
      } else {
        message.error(data.message || 'Failed to delete workspace');
      }
    },
    onError: (error: any) => {
      message.error(error.message || 'Error deleting workspace');
    },
  });

  const handleDeleteStorage = (storageId: string) => {
    deleteMutation.mutate({ storageId, force: true });
  };

  const formatStorageSize = (sizeBytes: number): string => {
    if (sizeBytes === 0) return 'Empty';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = sizeBytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDateTime = (dateString: string): string => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  const toggleDetails = (storageId: string) => {
    setShowDetails(prev => ({
      ...prev,
      [storageId]: !prev[storageId]
    }));
  };

  const toggleDeleteConfirm = (storageId: string) => {
    setDeleteConfirm(prev => ({
      ...prev,
      [storageId]: !prev[storageId]
    }));
  };

  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <Title level={4} type="danger">
            Failed to load storage information
          </Title>
          <Text type="secondary">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </Text>
          <br />
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={() => refetch()} 
            className="mt-4"
          >
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <Card>
        <div className="flex justify-between items-start mb-4">
          <div>
            <Title level={3} className="mb-2 flex items-center">
              <DatabaseOutlined className="mr-3 text-blue-500" />
              Workspace Storage Management
            </Title>
            <Paragraph type="secondary" className="mb-0">
              Manage your research workspace storage buckets. Each workspace provides isolated storage for your projects and data.
            </Paragraph>
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
              icon={<PlusOutlined />}
              onClick={() => setShowCreateForm(true)}
            >
              Create Workspace
            </Button>
          </Space>
        </div>
      </Card>

      {/* Workspace Selector (for environments) */}
      <StorageWorkspaceSelector 
        storages={storages} 
        onStorageSelect={setSelectedStorage}
      />

      {/* Storage Analytics Overview */}
      <StorageAnalytics storages={storages} />

      {/* Storage List */}
      <Card title="Your Workspaces" loading={isLoading}>
        {storages.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <Title level={4}>No Workspaces Found</Title>
                <Text type="secondary">
                  You don't have any workspace storage buckets yet. Create your first workspace to get started with your research projects.
                </Text>
              </div>
            }
          >
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => setShowCreateForm(true)}
            >
              Create Your First Workspace
            </Button>
          </Empty>
        ) : (
          <div className="space-y-4">
            {storages.map((storage) => (
              <Card
                key={storage.id}
                size="small"
                className="border border-gray-200 hover:border-blue-300 transition-colors"
              >
                <Row gutter={16} align="middle">
                  {/* Storage Info */}
                  <Col flex="1">
                    <div className="flex items-center space-x-3">
                      <CloudOutlined className="text-2xl text-blue-500" />
                      <div>
                        <Title level={5} className="mb-1">
                          {storage.display_name || 'Unknown Workspace'}
                        </Title>
                        <Text type="secondary" className="text-sm">
                          Bucket: {storage.bucket_name || 'unknown'}
                        </Text>
                      </div>
                    </div>
                  </Col>

                  {/* Status */}
                  <Col>
                    <Tag 
                      color={storage.status === 'active' ? 'green' : 'default'}
                      className="mb-0"
                    >
                      {storage.status === 'active' ? 'Active' : 'Inactive'}
                    </Tag>
                  </Col>

                  {/* Storage Details */}
                  <Col>
                    <div className="text-right">
                      <Text strong>{storage.storage_class?.toUpperCase() || 'STANDARD'}</Text>
                      <br />
                      <Text type="secondary" className="text-sm">
                        {formatStorageSize(storage.size_bytes || 0)}
                      </Text>
                    </div>
                  </Col>

                  {/* Created Date */}
                  <Col>
                    <div className="text-right">
                      <Text className="text-sm">Created</Text>
                      <br />
                      <Text type="secondary" className="text-sm">
                        {formatDateTime(storage.created_at)}
                      </Text>
                    </div>
                  </Col>

                  {/* Actions */}
                  <Col>
                    <Space direction="vertical" size="small">
                      <Button
                        type="text"
                        size="small"
                        icon={<InfoCircleOutlined />}
                        onClick={() => toggleDetails(storage.id)}
                      >
                        {showDetails[storage.id] ? 'Hide' : 'Details'}
                      </Button>
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => toggleDeleteConfirm(storage.id)}
                        loading={deleteMutation.isPending}
                      >
                        Delete
                      </Button>
                    </Space>
                  </Col>
                </Row>

                {/* Expanded Details */}
                {showDetails[storage.id] && (
                  <>
                    <Divider />
                    <Tabs defaultActiveKey="details" type="card" size="small">
                      <TabPane tab="📋 Details" key="details">
                        <Row gutter={16}>
                          <Col span={12}>
                            <div className="space-y-2">
                              <div>
                                <Text strong>Storage ID:</Text>
                                <br />
                                <Text type="secondary">{storage.id}</Text>
                              </div>
                              <div>
                                <Text strong>Display Name:</Text>
                                <br />
                                <Text>{storage.display_name || 'N/A'}</Text>
                              </div>
                              <div>
                                <Text strong>Bucket Name:</Text>
                                <br />
                                <Text type="secondary">{storage.bucket_name || 'N/A'}</Text>
                              </div>
                            </div>
                          </Col>
                          <Col span={12}>
                            <div className="space-y-2">
                              <div>
                                <Text strong>Size:</Text>
                                <br />
                                <Text>{formatStorageSize(storage.size_bytes || 0)}</Text>
                              </div>
                              <div>
                                <Text strong>Region:</Text>
                                <br />
                                <Text>{storage.region || 'Unknown'}</Text>
                              </div>
                              <div>
                                <Text strong>Last Modified:</Text>
                                <br />
                                <Text type="secondary">{formatDateTime(storage.updated_at || storage.created_at)}</Text>
                              </div>
                            </div>
                          </Col>
                        </Row>
                      </TabPane>
                      <TabPane 
                        tab="📁 Files" 
                        key="files"
                        disabled={storage.status !== 'active'}
                      >
                        {storage.status === 'active' ? (
                          <StorageFileManager 
                            storageId={storage.id} 
                            storageName={storage.display_name || 'Workspace'}
                          />
                        ) : (
                          <div className="text-center py-4">
                            <Text type="secondary">
                              File management is only available for active workspaces.
                            </Text>
                          </div>
                        )}
                      </TabPane>
                    </Tabs>
                  </>
                )}

                {/* Delete Confirmation */}
                {deleteConfirm[storage.id] && (
                  <>
                    <Divider />
                    <div className="bg-red-50 border border-red-200 rounded p-4">
                      <Title level={5} type="danger" className="mb-2">
                        ⚠️ Delete Workspace: {storage.display_name}
                      </Title>
                      <Text type="secondary" className="block mb-4">
                        This action cannot be undone. All files and data in this workspace will be permanently deleted.
                      </Text>
                      <Space>
                        <Button
                          type="primary"
                          danger
                          icon={<DeleteOutlined />}
                          loading={deleteMutation.isPending}
                          onClick={() => handleDeleteStorage(storage.id)}
                        >
                          Confirm Delete
                        </Button>
                        <Button
                          onClick={() => toggleDeleteConfirm(storage.id)}
                          disabled={deleteMutation.isPending}
                        >
                          Cancel
                        </Button>
                      </Space>
                    </div>
                  </>
                )}
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* Create Storage Form Modal */}
      <StorageCreationForm
        visible={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSuccess={() => {
          setShowCreateForm(false);
          refetch();
        }}
      />
    </div>
  );
}
