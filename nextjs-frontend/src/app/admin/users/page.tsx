'use client';

import MainLayout from '@/components/layout/MainLayout';
import { useAdmin } from '@/contexts/AdminContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Typography, 
  Space, 
  Tag, 
  Modal, 
  Select, 
  message,
  Popconfirm,
  Alert,
  Input
} from 'antd';
import {
  CrownOutlined,
  UserOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { apiClient } from '@/lib/api-client';
import { UserWithRole } from '@/types';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

function UserManagementContent() {
  const { currentRole, canSwitchToAdmin } = useAdmin();
  const router = useRouter();
  const [users, setUsers] = useState<UserWithRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserWithRole | null>(null);
  const [newRole, setNewRole] = useState<'user' | 'admin' | 'researcher'>('user');
  const [reason, setReason] = useState<string>('');

  // Redirect if not admin
  useEffect(() => {
    if (!canSwitchToAdmin || currentRole !== 'admin') {
      router.push('/');
      return;
    }
  }, [canSwitchToAdmin, currentRole, router]);

  // Load users from API
  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAllUsers();
      if (response.status === 'success' && response.data) {
        setUsers(response.data);
      } else {
        message.error('Failed to load users: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error loading users:', error);
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canSwitchToAdmin && currentRole === 'admin') {
      loadUsers();
    }
  }, [canSwitchToAdmin, currentRole]);

  const handleRoleChange = (user: UserWithRole) => {
    setSelectedUser(user);
    setNewRole(user.role);
    setRoleModalVisible(true);
  };

  const handleRoleSubmit = async () => {
    if (!selectedUser) return;
    
    try {
      const response = await apiClient.updateUserRole(selectedUser.id, newRole, reason);
      if (response.status === 'success') {
        message.success(`Role updated for ${selectedUser.name}`);
        loadUsers(); // Reload to get updated data
      } else {
        message.error('Failed to update role: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating role:', error);
      message.error('Failed to update user role');
    }
    
    setRoleModalVisible(false);
    setSelectedUser(null);
    setReason('');
  };

  const handleDeactivateUser = async (userId: string) => {
    try {
      const response = await apiClient.deactivateUser(userId);
      if (response.status === 'success') {
        message.success('User deactivated successfully');
        loadUsers(); // Reload to get updated data
      } else {
        message.error('Failed to deactivate user: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error deactivating user:', error);
      message.error('Failed to deactivate user');
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: UserWithRole) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email'
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const color = role === 'admin' ? 'gold' : role === 'researcher' ? 'blue' : 'default';
        const icon = role === 'admin' ? <CrownOutlined /> : <UserOutlined />;
        return (
          <Tag color={color} icon={icon}>
            {role.toUpperCase()}
          </Tag>
        );
      }
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date?: string) => date ? new Date(date).toLocaleDateString() : 'Never'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: UserWithRole) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleRoleChange(record)}
          >
            Change Role
          </Button>
          {record.role !== 'admin' && (
            <Popconfirm
              title="Are you sure you want to deactivate this user?"
              onConfirm={() => handleDeactivateUser(record.id)}
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
              >
                Deactivate
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  if (!canSwitchToAdmin || currentRole !== 'admin') {
    return null; // Will redirect
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>
          <CrownOutlined className="mr-2" />
          User Management
        </Title>
      </div>

      <Alert
        message="User Management Dashboard"
        description="Manage user roles and permissions. Only admins can access this page."
        type="info"
        showIcon
        className="mb-6"
      />

      <Card title="All Users" className="glass-card">
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="Change User Role"
        open={roleModalVisible}
        onOk={handleRoleSubmit}
        onCancel={() => setRoleModalVisible(false)}
        okText="Update Role"
      >
        {selectedUser && (
          <div>
            <p><strong>User:</strong> {selectedUser.name} ({selectedUser.email})</p>
            <p><strong>Current Role:</strong> {selectedUser.role}</p>
            <div className="mt-4">
              <label className="block mb-2">New Role:</label>
              <Select
                value={newRole}
                onChange={setNewRole}
                className="w-full"
              >
                <Option value="user">User</Option>
                <Option value="researcher">Researcher</Option>
                <Option value="admin">Admin</Option>
              </Select>
            </div>
            <div className="mt-4">
              <label className="block mb-2">Reason (optional):</label>
              <TextArea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Reason for role change..."
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default function UserManagementPage() {
  return (
    <MainLayout>
      <UserManagementContent />
    </MainLayout>
  );
}