'use client';

import { useSession } from 'next-auth/react';
import { Typography, Card, Row, Col, Button, Space, Tag, Progress } from 'antd';
import { 
  RocketOutlined, 
  PlayCircleOutlined, 
  StopOutlined, 
  ReloadOutlined,
  SettingOutlined,
  CodeOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import MainLayout from '@/components/layout/MainLayout';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const { Title, Text, Paragraph } = Typography;

// Mock environment data - this would come from your API
const mockEnvironments = [
  {
    id: 1,
    name: 'Python Research Environment',
    type: 'Jupyter Lab',
    status: 'running',
    uptime: '2h 15m',
    cpuUsage: 45,
    memoryUsage: 60,
    lastAccessed: '5 minutes ago',
  },
  {
    id: 2,
    name: 'Data Analysis Workspace',
    type: 'VS Code Server',
    status: 'stopped',
    uptime: '0h 0m',
    cpuUsage: 0,
    memoryUsage: 0,
    lastAccessed: '1 hour ago',
  },
  {
    id: 3,
    name: 'Machine Learning Lab',
    type: 'Custom Docker',
    status: 'starting',
    uptime: '0h 2m',
    cpuUsage: 15,
    memoryUsage: 25,
    lastAccessed: 'Just now',
  },
];

function EnvironmentsPage() {
  const { data: session } = useSession();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'starting': return 'processing';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayCircleOutlined />;
      case 'stopped': return <StopOutlined />;
      case 'starting': return <ReloadOutlined spin />;
      default: return <StopOutlined />;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex justify-between items-start">
          <div>
            <Title level={2} className="text-text-primary mb-2">
              Your Environments
            </Title>
            <Paragraph className="text-text-secondary">
              Manage your computational environments, launch new instances, and monitor resource usage.
            </Paragraph>
          </div>
          <Button type="primary" size="large" icon={<RocketOutlined />}>
            New Environment
          </Button>
        </div>

        {/* Environment Cards */}
        <Row gutter={[24, 24]}>
          {mockEnvironments.map((env) => (
            <Col xs={24} lg={8} key={env.id}>
              <Card
                className="bg-background-secondary border-border-primary hover:shadow-lg transition-shadow h-full"
                title={
                  <div className="flex items-center justify-between">
                    <div>
                      <Text strong className="text-text-primary">
                        {env.name}
                      </Text>
                      <br />
                      <Text type="secondary" className="text-sm">
                        {env.type}
                      </Text>
                    </div>
                    <Tag 
                      color={getStatusColor(env.status)} 
                      icon={getStatusIcon(env.status)}
                    >
                      {env.status.toUpperCase()}
                    </Tag>
                  </div>
                }
                actions={[
                  <Button 
                    key="launch" 
                    type="link" 
                    icon={<PlayCircleOutlined />}
                    disabled={env.status === 'running'}
                  >
                    Launch
                  </Button>,
                  <Button 
                    key="stop" 
                    type="link" 
                    icon={<StopOutlined />}
                    disabled={env.status === 'stopped'}
                  >
                    Stop
                  </Button>,
                  <Button 
                    key="settings" 
                    type="link" 
                    icon={<SettingOutlined />}
                  >
                    Settings
                  </Button>,
                ]}
              >
                <Space direction="vertical" size={16} className="w-full">
                  {/* Resource Usage */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Text className="text-text-secondary text-sm">CPU Usage</Text>
                      <Text className="text-text-primary text-sm">{env.cpuUsage}%</Text>
                    </div>
                    <Progress 
                      percent={env.cpuUsage} 
                      size="small" 
                      status={env.cpuUsage > 80 ? 'exception' : 'normal'}
                      showInfo={false}
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <Text className="text-text-secondary text-sm">Memory Usage</Text>
                      <Text className="text-text-primary text-sm">{env.memoryUsage}%</Text>
                    </div>
                    <Progress 
                      percent={env.memoryUsage} 
                      size="small" 
                      status={env.memoryUsage > 80 ? 'exception' : 'normal'}
                      showInfo={false}
                    />
                  </div>

                  {/* Environment Info */}
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Text className="text-text-secondary text-sm flex items-center">
                        <ClockCircleOutlined className="mr-1" />
                        Uptime
                      </Text>
                      <Text className="text-text-primary text-sm">{env.uptime}</Text>
                    </div>
                    <div className="flex justify-between">
                      <Text className="text-text-secondary text-sm">Last Accessed</Text>
                      <Text className="text-text-primary text-sm">{env.lastAccessed}</Text>
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
          ))}

          {/* Create New Environment Card */}
          <Col xs={24} lg={8}>
            <Card
              className="bg-background-secondary border-border-primary border-dashed hover:shadow-lg transition-all hover:border-primary cursor-pointer h-full"
              bodyStyle={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                minHeight: '300px'
              }}
              onClick={() => {/* Handle create new environment */}}
            >
              <Space direction="vertical" align="center" size={16}>
                <div className="text-6xl text-primary opacity-60">
                  <RocketOutlined />
                </div>
                <Title level={4} className="text-text-primary text-center mb-0">
                  Create New Environment
                </Title>
                <Text className="text-text-secondary text-center">
                  Launch a fresh computational environment tailored to your research needs
                </Text>
                <Button type="primary" size="large">
                  Get Started
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Environment Templates */}
        <div>
          <Title level={3} className="text-text-primary mb-4">
            Popular Templates
          </Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
              >
                <Space align="center">
                  <CodeOutlined className="text-primary text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Jupyter Lab</Text>
                    <br />
                    <Text type="secondary" className="text-xs">Python, R, Julia</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
              >
                <Space align="center">
                  <DatabaseOutlined className="text-green-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Data Science</Text>
                    <br />
                    <Text type="secondary" className="text-xs">Pandas, NumPy, Scikit</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
              >
                <Space align="center">
                  <RocketOutlined className="text-purple-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">ML Research</Text>
                    <br />
                    <Text type="secondary" className="text-xs">TensorFlow, PyTorch</Text>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                size="small" 
                className="bg-background-secondary border-border-primary hover:shadow-md transition-shadow cursor-pointer"
                bodyStyle={{ padding: '16px' }}
              >
                <Space align="center">
                  <SettingOutlined className="text-orange-500 text-xl" />
                  <div>
                    <Text strong className="text-text-primary">Custom</Text>
                    <br />
                    <Text type="secondary" className="text-xs">Docker, Custom Image</Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </MainLayout>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <EnvironmentsPage />
    </ProtectedRoute>
  );
}
