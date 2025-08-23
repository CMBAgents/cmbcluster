'use client';

import React, { useState } from 'react';
import {
  Card,
  Select,
  Button,
  Typography,
  Space,
  Radio,
  Alert,
  Divider,
  Tag,
  Row,
  Col,
} from 'antd';
import {
  DatabaseOutlined,
  PlusOutlined,
  FolderOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { StorageItem } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface StorageWorkspaceSelectorProps {
  storages: StorageItem[];
  onStorageSelect?: (storage: StorageItem | null) => void;
  showTitle?: boolean;
}

export default function StorageWorkspaceSelector({ 
  storages, 
  onStorageSelect,
  showTitle = true 
}: StorageWorkspaceSelectorProps) {
  const [selectionType, setSelectionType] = useState<'existing' | 'create_new'>('existing');
  const [selectedStorageId, setSelectedStorageId] = useState<string | null>(null);

  const activeStorages = storages.filter(s => s.status === 'active');
  const selectedStorage = activeStorages.find(s => s.id === selectedStorageId);

  const handleStorageSelect = (storageId: string) => {
    setSelectedStorageId(storageId);
    const storage = activeStorages.find(s => s.id === storageId);
    onStorageSelect?.(storage || null);
  };

  const handleSelectionTypeChange = (type: 'existing' | 'create_new') => {
    setSelectionType(type);
    if (type === 'create_new') {
      setSelectedStorageId(null);
      onStorageSelect?.(null);
    }
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
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  if (!showTitle && activeStorages.length === 0) {
    return (
      <Alert
        message="No Active Workspaces"
        description="You need to create at least one active workspace before launching environments."
        type="warning"
        showIcon
        action={
          <Button type="primary" size="small" icon={<PlusOutlined />}>
            Create Workspace
          </Button>
        }
      />
    );
  }

  return (
    <Card>
      {showTitle && (
        <Title level={4} className="mb-4 flex items-center">
          <FolderOutlined className="mr-2 text-blue-500" />
          Workspace Storage Selection
        </Title>
      )}

      {activeStorages.length === 0 ? (
        // No existing storages - auto create message
        <div className="text-center py-6">
          <DatabaseOutlined className="text-4xl text-blue-400 mb-4" />
          <Title level={5}>Welcome! We'll create your first workspace automatically.</Title>
          <Paragraph type="secondary">
            Your workspace will be given a unique research-themed name like:
          </Paragraph>
          <div className="space-x-2 mb-4">
            <Tag color="blue">Research Alpha</Tag>
            <Tag color="green">Research Beta</Tag>
            <Tag color="purple">Research Gamma</Tag>
          </div>
          <Alert
            message="First-time Setup"
            description="A new workspace will be automatically created when you launch your first environment."
            type="info"
            showIcon
          />
        </div>
      ) : (
        // Existing storages available
        <div className="space-y-4">
          <Paragraph type="secondary">
            Choose your workspace storage for environment data and files.
          </Paragraph>

          {/* Selection Type Radio */}
          <Radio.Group
            value={selectionType}
            onChange={(e) => handleSelectionTypeChange(e.target.value)}
            className="w-full"
          >
            <Space direction="vertical" className="w-full">
              <Radio value="existing">
                <Text strong>Continue with existing workspace</Text>
                <br />
                <Text type="secondary" className="ml-6">
                  Use one of your current workspaces
                </Text>
              </Radio>
              <Radio value="create_new">
                <Text strong>Start fresh with new workspace</Text>
                <br />
                <Text type="secondary" className="ml-6">
                  Create a brand new isolated workspace
                </Text>
              </Radio>
            </Space>
          </Radio.Group>

          <Divider />

          {selectionType === 'existing' ? (
            <div className="space-y-4">
              <Title level={5}>Your Existing Workspaces</Title>
              
              {/* Workspace Selection Grid */}
              <div className="space-y-3">
                {activeStorages.map((storage) => (
                  <Card
                    key={storage.id}
                    size="small"
                    className={`cursor-pointer transition-all ${
                      selectedStorageId === storage.id
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 hover:border-blue-300 hover:shadow-sm'
                    }`}
                    onClick={() => handleStorageSelect(storage.id)}
                  >
                    <Row align="middle" gutter={16}>
                      <Col flex="auto">
                        <div className="flex items-center space-x-3">
                          {selectedStorageId === storage.id && (
                            <CheckCircleOutlined className="text-blue-500 text-lg" />
                          )}
                          <div>
                            <Text strong className="text-base">
                              {storage.display_name || 'Unknown Workspace'}
                            </Text>
                            <br />
                            <Text type="secondary" className="text-sm">
                              Bucket: {storage.bucket_name || 'unknown'}
                            </Text>
                          </div>
                        </div>
                      </Col>
                      
                      <Col>
                        <div className="text-right">
                          <Text className="text-sm">Created: {formatDateTime(storage.created_at)}</Text>
                          <br />
                          <Text type="secondary" className="text-sm">
                            Size: {formatStorageSize(storage.size_bytes || 0)}
                          </Text>
                        </div>
                      </Col>
                      
                      <Col>
                        <div className="text-right">
                          <Text className="text-sm">Objects: {storage.object_count || 0}</Text>
                          <br />
                          <Text type="secondary" className="text-sm">
                            Class: {storage.storage_class?.toUpperCase() || 'STANDARD'}
                          </Text>
                        </div>
                      </Col>
                    </Row>
                  </Card>
                ))}
              </div>

              {/* Selected Storage Summary */}
              {selectedStorage && (
                <>
                  <Divider />
                  <Card size="small" className="bg-green-50 border-green-200">
                    <Title level={5} className="mb-2 text-green-700">
                      ✅ Selected Workspace
                    </Title>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Text strong>Name:</Text> {selectedStorage.display_name || 'Unknown'}
                        <br />
                        <Text strong>Size:</Text> {formatStorageSize(selectedStorage.size_bytes || 0)}
                      </Col>
                      <Col span={12}>
                        <Text strong>Objects:</Text> {selectedStorage.object_count || 0}
                        <br />
                        <Text strong>Class:</Text> {selectedStorage.storage_class?.toUpperCase() || 'STANDARD'}
                      </Col>
                    </Row>
                  </Card>
                </>
              )}
            </div>
          ) : (
            // Create new workspace option
            <div className="space-y-4">
              <Title level={5}>Create New Workspace</Title>
              
              <Card size="small" className="bg-blue-50 border-blue-200">
                <div className="text-center py-4">
                  <DatabaseOutlined className="text-3xl text-blue-500 mb-3" />
                  <Title level={5} className="mb-2 text-blue-700">
                    New Research Workspace
                  </Title>
                  <Paragraph type="secondary" className="mb-4">
                    A new workspace will be created automatically with:
                  </Paragraph>
                  
                  <div className="space-y-2 text-left bg-white rounded p-3 border">
                    <Text>• Unique research workspace name</Text>
                    <br />
                    <Text>• Private and secure storage</Text>
                    <br />
                    <Text>• Automatic versioning enabled</Text>
                    <br />
                    <Text>• Lifecycle management included</Text>
                  </div>
                </div>
              </Card>

              {/* Storage Class Selection (simplified) */}
              <div>
                <Text strong className="block mb-2">Storage Performance:</Text>
                <Select
                  defaultValue="STANDARD"
                  className="w-full"
                  size="large"
                >
                  <Option value="STANDARD">
                    <div>
                      <Text strong>Standard</Text> - Best performance
                      <br />
                      <Text type="secondary" className="text-xs">
                        Recommended for active research data
                      </Text>
                    </div>
                  </Option>
                  <Option value="NEARLINE">
                    <div>
                      <Text strong>Nearline</Text> - Good for monthly access
                      <br />
                      <Text type="secondary" className="text-xs">
                        Cost-effective for less frequent access
                      </Text>
                    </div>
                  </Option>
                  <Option value="COLDLINE">
                    <div>
                      <Text strong>Coldline</Text> - Archive storage
                      <br />
                      <Text type="secondary" className="text-xs">
                        Best for long-term storage
                      </Text>
                    </div>
                  </Option>
                </Select>
              </div>
            </div>
          )}

          {/* Selection Status */}
          {selectionType === 'existing' && !selectedStorage && (
            <Alert
              message="Please select a workspace"
              description="Choose one of your existing workspaces to continue."
              type="warning"
              showIcon
            />
          )}
        </div>
      )}
    </Card>
  );
}
