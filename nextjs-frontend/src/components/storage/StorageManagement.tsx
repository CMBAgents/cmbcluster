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

interface StorageManagementProps {
  hideCreateButton?: boolean;
}

export default function StorageManagement({ hideCreateButton = false }: StorageManagementProps) {
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
      {/* Professional Header - Only show full header when not embedded */}
      {!hideCreateButton ? (
        <div className="page-header">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="icon-container primary p-2">
                  <DatabaseOutlined style={{ fontSize: '18px' }} />
                </div>
                <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  Workspace Storage
                </h2>
              </div>
              <p className="text-lg mb-4" style={{ color: 'var(--text-secondary)' }}>
                Manage your research workspace storage and data files
              </p>
              <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-tertiary)' }}>
                <span className="flex items-center gap-1">
                  <div className="status-indicator running"></div>
                  {storages.length} active workspaces
                </span>
                <span>•</span>
                <span>Auto-synced and backed up</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                icon={<ReloadOutlined />}
                onClick={() => refetch()}
                loading={isLoading}
                className="btn-secondary"
              >
                Refresh
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setShowCreateForm(true)}
                size="large"
                className="btn-primary"
                style={{
                  height: '48px',
                  fontSize: 'var(--text-lg)',
                  fontWeight: 'var(--font-semibold)'
                }}
              >
                Create Workspace
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <div className="icon-container primary p-2">
              <DatabaseOutlined style={{ fontSize: '16px' }} />
            </div>
            <div>
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                Storage Management
              </h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {storages.length} workspace{storages.length !== 1 ? 's' : ''} available
              </p>
            </div>
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
            className="btn-secondary"
          >
            Refresh
          </Button>
        </div>
      )}

      {/* Storage Analytics Overview - only show when not embedded in environments */}
      {!hideCreateButton && <StorageAnalytics storages={storages} />}

      {/* Professional Storage List */}
      <Card 
        className="glass-card"
        loading={isLoading}
        title={!hideCreateButton ? (
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
              Your Workspaces
            </h3>
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              {storages.length} workspace{storages.length !== 1 ? 's' : ''} total
            </span>
          </div>
        ) : null}
      >
        {storages.length === 0 ? (
          <div className="empty-state py-12">
            <div className="empty-state-icon">
              <DatabaseOutlined />
            </div>
            <h3>No Workspaces Found</h3>
            <p>
              You don't have any workspace storage yet. Create your first workspace to store and manage your research data and files.
            </p>
            {!hideCreateButton && (
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setShowCreateForm(true)}
                size="large"
              >
                Create Your First Workspace
              </Button>
            )}
          </div>
        ) : (
          <div className={hideCreateButton ? "space-y-3" : "space-y-4"}>
            {storages.map((storage) => (
              <Card
                key={storage.id}
                className={`action-card transition-all hover:shadow-md ${
                  hideCreateButton ? 'p-4' : 'p-6'
                }`}
                bodyStyle={{ padding: hideCreateButton ? 'var(--spacing-md)' : 'var(--spacing-lg)' }}
              >
                <div className="flex items-center justify-between">
                  {/* Storage Info */}
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`icon-container ${storage.status === 'active' ? 'success' : 'primary'} ${hideCreateButton ? 'p-2' : 'p-3'}`}>
                      <CloudOutlined style={{ fontSize: hideCreateButton ? '16px' : '20px' }} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={`font-semibold ${hideCreateButton ? 'text-sm' : 'text-base'}`} style={{ color: 'var(--text-primary)' }}>
                          {storage.display_name || 'Unknown Workspace'}
                        </h4>
                        <span className={`status-badge ${storage.status === 'active' ? 'running' : 'stopped'} text-xs`}>
                          {storage.status === 'active' ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                        {storage.bucket_name || 'unknown'}
                      </p>
                      {!hideCreateButton && (
                        <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          <span>{formatStorageSize(storage.size_bytes || 0)}</span>
                          <span>•</span>
                          <span>{storage.storage_class?.toUpperCase() || 'STANDARD'}</span>
                          <span>•</span>
                          <span>Created {new Date(storage.created_at).toLocaleDateString()}</span>
                        </div>
                      )}
                      {hideCreateButton && (
                        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                          {formatStorageSize(storage.size_bytes || 0)}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Status & Details Combined for Compact View */}
                  {hideCreateButton ? (
                    <Col>
                      <div className="text-right">
                        <Tag 
                          color={storage.status === 'active' ? 'green' : 'default'}
                          size="small"
                        >
                          {storage.status === 'active' ? 'Active' : 'Inactive'}
                        </Tag>
                        <br />
                        <Text type="secondary" className="text-xs">
                          {formatStorageSize(storage.size_bytes || 0)}
                        </Text>
                      </div>
                    </Col>
                  ) : (
                    <>
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
                    </>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button
                      size="small"
                      icon={<InfoCircleOutlined />}
                      onClick={() => toggleDetails(storage.id)}
                      className="btn-secondary"
                      title={showDetails[storage.id] ? 'Hide Details' : 'Show Details'}
                    >
                      {hideCreateButton ? '' : (showDetails[storage.id] ? 'Hide' : 'Details')}
                    </Button>
                    <Button
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => toggleDeleteConfirm(storage.id)}
                      loading={deleteMutation.isPending}
                      title="Delete Workspace"
                    >
                      {hideCreateButton ? '' : 'Delete'}
                    </Button>
                  </div>
                </div>

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
      {!hideCreateButton && (
        <StorageCreationForm
          visible={showCreateForm}
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => {
            setShowCreateForm(false);
            refetch();
          }}
        />
      )}
    </div>
  );
}
