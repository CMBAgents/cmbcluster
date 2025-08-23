'use client';

import React, { useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Typography,
  Space,
  Tag,
  Divider,
} from 'antd';
import {
  DatabaseOutlined,
  CloudOutlined,
  FileOutlined,
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import type { StorageItem } from '@/types';

const { Title, Text } = Typography;

interface StorageAnalyticsProps {
  storages: StorageItem[];
}

export default function StorageAnalytics({ storages }: StorageAnalyticsProps) {
  const analytics = useMemo(() => {
    const totalStorages = storages.length;
    const activeStorages = storages.filter(s => s.status === 'active').length;
    const totalSize = storages.reduce((acc, s) => acc + (s.size_bytes || 0), 0);
    const totalObjects = storages.reduce((acc, s) => acc + (s.object_count || 0), 0);

    // Storage class breakdown
    const classCounts = storages.reduce((acc, s) => {
      const storageClass = s.storage_class || 'standard';
      acc[storageClass] = (acc[storageClass] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Size by class
    const sizeByClass = storages.reduce((acc, s) => {
      const storageClass = s.storage_class || 'standard';
      acc[storageClass] = (acc[storageClass] || 0) + (s.size_bytes || 0);
      return acc;
    }, {} as Record<string, number>);

    // Largest workspace
    const largestWorkspace = storages.reduce((largest, current) => {
      return (current.size_bytes || 0) > (largest?.size_bytes || 0) ? current : largest;
    }, storages[0]);

    // Most active workspace (by object count)
    const mostActiveWorkspace = storages.reduce((mostActive, current) => {
      return (current.object_count || 0) > (mostActive?.object_count || 0) ? current : mostActive;
    }, storages[0]);

    return {
      totalStorages,
      activeStorages,
      totalSize,
      totalObjects,
      classCounts,
      sizeByClass,
      largestWorkspace,
      mostActiveWorkspace,
    };
  }, [storages]);

  const formatStorageSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const storageClassColors = {
    standard: '#1890ff',
    nearline: '#52c41a', 
    coldline: '#722ed1',
  };

  const storageClassIcons = {
    standard: '⚡',
    nearline: '📊',
    coldline: '❄️',
  };

  if (storages.length === 0) {
    return (
      <Card>
        <div className="text-center py-8">
          <DatabaseOutlined className="text-4xl text-gray-400 mb-4" />
          <Title level={4} type="secondary">No Storage Analytics</Title>
          <Text type="secondary">
            Create your first workspace to see storage analytics and usage statistics.
          </Text>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Statistics */}
      <Card title={
        <Space>
          <BarChartOutlined className="text-blue-500" />
          Storage Overview
        </Space>
      }>
        <Row gutter={16}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Workspaces"
              value={analytics.totalStorages}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Active Workspaces"
              value={analytics.activeStorages}
              suffix={`/ ${analytics.totalStorages}`}
              prefix={<CloudOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Storage Used"
              value={formatStorageSize(analytics.totalSize)}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Objects"
              value={analytics.totalObjects}
              prefix={<PieChartOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* Storage Class Breakdown */}
        <Col xs={24} md={12}>
          <Card title="Storage Class Distribution" className="h-full">
            <div className="space-y-4">
              {Object.entries(analytics.classCounts).map(([storageClass, count]) => {
                const percentage = (count / analytics.totalStorages) * 100;
                const sizeForClass = analytics.sizeByClass[storageClass] || 0;
                
                return (
                  <div key={storageClass} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Space>
                        <span className="text-lg">{storageClassIcons[storageClass as keyof typeof storageClassIcons] || '📦'}</span>
                        <Text strong className="capitalize">{storageClass}</Text>
                        <Tag color={storageClassColors[storageClass as keyof typeof storageClassColors]}>
                          {count} workspace{count !== 1 ? 's' : ''}
                        </Tag>
                      </Space>
                      <Text type="secondary">{formatStorageSize(sizeForClass)}</Text>
                    </div>
                    <Progress
                      percent={percentage}
                      strokeColor={storageClassColors[storageClass as keyof typeof storageClassColors]}
                      size="small"
                      showInfo={false}
                    />
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>

        {/* Usage Statistics */}
        <Col xs={24} md={12}>
          <Card title="Usage Statistics" className="h-full">
            <div className="space-y-4">
              {/* Utilization Rate */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Text strong>Workspace Utilization</Text>
                  <Text type="secondary">
                    {analytics.activeStorages}/{analytics.totalStorages} active
                  </Text>
                </div>
                <Progress
                  percent={(analytics.activeStorages / analytics.totalStorages) * 100}
                  strokeColor="#52c41a"
                  size="small"
                />
              </div>

              <Divider />

              {/* Top Workspaces */}
              {analytics.largestWorkspace && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <TrophyOutlined className="text-yellow-500" />
                    <Text strong>Largest Workspace</Text>
                  </div>
                  <div className="bg-yellow-50 rounded p-3 border border-yellow-200">
                    <Text strong className="block">
                      {analytics.largestWorkspace.display_name || 'Unknown'}
                    </Text>
                    <Text type="secondary" className="text-sm">
                      {formatStorageSize(analytics.largestWorkspace.size_bytes || 0)}
                    </Text>
                  </div>
                </div>
              )}

              {analytics.mostActiveWorkspace && analytics.mostActiveWorkspace.object_count! > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <FileOutlined className="text-blue-500" />
                    <Text strong>Most Active Workspace</Text>
                  </div>
                  <div className="bg-blue-50 rounded p-3 border border-blue-200">
                    <Text strong className="block">
                      {analytics.mostActiveWorkspace.display_name || 'Unknown'}
                    </Text>
                    <Text type="secondary" className="text-sm">
                      {analytics.mostActiveWorkspace.object_count} object{analytics.mostActiveWorkspace.object_count !== 1 ? 's' : ''}
                    </Text>
                  </div>
                </div>
              )}

              {/* Average Size */}
              <div>
                <div className="flex justify-between items-center">
                  <Text strong>Average Workspace Size</Text>
                  <Text>{formatStorageSize(analytics.totalSize / Math.max(analytics.totalStorages, 1))}</Text>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center">
                  <Text strong>Average Objects per Workspace</Text>
                  <Text>{Math.round(analytics.totalObjects / Math.max(analytics.totalStorages, 1))}</Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Storage Trends (placeholder for future implementation) */}
      <Card title="Storage Trends" className="border-dashed">
        <div className="text-center py-8">
          <BarChartOutlined className="text-4xl text-gray-300 mb-4" />
          <Title level={5} type="secondary">Storage Trends</Title>
          <Text type="secondary">
            Historical storage usage charts will be available soon.
            This will show storage growth over time, usage patterns, and cost analysis.
          </Text>
        </div>
      </Card>
    </div>
  );
}
