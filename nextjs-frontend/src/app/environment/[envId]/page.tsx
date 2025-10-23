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
  message,
  Progress
} from 'antd';
import {
  ReloadOutlined,
  ArrowLeftOutlined,
  FullscreenOutlined,
  InfoCircleOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  RocketOutlined,
  CheckCircleOutlined
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
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState('Initializing environment...');

  // Extract envId after hooks are initialized
  const envId = params?.envId as string;

  // Debug logging

  // Fetch environment details
  const {
    data: environment,
    isLoading: isQueryLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['environment', envId],
    queryFn: async () => {
      if (!envId) {
        throw new Error('Environment ID is required');
      }

      try {
        const response = await apiClient.getEnvironmentById(envId);

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

  // Enhanced loading simulation with progress
  useEffect(() => {
    if (!environment?.url) return;
    
    setIsLoading(true);
    setLoadingProgress(0);
    setLoadingMessage('Connecting to environment...');

    const loadingSteps = [
      { progress: 20, message: 'Establishing connection...' },
      { progress: 40, message: 'Loading application...' },
      { progress: 60, message: 'Initializing interface...' },
      { progress: 80, message: 'Preparing workspace...' },
      { progress: 95, message: 'Almost ready...' },
      { progress: 100, message: 'Environment ready!' }
    ];

    let currentStep = 0;
    const stepInterval = setInterval(() => {
      if (currentStep < loadingSteps.length) {
        const step = loadingSteps[currentStep];
        setLoadingProgress(step.progress);
        setLoadingMessage(step.message);
        currentStep++;
        
        if (currentStep === loadingSteps.length) {
          setTimeout(() => setIsLoading(false), 500);
        }
      } else {
        clearInterval(stepInterval);
      }
    }, 800);

    return () => clearInterval(stepInterval);
  }, [environment?.url, iframeKey]);

  // Handle iframe reload
  const handleIframeReload = () => {
    setIframeKey(prev => prev + 1);
    setIframeError(false);
    setIsLoading(true);
    setLoadingProgress(0);
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

  // Get application display name, with fallback to type detection
  const getApplicationName = (environment: Environment) => {
    // First priority: use actual application name if available
    if (environment.application_name) {
      return environment.application_name;
    }
    
    // Second priority: detect from URL for legacy environments
    if (environment.url) {
      if (environment.url.includes('streamlit')) return 'Streamlit Application';
      if (environment.url.includes('jupyter')) return 'Jupyter Notebook';
      if (environment.url.includes('rstudio')) return 'RStudio Server';
      if (environment.url.includes('react')) return 'React Application';
      if (environment.url.includes('python')) return 'Python Environment';
    }
    
    // Third priority: use image name if available
    if (environment.image) {
      const imageName = environment.image.split('/').pop()?.split(':')[0];
      if (imageName) {
        return imageName.charAt(0).toUpperCase() + imageName.slice(1) + ' Environment';
      }
    }
    
    // Fallback
    return 'Research Environment';
  };

  // Handle different states after all hooks are called
  // Show loading if envId is not available yet or if query is loading
  if (!envId || isQueryLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center" style={{ height: '60vh' }}>
          <Card className="glass-card" style={{ width: '400px', textAlign: 'center' }}>
            <div style={{ padding: '40px 20px' }}>
              <div className="icon-container primary mb-4" style={{ width: '64px', height: '64px', margin: '0 auto 24px' }}>
                <RocketOutlined style={{ fontSize: '32px' }} />
              </div>
              <Title level={3} style={{ color: 'var(--text-primary)', marginBottom: '16px' }}>
                Loading Environment
              </Title>
              <Text style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '24px' }}>
                {!envId ? 'Initializing environment access...' : 'Fetching environment details...'}
              </Text>
              <Spin size="large" />
            </div>
          </Card>
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
        {/* Professional Header */}
        <Card className="glass-card">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Tooltip title="Return to environments list">
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => router.push('/environments')}
                  className="glass-button"
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="icon-container success p-2">
                    <RocketOutlined style={{ fontSize: '18px' }} />
                  </div>
                  <Title level={2} style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {getApplicationName(environment)}
                  </Title>
                </div>
                <Space size="medium">
                  <Tag 
                    color={getStatusColor(environment.status)}
                    style={{ fontSize: '12px', padding: '4px 8px', fontWeight: '500' }}
                  >
                    {environment.status.toUpperCase()}
                  </Tag>
                  <Text style={{ color: 'var(--text-secondary)', fontFamily: 'mono' }}>
                    {environment.env_id || environment.id}
                  </Text>
                  {environment.resource_config && (
                    <Text style={{ color: 'var(--text-secondary)' }}>
                      {environment.resource_config.cpu_limit} CPU • {environment.resource_config.memory_limit}
                    </Text>
                  )}
                </Space>
              </div>
            </div>

            <Space size="small" wrap>
              <Tooltip title="Refresh the environment and reload the application">
                <Button
                  type="default"
                  icon={<ReloadOutlined />}
                  onClick={handleIframeReload}
                  className="glass-button"
                  loading={isLoading}
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
              <Tooltip title="Open environment in a new browser tab">
                <Button
                  type="primary"
                  icon={<LinkOutlined />}
                  onClick={handleExternalLink}
                  className="glass-button"
                  shape="circle"
                  style={{
                    background: 'var(--interactive-primary)',
                    borderColor: 'var(--interactive-primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
              <Tooltip title="View environment in fullscreen mode">
                <Button
                  type="default"
                  icon={<FullscreenOutlined />}
                  onClick={() => setFullscreen(!fullscreen)}
                  className="glass-button"
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
            </Space>
          </div>
        </Card>

        {/* Application Container with Loading */}
        <div className="w-full" style={{ height: '85vh', minHeight: '700px' }}>
          <Card 
            className="glass-card overflow-hidden h-full" 
            bodyStyle={{ padding: 0, height: '100%', position: 'relative' }}
          >
            {/* Loading Overlay */}
            {isLoading && (
              <div 
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'var(--glass-bg-primary)',
                  backdropFilter: 'blur(8px)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 10
                }}
              >
                <div style={{ textAlign: 'center', maxWidth: '400px' }}>
                  <div className="icon-container primary mb-6" style={{ width: '80px', height: '80px', margin: '0 auto 32px' }}>
                    <RocketOutlined style={{ fontSize: '40px' }} />
                  </div>
                  
                  <Title level={2} style={{ color: 'var(--text-primary)', marginBottom: '16px' }}>
                    {loadingProgress === 100 ? 'Ready!' : 'Loading Environment'}
                  </Title>
                  
                  <Text style={{ 
                    color: 'var(--text-secondary)', 
                    display: 'block', 
                    marginBottom: '32px',
                    fontSize: '16px'
                  }}>
                    {loadingMessage}
                  </Text>
                  
                  <div style={{ marginBottom: '24px' }}>
                    <Progress
                      percent={loadingProgress}
                      strokeColor={{
                        '0%': 'var(--primary-400)',
                        '50%': 'var(--primary-500)',
                        '100%': 'var(--success-500)',
                      }}
                      trailColor="var(--glass-border)"
                      size="default"
                      showInfo={false}
                      style={{ marginBottom: '16px' }}
                    />
                    <Text style={{ color: 'var(--text-tertiary)', fontSize: '14px' }}>
                      {loadingProgress}% Complete
                    </Text>
                  </div>
                  
                  {loadingProgress === 100 && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                      <CheckCircleOutlined style={{ color: 'var(--success-500)', fontSize: '16px' }} />
                      <Text style={{ color: 'var(--success-600)', fontWeight: '500' }}>
                        Environment is ready!
                      </Text>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Error State */}
            {iframeError ? (
              <div className="flex flex-col items-center justify-center h-full" style={{ padding: '48px' }}>
                <Alert
                  message="Application Loading Error"
                  description="The application could not be loaded. This might be due to network issues or security policies."
                  type="warning"
                  showIcon
                  action={
                    <Space size="small">
                      <Tooltip title="Reload the application and try again">
                        <Button
                          onClick={handleIframeReload}
                          icon={<ReloadOutlined />}
                          shape="circle"
                          style={{
                            borderColor: 'var(--border-primary)',
                            color: 'var(--text-primary)',
                            background: 'var(--glass-bg-secondary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '40px',
                            height: '40px'
                          }}
                        />
                      </Tooltip>
                      <Tooltip title="Open environment in a new browser tab">
                        <Button
                          type="primary"
                          onClick={handleExternalLink}
                          icon={<LinkOutlined />}
                          shape="circle"
                          style={{
                            background: 'var(--interactive-primary)',
                            borderColor: 'var(--interactive-primary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '40px',
                            height: '40px'
                          }}
                        />
                      </Tooltip>
                    </Space>
                  }
                  className="glass-alert"
                  style={{ maxWidth: '500px' }}
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
                  opacity: isLoading ? 0 : 1,
                  transition: 'opacity 0.3s ease-in-out'
                }}
                title={`Environment ${environment.env_id || environment.id}`}
                onError={handleIframeError}
                onLoad={() => {
                  setIframeError(false);
                }}
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
                allow="fullscreen; clipboard-read; clipboard-write"
              />
            )}
          </Card>
        </div>

        {/* Quick Help */}
        {iframeError && (
          <Card className="glass-card">
            <Alert
              message="Need help accessing your environment?"
              description="If the embedded view isn't working, try opening the application in a new tab using the 'Open External' button above."
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
              className="glass-alert"
            />
          </Card>
        )}
      </div>

      {/* Fullscreen Modal */}
      <Modal
        open={fullscreen}
        onCancel={() => setFullscreen(false)}
        footer={null}
        width="100vw"
        style={{ top: 0, padding: 0, background: 'var(--bg-primary)' }}
        bodyStyle={{ height: '100vh', padding: 0 }}
        styles={{
          content: {
            background: 'var(--bg-primary)',
            borderRadius: 0
          }
        }}
      >
        <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
          <div 
            className="flex justify-between items-center px-6 py-4"
            style={{ 
              background: 'var(--glass-bg-primary)', 
              borderBottom: '1px solid var(--border-primary)',
              backdropFilter: 'blur(8px)'
            }}
          >
            <div className="flex items-center gap-3">
              <div className="icon-container primary p-2">
                <RocketOutlined style={{ fontSize: '16px' }} />
              </div>
              <Text strong style={{ color: 'var(--text-primary)' }}>
                {getApplicationName(environment)} - {environment.env_id}
              </Text>
            </div>
            <Space size="small">
              <Tooltip title="Refresh the environment and reload the application">
                <Button
                  onClick={handleIframeReload}
                  icon={<ReloadOutlined />}
                  className="glass-button"
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
              <Tooltip title="Open environment in a new browser tab">
                <Button
                  onClick={handleExternalLink}
                  icon={<LinkOutlined />}
                  className="glass-button"
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
              <Tooltip title="Exit fullscreen mode and return to normal view">
                <Button
                  onClick={() => setFullscreen(false)}
                  type="default"
                  icon={<FullscreenOutlined style={{ transform: 'rotate(45deg)' }} />}
                  className="glass-button"
                  shape="circle"
                  style={{
                    borderColor: 'var(--border-primary)',
                    color: 'var(--text-primary)',
                    background: 'var(--glass-bg-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '40px',
                    height: '40px'
                  }}
                />
              </Tooltip>
            </Space>
          </div>
          <div style={{ flex: 1 }}>
            <iframe
              src={environment.url}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                background: 'var(--bg-primary)'
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