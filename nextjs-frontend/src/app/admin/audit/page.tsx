'use client';

import MainLayout from '@/components/layout/MainLayout';
import { useAdmin } from '@/contexts/AdminContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  Card, 
  Table, 
  Typography, 
  Space, 
  Tag, 
  DatePicker,
  Select,
  Alert,
  Button
} from 'antd';
import {
  FileTextOutlined,
  UserOutlined,
  ClockCircleOutlined,
  SearchOutlined,
  DownloadOutlined
} from '@ant-design/icons';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface AuditLog {
  id: string;
  user: string;
  action: string;
  resource: string;
  details: string;
  timestamp: string;
  ip_address: string;
  status: 'success' | 'failed' | 'warning';
}

function AuditLogsContent() {
  const { currentRole, canSwitchToAdmin } = useAdmin();
  const router = useRouter();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Redirect if not admin
  useEffect(() => {
    if (!canSwitchToAdmin || currentRole !== 'admin') {
      router.push('/');
      return;
    }
  }, [canSwitchToAdmin, currentRole, router]);

  // Mock audit log data
  useEffect(() => {
    setTimeout(() => {
      setLogs([
        {
          id: '1',
          user: '22yash.tiwari@gmail.com',
          action: 'USER_ROLE_CHANGED',
          resource: 'user@example.com',
          details: 'Changed role from user to researcher',
          timestamp: '2024-08-28T15:30:00Z',
          ip_address: '192.168.1.100',
          status: 'success'
        },
        {
          id: '2',
          user: 'user@example.com',
          action: 'ENVIRONMENT_CREATED',
          resource: 'jupyter-env-001',
          details: 'Created new Jupyter environment with 2GB RAM',
          timestamp: '2024-08-28T15:15:00Z',
          ip_address: '192.168.1.105',
          status: 'success'
        },
        {
          id: '3',
          user: 'researcher@example.com',
          action: 'ENVIRONMENT_FAILED',
          resource: 'pytorch-env-003',
          details: 'Environment creation failed due to resource limits',
          timestamp: '2024-08-28T14:45:00Z',
          ip_address: '192.168.1.110',
          status: 'failed'
        },
        {
          id: '4',
          user: '22yash.tiwari@gmail.com',
          action: 'APPLICATION_ADDED',
          resource: 'tensorflow-env',
          details: 'Added new TensorFlow application to store',
          timestamp: '2024-08-28T14:30:00Z',
          ip_address: '192.168.1.100',
          status: 'success'
        },
        {
          id: '5',
          user: 'user@example.com',
          action: 'LOGIN',
          resource: 'auth_system',
          details: 'User successfully logged in via Google OAuth',
          timestamp: '2024-08-28T14:00:00Z',
          ip_address: '192.168.1.105',
          status: 'success'
        },
        {
          id: '6',
          user: 'unknown@example.com',
          action: 'LOGIN_FAILED',
          resource: 'auth_system',
          details: 'Failed login attempt - invalid credentials',
          timestamp: '2024-08-28T13:45:00Z',
          ip_address: '192.168.1.200',
          status: 'failed'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const filteredLogs = filterStatus === 'all' 
    ? logs 
    : logs.filter(log => log.status === filterStatus);

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => (
        <Space>
          <ClockCircleOutlined />
          {new Date(timestamp).toLocaleString()}
        </Space>
      ),
      sorter: (a: AuditLog, b: AuditLog) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      defaultSortOrder: 'descend' as const
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      render: (user: string) => (
        <Space>
          <UserOutlined />
          {user}
        </Space>
      )
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => (
        <Tag color="blue">{action.replace(/_/g, ' ')}</Tag>
      )
    },
    {
      title: 'Resource',
      dataIndex: 'resource',
      key: 'resource',
      render: (resource: string) => (
        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
          {resource}
        </code>
      )
    },
    {
      title: 'Details',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'success' ? 'green' : 
                     status === 'failed' ? 'red' : 'orange';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      }
    }
  ];

  if (!canSwitchToAdmin || currentRole !== 'admin') {
    return null; // Will redirect
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <Title level={2}>
          <FileTextOutlined className="mr-2" />
          Audit Logs
        </Title>
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={() => {
            // TODO: Implement export functionality
            alert('Export functionality will be implemented soon');
          }}
        >
          Export Logs
        </Button>
      </div>

      <Alert
        message="Security Audit Trail"
        description="Complete audit log of all user actions, system events, and security-related activities."
        type="info"
        showIcon
        className="mb-6"
      />

      {/* Filters */}
      <Card className="glass-card mb-6">
        <Space className="w-full" style={{ justifyContent: 'space-between' }}>
          <Space>
            <RangePicker 
              placeholder={['Start Date', 'End Date']}
              style={{ width: 250 }}
            />
            <Select
              value={filterStatus}
              onChange={setFilterStatus}
              style={{ width: 120 }}
            >
              <Option value="all">All Status</Option>
              <Option value="success">Success</Option>
              <Option value="failed">Failed</Option>
              <Option value="warning">Warning</Option>
            </Select>
          </Space>
          <Button 
            icon={<SearchOutlined />}
            onClick={() => {
              // TODO: Implement search functionality
              alert('Search functionality will be implemented soon');
            }}
          >
            Search
          </Button>
        </Space>
      </Card>

      {/* Audit Log Table */}
      <Card title={`Audit Logs (${filteredLogs.length} entries)`} className="glass-card">
        <Table
          columns={columns}
          dataSource={filteredLogs}
          rowKey="id"
          loading={loading}
          pagination={{ 
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} entries`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
}

export default function AuditLogsPage() {
  return (
    <MainLayout>
      <AuditLogsContent />
    </MainLayout>
  );
}