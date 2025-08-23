'use client';

import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  Button,
  Typography,
  Card,
  Row,
  Col,
  Alert,
  Progress,
  Space,
  message,
} from 'antd';
import {
  DatabaseOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface StorageCreationFormProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface StorageFormData {
  storageClass: 'STANDARD' | 'NEARLINE' | 'COLDLINE';
  customName?: string;
  autoBackup: boolean;
  enableVersioning: boolean;
  publicAccess: boolean;
}

export default function StorageCreationForm({ visible, onClose, onSuccess }: StorageCreationFormProps) {
  const [form] = Form.useForm();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<StorageFormData>({
    storageClass: 'STANDARD',
    autoBackup: false,
    enableVersioning: true,
    publicAccess: false,
  });
  const queryClient = useQueryClient();

  // Create storage mutation
  const createMutation = useMutation({
    mutationFn: (data: StorageFormData) =>
      apiClient.createStorageBucket(data.storageClass, data.customName),
    onSuccess: (response) => {
      if (response.status === 'created') {
        message.success('Workspace created successfully!');
        queryClient.invalidateQueries({ queryKey: ['user-storages'] });
        onSuccess();
        handleReset();
      } else {
        message.error(response.message || 'Failed to create workspace');
      }
    },
    onError: (error: any) => {
      message.error(error.message || 'Error creating workspace');
    },
  });

  const storageClassInfo = {
    STANDARD: {
      icon: '⚡',
      title: 'Standard',
      subtitle: 'Best for frequently accessed data',
      description: 'Higher cost, instant access. Perfect for active research data.',
      cost: '$0.020/GB',
      operations: '$0.004/1K ops',
      color: '#1890ff',
    },
    NEARLINE: {
      icon: '📊',
      title: 'Nearline',
      subtitle: 'Best for data accessed monthly',
      description: 'Lower cost, fast access. Good for periodic analysis.',
      cost: '$0.010/GB',
      operations: '$0.01/1K ops',
      color: '#52c41a',
    },
    COLDLINE: {
      icon: '❄️',
      title: 'Coldline',
      subtitle: 'Best for archival data',
      description: 'Lowest cost, slower access. Ideal for long-term storage.',
      cost: '$0.004/GB',
      operations: '$0.02/1K ops',
      color: '#722ed1',
    },
  };

  const handleNext = () => {
    form.validateFields().then(values => {
      setFormData({ ...formData, ...values });
      setStep(step + 1);
    });
  };

  const handlePrevious = () => {
    setStep(step - 1);
  };

  const handleSubmit = () => {
    createMutation.mutate(formData);
  };

  const handleReset = () => {
    setStep(0);
    form.resetFields();
    setFormData({
      storageClass: 'STANDARD',
      autoBackup: false,
      enableVersioning: true,
      publicAccess: false,
    });
  };

  const handleCancel = () => {
    handleReset();
    onClose();
  };

  return (
    <Modal
      title={
        <Space>
          <DatabaseOutlined className="text-blue-500" />
          Create New Workspace
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={700}
      destroyOnClose
    >
      <div className="space-y-6">
        {/* Progress Steps */}
        <div className="mb-6">
          <Progress
            percent={((step + 1) / 3) * 100}
            steps={3}
            size="small"
            strokeColor="#1890ff"
          />
          <div className="flex justify-between mt-2 text-sm text-gray-500">
            <span className={step >= 0 ? 'text-blue-500 font-medium' : ''}>Configuration</span>
            <span className={step >= 1 ? 'text-blue-500 font-medium' : ''}>Options</span>
            <span className={step >= 2 ? 'text-blue-500 font-medium' : ''}>Review</span>
          </div>
        </div>

        <Form form={form} layout="vertical" initialValues={formData}>
          {step === 0 && (
            <div className="space-y-6">
              <div>
                <Title level={4}>Storage Configuration</Title>
                <Paragraph type="secondary">
                  Choose the storage class based on your access frequency needs.
                </Paragraph>
              </div>

              {/* Storage Class Selection */}
              <Form.Item
                name="storageClass"
                label="Storage Class"
                rules={[{ required: true }]}
              >
                <div className="space-y-3">
                  {Object.entries(storageClassInfo).map(([key, info]) => (
                    <Card
                      key={key}
                      size="small"
                      className={`cursor-pointer transition-all ${
                        formData.storageClass === key
                          ? `border-2 shadow-md`
                          : 'border hover:border-blue-300'
                      }`}
                      style={{ 
                        borderColor: formData.storageClass === key ? info.color : undefined,
                        backgroundColor: formData.storageClass === key ? `${info.color}08` : undefined
                      }}
                      onClick={() => setFormData({ ...formData, storageClass: key as any })}
                    >
                      <Row align="middle" gutter={16}>
                        <Col>
                          <div className="text-2xl">{info.icon}</div>
                        </Col>
                        <Col flex="auto">
                          <div>
                            <Text strong style={{ color: info.color }}>
                              {info.title}
                            </Text>
                            <Text type="secondary" className="block text-sm">
                              {info.subtitle}
                            </Text>
                            <Text type="secondary" className="text-xs">
                              {info.description}
                            </Text>
                          </div>
                        </Col>
                        <Col>
                          <div className="text-right">
                            <Text className="text-sm font-medium">{info.cost}</Text>
                            <br />
                            <Text type="secondary" className="text-xs">{info.operations}</Text>
                          </div>
                        </Col>
                        <Col>
                          {formData.storageClass === key && (
                            <CheckCircleOutlined style={{ color: info.color, fontSize: 20 }} />
                          )}
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </div>
              </Form.Item>

              {/* Custom Name (Optional) */}
              <Form.Item
                name="customName"
                label="Custom Workspace Name (Optional)"
                help="Leave blank to generate a unique research-themed name automatically"
              >
                <Input 
                  placeholder="e.g., My Research Project Alpha"
                  maxLength={50}
                />
              </Form.Item>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-6">
              <div>
                <Title level={4}>Workspace Options</Title>
                <Paragraph type="secondary">
                  Configure additional features for your workspace.
                </Paragraph>
              </div>

              <Row gutter={16}>
                <Col span={12}>
                  <Card size="small" title="Data Protection">
                    <Form.Item
                      name="enableVersioning"
                      valuePropName="checked"
                    >
                      <Checkbox>
                        <Space direction="vertical" size={0}>
                          <Text strong>Enable file versioning</Text>
                          <Text type="secondary" className="text-xs">
                            Keep multiple versions of files for better data protection
                          </Text>
                        </Space>
                      </Checkbox>
                    </Form.Item>

                    <Form.Item
                      name="autoBackup"
                      valuePropName="checked"
                    >
                      <Checkbox>
                        <Space direction="vertical" size={0}>
                          <Text strong>Enable automatic backups</Text>
                          <Text type="secondary" className="text-xs">
                            Automatically create periodic backups of your workspace
                          </Text>
                        </Space>
                      </Checkbox>
                    </Form.Item>
                  </Card>
                </Col>
                
                <Col span={12}>
                  <Card size="small" title="Access Control">
                    <Form.Item
                      name="publicAccess"
                      valuePropName="checked"
                    >
                      <Checkbox>
                        <Space direction="vertical" size={0}>
                          <Text strong>Allow public read access</Text>
                          <Text type="secondary" className="text-xs">
                            ⚠️ Make workspace content publicly readable
                          </Text>
                        </Space>
                      </Checkbox>
                    </Form.Item>
                    
                    {formData.publicAccess && (
                      <Alert
                        message="Security Warning"
                        description="Public access will make your workspace content readable by anyone with the URL. Only enable this for non-sensitive data."
                        type="warning"
                        icon={<ExclamationCircleOutlined />}
                        showIcon
                        className="mt-3"
                      />
                    )}
                  </Card>
                </Col>
              </Row>

              {/* Cost Estimation */}
              <Card size="small" title="💰 Estimated Monthly Costs" className="bg-blue-50 border-blue-200">
                <Row gutter={16}>
                  <Col span={12}>
                    <Text strong>Storage Cost: </Text>
                    <Text>{storageClassInfo[formData.storageClass].cost}</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>Operations Cost: </Text>
                    <Text>{storageClassInfo[formData.storageClass].operations}</Text>
                  </Col>
                </Row>
                <Text type="secondary" className="text-xs block mt-2">
                  * Estimates based on typical research workloads. Actual costs may vary.
                </Text>
              </Card>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div>
                <Title level={4}>Review & Create</Title>
                <Paragraph type="secondary">
                  Please review your workspace configuration before creating.
                </Paragraph>
              </div>

              {/* Configuration Summary */}
              <Card>
                <Title level={5} className="mb-4">Configuration Summary</Title>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <div className="space-y-3">
                      <div>
                        <Text strong>Storage Class:</Text>
                        <br />
                        <Space>
                          <span>{storageClassInfo[formData.storageClass].icon}</span>
                          <Text>{storageClassInfo[formData.storageClass].title}</Text>
                        </Space>
                      </div>
                      
                      <div>
                        <Text strong>Workspace Name:</Text>
                        <br />
                        <Text>{formData.customName || 'Auto-generated research name'}</Text>
                      </div>
                    </div>
                  </Col>
                  
                  <Col span={12}>
                    <div className="space-y-3">
                      <div>
                        <Text strong>Features:</Text>
                        <br />
                        <Space direction="vertical" size={0}>
                          <Text className={formData.enableVersioning ? 'text-green-600' : 'text-gray-400'}>
                            {formData.enableVersioning ? '✅' : '❌'} File Versioning
                          </Text>
                          <Text className={formData.autoBackup ? 'text-green-600' : 'text-gray-400'}>
                            {formData.autoBackup ? '✅' : '❌'} Auto Backup
                          </Text>
                          <Text className={formData.publicAccess ? 'text-orange-600' : 'text-green-600'}>
                            {formData.publicAccess ? '⚠️ Public Access' : '✅ Private'}
                          </Text>
                        </Space>
                      </div>
                    </div>
                  </Col>
                </Row>
              </Card>

              {/* Final warnings */}
              {formData.publicAccess && (
                <Alert
                  message="Security Notice"
                  description="You have enabled public access. Your workspace content will be readable by anyone with the URL."
                  type="warning"
                  showIcon
                />
              )}
            </div>
          )}
        </Form>

        {/* Action Buttons */}
        <div className="flex justify-between pt-4 border-t">
          <Button onClick={step > 0 ? handlePrevious : handleCancel}>
            {step > 0 ? 'Previous' : 'Cancel'}
          </Button>
          
          <Space>
            {step < 2 ? (
              <Button type="primary" onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button
                type="primary"
                icon={<RocketOutlined />}
                onClick={handleSubmit}
                loading={createMutation.isPending}
              >
                Create Workspace
              </Button>
            )}
          </Space>
        </div>

        {/* Creation Progress */}
        {createMutation.isPending && (
          <Card size="small" className="bg-blue-50 border-blue-200">
            <div className="text-center py-4">
              <div className="text-2xl mb-2">🏗️</div>
              <Text strong>Creating your workspace...</Text>
              <br />
              <Text type="secondary" className="text-sm">
                This may take up to 30 seconds. Please don't close this window.
              </Text>
            </div>
          </Card>
        )}
      </div>
    </Modal>
  );
}
