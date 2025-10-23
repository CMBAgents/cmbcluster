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
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Alert,
  Upload,
  Image
} from 'antd';
import {
  AppstoreOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DockerOutlined,
  UploadOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { apiClient } from '@/lib/api-client';
import { ApplicationImage, ApplicationImageRequest } from '@/types';
import { getImageUrlSync } from '@/lib/image-utils';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

function ApplicationManagementContent() {
  const { currentRole, canSwitchToAdmin } = useAdmin();
  const router = useRouter();
  const [applications, setApplications] = useState<ApplicationImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingApp, setEditingApp] = useState<ApplicationImage | null>(null);
  const [form] = Form.useForm();
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [uploading, setUploading] = useState(false);

  // Redirect if not admin
  useEffect(() => {
    if (!canSwitchToAdmin || currentRole !== 'admin') {
      router.push('/');
      return;
    }
  }, [canSwitchToAdmin, currentRole, router]);

  // Load applications from API
  const loadApplications = async () => {
    try {
      setLoading(true);
     
      const response = await apiClient.getAdminApplications();
      
      if (response.status === 'success' && response.data) {
        setApplications(response.data);
      } else {
        console.error('Failed to load applications - invalid response:', response);
        message.error('Failed to load applications: ' + (response.error || response.message || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error loading applications:', error);
      message.error('Failed to load applications: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canSwitchToAdmin && currentRole === 'admin') {
      loadApplications();
    }
  }, [canSwitchToAdmin, currentRole]);

  const handleAdd = () => {
    form.resetFields();
    setEditingApp(null);
    setImageFile(null);
    setImagePreview('');
    setModalVisible(true);
  };

  const handleEdit = (app: ApplicationImage) => {
    setEditingApp(app);
    form.setFieldsValue({
      ...app,
      tags: app.tags && Array.isArray(app.tags) ? app.tags.join(', ') : ''
    });
    setImageFile(null);
    setImagePreview(getImageUrlSync(app.icon_url) || '');
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      setUploading(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('name', values.name);
      formData.append('summary', values.summary);
      formData.append('image_path', values.image_path);
      formData.append('category', values.category);
      formData.append('port', (values.port || 8888).toString());
      formData.append('working_dir', values.working_dir || '/cmbagent');
      formData.append('tags', values.tags || '');

      if (imageFile) {
        formData.append('image_file', imageFile);
      }
      
      if (editingApp) {
        // Update existing with image support
        // Use apiClient which handles authentication properly via NextAuth
        const response = await apiClient.updateApplicationWithImage(editingApp.id, formData);
        
        if (response.status === 'success') {
          message.success('Application updated successfully');
          loadApplications();
        } else {
          message.error('Failed to update application: ' + (response.error || response.message || 'Unknown error'));
        }
      } else {
        // Add new with image support
        // Use apiClient which handles authentication properly via NextAuth
        const response = await apiClient.createApplicationWithImage(formData);
        
        if (response.status === 'success') {
          message.success('Application added successfully');
          loadApplications();
        } else {
          message.error('Failed to add application: ' + (response.error || response.message || 'Unknown error'));
        }
      }
      
      setModalVisible(false);
      form.resetFields();
      setImageFile(null);
      setImagePreview('');
    } catch (error) {
      console.error('Error saving application:', error);
      message.error('Failed to save application');
    } finally {
      setUploading(false);
    }
  };
  
  const handleImageChange = (info: any) => {
    const file = info.file;
    
    if (file.status === 'uploading') {
      return;
    }
    
    // Validate file type
    if (!file.type?.startsWith('image/')) {
      message.error('Please upload only image files!');
      return;
    }
    
    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      message.error('Image size must be less than 5MB!');
      return;
    }
    
    setImageFile(file.originFileObj || file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file.originFileObj || file);
  };
  
  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview('');
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await apiClient.deleteApplication(id);
      if (response.status === 'success') {
        message.success('Application deleted successfully');
        loadApplications(); // Reload to reflect deletion
      } else {
        message.error('Failed to delete application: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error deleting application:', error);
      message.error('Failed to delete application');
    }
  };

  const handleToggleStatus = async (app: ApplicationImage) => {
    try {
      const response = await apiClient.updateApplication(app.id, {
        is_active: !app.is_active
      });
      if (response.status === 'success') {
        message.success(`Application ${app.is_active ? 'deactivated' : 'activated'}`);
        loadApplications(); // Reload to reflect status change
      } else {
        message.error('Failed to update application status: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating application status:', error);
      message.error('Failed to update application status');
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ApplicationImage) => (
        <Space>
          {record.icon_url ? (
            <Image
              src={getImageUrlSync(record.icon_url)}
              alt={record.name}
              width={32}
              height={32}
              className="object-cover rounded"
              fallback={<DockerOutlined style={{ fontSize: 24 }} />}
              preview={false}
            />
          ) : (
            <DockerOutlined style={{ fontSize: 24 }} />
          )}
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color="blue">{category}</Tag>
      )
    },
    {
      title: 'Image Path',
      dataIndex: 'image_path',
      key: 'image_path',
      render: (path: string) => (
        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
          {path.length > 50 ? `${path.substring(0, 47)}...` : path}
        </code>
      )
    },
    {
      title: 'Port',
      dataIndex: 'port',
      key: 'port',
      render: (port: number) => (
        <Tag color="blue">{port || 8888}</Tag>
      )
    },
    {
      title: 'Working Dir',
      dataIndex: 'working_dir',
      key: 'working_dir',
      render: (workingDir: string) => (
        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
          {workingDir || '/cmbagent'}
        </code>
      )
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
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => {
        const tagArray = tags && Array.isArray(tags) ? tags : [];
        return (
          <Space wrap>
            {tagArray.slice(0, 3).map(tag => (
              <Tag key={tag}>{tag}</Tag>
            ))}
            {tagArray.length > 3 && <Tag>+{tagArray.length - 3} more</Tag>}
            {tagArray.length === 0 && <span className="text-gray-500">No tags</span>}
          </Space>
        );
      }
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: ApplicationImage) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Edit
          </Button>
          <Button
            type="link"
            onClick={() => handleToggleStatus(record)}
          >
            {record.is_active ? 'Deactivate' : 'Activate'}
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this application?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  if (!canSwitchToAdmin || currentRole !== 'admin') {
    return null; // Will redirect
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <Title level={2}>
          <AppstoreOutlined className="mr-2" />
          Application Management
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
        >
          Add Application
        </Button>
      </div>

      <Alert
        message="Application Management"
        description="Manage research environment applications and Docker images available to users."
        type="info"
        showIcon
        className="mb-6"
      />

      <Card title="Applications & Images" className="glass-card">
        <Table
          columns={columns}
          dataSource={applications}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingApp ? 'Edit Application' : 'Add New Application'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Application Name"
            rules={[{ required: true, message: 'Please enter application name' }]}
          >
            <Input placeholder="e.g., CMBAgent Research Environment" />
          </Form.Item>

          <Form.Item
            name="summary"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea rows={3} placeholder="Brief description of the application and its features" />
          </Form.Item>

          <Form.Item
            name="image_path"
            label="Docker Image Path"
            rules={[{ required: true, message: 'Please enter Docker image path' }]}
          >
            <Input placeholder="e.g., gcr.io/project/image:tag" />
          </Form.Item>

          <Form.Item
            name="port"
            label="Application Port"
            rules={[{ required: true, message: 'Please enter application port' }]}
            initialValue={8888}
          >
            <InputNumber
              min={1}
              max={65535}
              placeholder="8888"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="working_dir"
            label="Working Directory"
            rules={[{ required: true, message: 'Please enter working directory' }]}
            initialValue="/cmbagent"
            tooltip="The mount path and working directory for the container. Must match your Docker image's WORKDIR."
          >
            <Input placeholder="/cmbagent" />
          </Form.Item>

          <Form.Item
            name="category"
            label="Category"
            rules={[{ required: true, message: 'Please select category' }]}
          >
            <Select placeholder="Select category">
              <Option value="research">Research</Option>
              <Option value="machine-learning">Machine Learning</Option>
              <Option value="data-science">Data Science</Option>
              <Option value="development">Development</Option>
              <Option value="other">Other</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Application Image (optional)"
          >
            <div className="space-y-4">
              {/* Current/Preview Image */}
              {imagePreview && (
                <div className="flex items-center space-x-4">
                  <Image
                    src={imagePreview}
                    alt="Preview"
                    width={80}
                    height={80}
                    className="object-cover rounded-lg border"
                    fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                  />
                  <Button 
                    type="text" 
                    danger 
                    onClick={handleRemoveImage}
                    size="small"
                  >
                    Remove
                  </Button>
                </div>
              )}
              
              {/* Upload */}
              <Upload
                name="image"
                listType="picture-card"
                className="avatar-uploader"
                showUploadList={false}
                beforeUpload={() => false} // Prevent auto upload
                onChange={handleImageChange}
                accept="image/*"
              >
                {!imagePreview && (
                  <div className="text-center">
                    {uploading ? <LoadingOutlined /> : <UploadOutlined />}
                    <div style={{ marginTop: 8 }}>Upload Image</div>
                  </div>
                )}
              </Upload>
              
              <div className="text-sm text-gray-500">
                Upload an image file (PNG, JPG, etc.) up to 5MB. This will be displayed in the store.
              </div>
            </div>
          </Form.Item>

          <Form.Item
            name="tags"
            label="Tags (comma-separated)"
          >
            <Input placeholder="e.g., python, jupyter, research, gpu" />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={uploading}>
                {uploading ? 'Saving...' : (editingApp ? 'Update' : 'Add')} Application
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default function ApplicationManagementPage() {
  return (
    <MainLayout>
      <ApplicationManagementContent />
    </MainLayout>
  );
}