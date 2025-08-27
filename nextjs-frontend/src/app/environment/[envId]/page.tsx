'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  Button,
  Space,
  Typography,
  Alert,
  Spin,
  Tooltip,
  Tag,
  Divider,
  Modal,
  message
} from 'antd';
import {
  ReloadOutlined,
  ArrowLeftOutlined,
  FullscreenOutlined,
  InfoCircleOutlined,
  LinkOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { formatDateTime, getStatusColor } from '@/lib/utils';
import type { Environment } from '@/types';
import MainLayout from '@/components/layout/MainLayout';

const { Title, Text, Paragraph } = Typography;

export default function EnvironmentAccessPage() {
  // Initialize all hooks first, before any conditional logic
  const params = useParams();
  const router = useRouter();
  const [iframeKey, setIframeKey] = useState(0);
  const [iframeError, setIframeError] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  // Extract envId after hooks are initialized
  const envId = params?.envId as string;

  // Debug logging
  console.log('EnvironmentAccessPage params:', params);
  console.log('EnvironmentAccessPage envId:', envId);

  // Fetch environment details
  const {
    data: environment,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['environment', envId],
    queryFn: async () => {
      if (!envId) {
        throw new Error('Environment ID is required');
      }

      try {
        console.log('Fetching environment with ID:', envId);
        const response = await apiClient.getEnvironmentById(envId);
        console.log('Environment API response:', response);

        if (response.status === 'success' && response.environment) {
          return response.environment;
        }
        throw new Error(response.message || 'Environment not found');
      }
      catch (error) {
        console.error('Failed to fetch environment:', error);
        throw error;
      }
    },
    refetchInterval: (query) => {
      // In modern TanStack Query, the function receives the query object.
      const data = query.state.data;
      return data && data.status === 'pending' ? 5000 : 30000;
    },
    enabled: !!envId && envId !== 'undefined' // Enable query only when envId is available

  });

  // Handle iframe reload
  const handleIframeReload = () => {
    setIframeKey(prev => prev + 1);
    setIframeError(false);
  };

  // Handle external link
  const handleExternalLink = () => {
    if (environment?.url) {
      window.open(environment.url, '_blank', 'noopener,noreferrer');
    }
  };

  // Handle iframe error
  const handleIframeError = () => {
    setIframeError(true);
  };

  // Get application type from URL or environment metadata
  const getAppType = (url: string) => {
    if (url.includes('streamlit')) return 'Streamlit';
    if (url.includes('jupyter')) return 'Jupyter';
    if (url.includes('rstudio')) return 'RStudio';
    if (url.includes('react')) return 'React App';
    return 'Web Application';
  };

  // Handle different states after all hooks are called
  // Show loading if envId is not available yet or if query is loading
  if (!envId || isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <Spin size="large" />
          <div className="ml-4">
            {!envId ? 'Loading environment...' : 'Fetching environment details...'}
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error || !environment) {
    return (
      <MainLayout>
        <Alert
          message="Environment Not Found"
          description="The requested environment could not be found or accessed."
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={() => refetch()}>
                Retry
              </Button>
              <Button size="small" onClick={() => router.push('/environments')}>
                Back to Environments
              </Button>
            </Space>
          }
        />
      </MainLayout>
    );
  }

  if (environment.status !== 'running') {
    return (
      <MainLayout>
        <Alert
          message={`Environment ${environment.status}`}
          description={`This environment is currently ${environment.status}. Please wait for it to be running before accessing it.`}
          type="warning"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={() => refetch()}>
                Refresh Status
              </Button>
              <Button size="small" onClick={() => router.push('/environments')}>
                Back to Environments
              </Button>
            </Space>
          }
        />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-4">
        {/* Header */}
        <Card>
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => router.push('/environments')}
              >
                Back
              </Button>
              <div>
                <Title level={3} className="mb-1">
                  Environment Access
                </Title>
                <Space size="small">
                  <Tag color={getStatusColor(environment.status)}>
                    {environment.status.toUpperCase()}
                  </Tag>
                  <Text type="secondary">
                    {getAppType(environment.url || '')}
                  </Text>
                  <Text type="secondary">•</Text>
                  <Text type="secondary">
                    {environment.env_id || environment.id}
                  </Text>
                </Space>
              </div>
            </div>

            <Space>
              <Tooltip title="Refresh application">
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleIframeReload}
                />
              </Tooltip>
              <Tooltip title="Open in new tab">
                <Button
                  icon={<LinkOutlined />}
                  onClick={handleExternalLink}
                  type="primary"
                >
                  Open External
                </Button>
              </Tooltip>
              <Tooltip title="Toggle fullscreen">
                <Button
                  icon={<FullscreenOutlined />}
                  onClick={() => setFullscreen(!fullscreen)}
                />
              </Tooltip>
            </Space>
          </div>

          <Divider />

          {/* Environment Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <Text type="secondary">Created:</Text>
              <div>{formatDateTime(environment.created_at)}</div>
            </div>
            <div>
              <Text type="secondary">URL:</Text>
              <div className="truncate">
                <a
                  href={environment.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-600"
                >
                  {environment.url}
                </a>
              </div>
            </div>
            <div>
              <Text type="secondary">Resources:</Text>
              <div>
                {environment.resource_config && (
                  <span>
                    {environment.resource_config.cpu_limit} CPU, {environment.resource_config.memory_limit}
                  </span>
                )}
              </div>
            </div>
            <div>
              <Text type="secondary">Storage:</Text>
              <div>
                {environment.resource_config?.storage_size || 'Default'}
              </div>
            </div>
          </div>
        </Card>

        {/* iframe Container */}
        <div className="w-full" style={{ height: '850px' }}>
          <Card 
            className="p-0 overflow-hidden h-full" 
            bodyStyle={{ padding: 0, height: '100%' }}
          >
            {iframeError ? (
              <div className="flex flex-col items-center justify-center h-full space-y-4">
                <Alert
                  message="Application Loading Error"
                  description="The application could not be loaded in the iframe. This might be due to security policies."
                  type="warning"
                  showIcon
                  action={
                    <Space>
                      <Button size="small" onClick={handleIframeReload}>
                        Retry
                      </Button>
                      <Button size="small" type="primary" onClick={handleExternalLink}>
                        Open External
                      </Button>
                    </Space>
                  }
                />
              </div>
            ) : (
              <iframe
                key={iframeKey}
                src={environment.url}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  minHeight: '800px'
                }}
                title={`Environment ${environment.env_id || environment.id}`}
                onError={handleIframeError}
                onLoad={() => {
                  console.log('Iframe loaded successfully');
                  setIframeError(false);
                }}
                // Security attributes
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
                allow="fullscreen; clipboard-read; clipboard-write"
              />
            )}
          </Card>
        </div>

        {/* Help Text */}
        <Alert
          message="Having trouble with the embedded view?"
          description={
            <div>
              <Paragraph className="mb-2">
                Some applications may not display correctly in the embedded iframe due to security policies.
                If you're experiencing issues, try:
              </Paragraph>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Clicking the "Open External" button to access the application in a new tab</li>
                <li>Refreshing the application using the reload button</li>
                <li>Checking if the application is fully started (may take a few minutes)</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />
      </div>

      {/* Fullscreen Modal */}
      <Modal
        open={fullscreen}
        onCancel={() => setFullscreen(false)}
        footer={null}
        width="100vw"
        style={{ top: 0, padding: 0 }}
        bodyStyle={{ height: '100vh', padding: 0 }}
      >
        <div className="h-full flex flex-col">
          <div className="flex justify-between items-center p-4 border-b">
            <div>
              <Text strong>{getAppType(environment.url || '')} - {environment.env_id}</Text>
            </div>
            <Space>
              <Button onClick={handleIframeReload} icon={<ReloadOutlined />}>
                Refresh
              </Button>
              <Button onClick={handleExternalLink} icon={<LinkOutlined />}>
                External
              </Button>
              <Button onClick={() => setFullscreen(false)}>
                Exit Fullscreen
              </Button>
            </Space>
          </div>
          <div style={{ flex: 1 }}>
            <iframe
              src={environment.url}
              style={{
                width: '100%',
                height: '100%',
                border: 'none'
              }}
              title={`Environment ${environment.env_id || environment.id} - Fullscreen`}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
              allow="fullscreen; clipboard-read; clipboard-write"
            />
          </div>
        </div>
      </Modal>
    </MainLayout>
  );
}