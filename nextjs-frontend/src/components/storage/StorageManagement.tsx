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
  Table,
  Tooltip,
  Dropdown,
  Input,
  Select,
  Progress,
  Avatar,
  Badge,
  Statistic,
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
  MoreOutlined,
  SearchOutlined,
  FilterOutlined,
  SortAscendingOutlined,
  CopyOutlined,
  DownloadOutlined,
  FolderOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  SnowflakeOutlined,
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
const { Search } = Input;
const { Option } = Select;

interface StorageManagementProps {
  hideCreateButton?: boolean;
}

type SortField = 'name' | 'size' | 'created' | 'status';
type FilterStatus = 'all' | 'active' | 'inactive';

export default function StorageManagement({ hideCreateButton = false }: StorageManagementProps) {
  const [selectedStorage, setSelectedStorage] = useState<StorageItem | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});
  const [deleteConfirm, setDeleteConfirm] = useState<Record<string, boolean>>({});
  const [searchText, setSearchText] = useState('');
  const [sortField, setSortField] = useState<SortField>('created');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const queryClient = useQueryClient();

  // Fetch user storages
  const { data: storagesResponse, isLoading, error, refetch } = useQuery({
    queryKey: ['user-storages'],
    queryFn: () => apiClient.listUserStorages(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const storages = storagesResponse?.storages || [];

  // Filter and sort storages
  const filteredStorages = storages
    .filter(storage => {
      const matchesSearch = !searchText || 
        storage.display_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        storage.bucket_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        storage.storage_class?.toLowerCase().includes(searchText.toLowerCase());
      
      const matchesFilter = filterStatus === 'all' || 
        (filterStatus === 'active' && storage.status === 'active') ||
        (filterStatus === 'inactive' && storage.status !== 'active');
      
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => {
      let aVal, bVal;
      switch (sortField) {
        case 'name':
          aVal = a.display_name || a.bucket_name || '';
          bVal = b.display_name || b.bucket_name || '';
          break;
        case 'size':
          aVal = a.size_bytes || 0;
          bVal = b.size_bytes || 0;
          break;
        case 'created':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        case 'status':
          aVal = a.status === 'active' ? 1 : 0;
          bVal = b.status === 'active' ? 1 : 0;
          break;
        default:
          return 0;
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

  // Analytics calculations
  const analytics = {
    total: storages.length,
    active: storages.filter(s => s.status === 'active').length,
    totalSize: storages.reduce((acc, s) => acc + (s.size_bytes || 0), 0),
    totalObjects: storages.reduce((acc, s) => acc + (s.object_count || 0), 0),
  };

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

  const getStorageIcon = (storage: StorageItem) => {
    switch (storage.storage_class?.toLowerCase()) {
      case 'standard':
        return <ThunderboltOutlined style={{ color: '#1890ff' }} />;
      case 'nearline':
        return <SafetyOutlined style={{ color: '#52c41a' }} />;
      case 'coldline':
        return <SnowflakeOutlined style={{ color: '#722ed1' }} />;
      default:
        return <CloudOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const handleBulkAction = (action: string) => {
    const selectedStorages = filteredStorages.filter(s => selectedRowKeys.includes(s.id));
    switch (action) {
      case 'delete':
        Modal.confirm({
          title: `Delete ${selectedStorages.length} workspace${selectedStorages.length > 1 ? 's' : ''}?`,
          content: 'This action cannot be undone. All data will be permanently deleted.',
          okText: 'Delete All',
          okType: 'danger',
          onOk: () => {
            selectedStorages.forEach(storage => {
              deleteMutation.mutate({ storageId: storage.id, force: true });
            });
            setSelectedRowKeys([]);
          }
        });
        break;
      default:
        break;
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Copied to clipboard');
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
    <div className="space-y-4">
      {/* Modern Header with Analytics */}
      {!hideCreateButton ? (
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="icon-container primary p-3">
                  <DatabaseOutlined style={{ fontSize: '20px' }} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)', margin: 0 }}>
                    Workspace Storage
                  </h1>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)', margin: 0 }}>
                    Manage your research data and workspace storage
                  </p>
                </div>
              </div>
            </div>
            <Space>
              <Tooltip title="Refresh">
                <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading} />
              </Tooltip>
              <Tooltip title="Create New Workspace">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => setShowCreateForm(true)}
                />
              </Tooltip>
            </Space>
          </div>

          {/* Compact Analytics Cards */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={6}>
              <Card size="small" className="glass-card">
                <Statistic
                  title="Total Workspaces"
                  value={analytics.total}
                  prefix={<DatabaseOutlined />}
                  valueStyle={{ fontSize: '20px', color: 'var(--primary-600)' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small" className="glass-card">
                <Statistic
                  title="Active"
                  value={analytics.active}
                  prefix={<CloudOutlined />}
                  valueStyle={{ fontSize: '20px', color: 'var(--success-600)' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small" className="glass-card">
                <Statistic
                  title="Total Storage"
                  value={formatStorageSize(analytics.totalSize)}
                  prefix={<FileOutlined />}
                  valueStyle={{ fontSize: '20px', color: 'var(--purple-600)' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={6}>
              <Card size="small" className="glass-card">
                <Statistic
                  title="Objects"
                  value={analytics.totalObjects}
                  prefix={<FolderOutlined />}
                  valueStyle={{ fontSize: '20px', color: 'var(--orange-600)' }}
                />
              </Card>
            </Col>
          </Row>
        </div>
      ) : (
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Badge count={analytics.active} showZero>
              <Avatar icon={<DatabaseOutlined />} />
            </Badge>
            <div>
              <h3 className="text-lg font-semibold m-0" style={{ color: 'var(--text-primary)' }}>
                Storage Management
              </h3>
              <p className="text-sm m-0" style={{ color: 'var(--text-secondary)' }}>
                {analytics.active}/{analytics.total} active • {formatStorageSize(analytics.totalSize)}
              </p>
            </div>
          </div>
          <Tooltip title="Refresh">
            <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading} />
          </Tooltip>
        </div>
      )}

      {/* Advanced Controls */}
      <Card className="glass-card" size="small">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Input
              placeholder="Search workspaces..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
              prefix={<SearchOutlined />}
              className="simple-search-input"
            />
          </Col>
          <Col xs={12} md={4}>
            <Select
              placeholder="Filter status"
              value={filterStatus}
              onChange={setFilterStatus}
              style={{ width: '100%' }}
            >
              <Option value="all">All Status</Option>
              <Option value="active">Active Only</Option>
              <Option value="inactive">Inactive Only</Option>
            </Select>
          </Col>
          <Col xs={12} md={4}>
            <Select
              placeholder="Sort by"
              value={`${sortField}-${sortOrder}`}
              onChange={(value) => {
                const [field, order] = value.split('-') as [SortField, 'asc' | 'desc'];
                setSortField(field);
                setSortOrder(order);
              }}
              style={{ width: '100%' }}
            >
              <Option value="created-desc">Newest First</Option>
              <Option value="created-asc">Oldest First</Option>
              <Option value="name-asc">Name A-Z</Option>
              <Option value="name-desc">Name Z-A</Option>
              <Option value="size-desc">Largest First</Option>
              <Option value="size-asc">Smallest First</Option>
            </Select>
          </Col>
          <Col xs={24} md={8}>
            <div className="flex justify-between items-center">
              <Text style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                {filteredStorages.length} of {storages.length} workspaces
              </Text>
              <Space>
                {selectedRowKeys.length > 0 && (
                  <Dropdown
                    menu={{
                      items: [
                        { key: 'delete', label: 'Delete Selected', icon: <DeleteOutlined />, danger: true },
                      ],
                      onClick: ({ key }) => handleBulkAction(key)
                    }}
                  >
                    <Button size="small" type="primary" danger>
                      Actions ({selectedRowKeys.length})
                    </Button>
                  </Dropdown>
                )}
              </Space>
            </div>
          </Col>
        </Row>
      </Card>

      {filteredStorages.length === 0 ? (
        <Card className="glass-card">
          <Empty
            image={<DatabaseOutlined style={{ fontSize: '48px', color: 'var(--text-tertiary)' }} />}
            description={
              <div>
                <Title level={4} style={{ color: 'var(--text-secondary)' }}>
                  {storages.length === 0 ? 'No Workspaces Yet' : 'No Results Found'}
                </Title>
                <Text style={{ color: 'var(--text-tertiary)' }}>
                  {storages.length === 0 
                    ? 'Create your first workspace to store and manage your research data.'
                    : 'Try adjusting your search or filter criteria.'
                  }
                </Text>
              </div>
            }
          >
            {storages.length === 0 && !hideCreateButton && (
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setShowCreateForm(true)}
                size="large"
              >
                Create First Workspace
              </Button>
            )}
          </Empty>
        </Card>
      ) : (
        <StorageTable 
          storages={filteredStorages}
          loading={isLoading}
          selectedRowKeys={selectedRowKeys}
          onSelectionChange={setSelectedRowKeys}
          onToggleDetails={toggleDetails}
          onDelete={handleDeleteStorage}
          showDetails={showDetails}
          deleteConfirm={deleteConfirm}
          onToggleDeleteConfirm={toggleDeleteConfirm}
          deleteMutation={deleteMutation}
          formatStorageSize={formatStorageSize}
          formatDateTime={formatDateTime}
          getStorageIcon={getStorageIcon}
          copyToClipboard={copyToClipboard}
        />
      )}

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

// Modern Table View Component
interface StorageTableProps {
  storages: StorageItem[];
  loading: boolean;
  selectedRowKeys: string[];
  onSelectionChange: (keys: string[]) => void;
  onToggleDetails: (id: string) => void;
  onDelete: (id: string) => void;
  showDetails: Record<string, boolean>;
  deleteConfirm: Record<string, boolean>;
  onToggleDeleteConfirm: (id: string) => void;
  deleteMutation: any;
  formatStorageSize: (bytes: number) => string;
  formatDateTime: (date: string) => string;
  getStorageIcon: (storage: StorageItem) => JSX.Element;
  copyToClipboard: (text: string) => void;
}

function StorageTable({
  storages,
  loading,
  selectedRowKeys,
  onSelectionChange,
  onToggleDetails,
  onDelete,
  formatStorageSize,
  formatDateTime,
  getStorageIcon,
  copyToClipboard,
}: StorageTableProps) {
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);
  const columns = [
    {
      title: 'Workspace',
      dataIndex: 'display_name',
      key: 'name',
      render: (name: string, record: StorageItem) => (
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">
            {getStorageIcon(record)}
          </div>
          <div>
            <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {name || record.bucket_name || 'Unknown'}
            </div>
            <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {record.bucket_name}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'storage_class',
      key: 'class',
      width: 120,
      render: (storageClass: string) => (
        <Tag color="blue">{(storageClass || 'standard').toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Size',
      dataIndex: 'size_bytes',
      key: 'size',
      width: 100,
      render: (size: number) => (
        <Text style={{ fontFamily: 'mono' }}>{formatStorageSize(size || 0)}</Text>
      ),
      sorter: (a: StorageItem, b: StorageItem) => (a.size_bytes || 0) - (b.size_bytes || 0),
    },
    {
      title: 'Objects',
      dataIndex: 'object_count',
      key: 'objects',
      width: 80,
      render: (count: number) => (
        <Text>{count || 0}</Text>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created',
      width: 150,
      render: (date: string) => (
        <div className="text-xs">
          <div>{new Date(date).toLocaleDateString()}</div>
          <div style={{ color: 'var(--text-secondary)' }}>
            {new Date(date).toLocaleTimeString()}
          </div>
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: any, record: StorageItem) => (
        <Space size="small">
          <Tooltip title="Manage Files">
            <Button
              size="small"
              icon={<FileOutlined />}
              disabled={record.status !== 'active'}
              onClick={() => {
                // Expand the row if not already expanded
                if (!expandedRowKeys.includes(record.id)) {
                  setExpandedRowKeys([...expandedRowKeys, record.id]);
                }
                // Small delay to ensure the row is expanded, then focus on files tab
                setTimeout(() => {
                  const filesTab = document.querySelector(`[data-node-key="files"]`);
                  if (filesTab) {
                    (filesTab as HTMLElement).click();
                  }
                }, 100);
              }}
            />
          </Tooltip>
          <Tooltip title="Copy Bucket Name">
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(record.bucket_name || '')}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => onDelete(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <Card className="glass-card">
      <Table
        columns={columns}
        dataSource={storages.map(s => ({ ...s, key: s.id }))}
        loading={loading}
        rowSelection={{
          selectedRowKeys,
          onChange: onSelectionChange,
          checkStrictly: true,
        }}
        pagination={{
          pageSize: 10,
          size: 'small',
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} workspaces`,
        }}
        size="middle"
        expandable={{
          expandedRowKeys,
          onExpandedRowsChange: (keys) => setExpandedRowKeys(keys as string[]),
          expandedRowRender: (record) => (
            <div style={{ margin: '16px 0' }}>
              <Tabs size="small" defaultActiveKey="details">
                <Tabs.TabPane tab="Details" key="details">
                  <Row gutter={[24, 16]}>
                    <Col span={8}>
                      <div>
                        <Text strong>Storage ID:</Text>
                        <br />
                        <Text copyable style={{ fontFamily: 'mono', fontSize: '12px' }}>
                          {record.id}
                        </Text>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div>
                        <Text strong>Location:</Text>
                        <br />
                        <Text>{record.location || record.region || 'Unknown'}</Text>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div>
                        <Text strong>Last Modified:</Text>
                        <br />
                        <Text>{formatDateTime(record.updated_at || record.created_at)}</Text>
                      </div>
                    </Col>
                  </Row>
                </Tabs.TabPane>
                <Tabs.TabPane tab="Files" key="files" disabled={record.status !== 'active'}>
                  {record.status === 'active' ? (
                    <StorageFileManager 
                      storageId={record.id} 
                      storageName={record.display_name || 'Workspace'}
                    />
                  ) : (
                    <Text type="secondary">File management requires active workspace</Text>
                  )}
                </Tabs.TabPane>
              </Tabs>
            </div>
          ),
        }}
      />
    </Card>
  );
}

