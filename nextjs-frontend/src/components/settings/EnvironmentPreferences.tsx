'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Slider, 
  Select, 
  Switch, 
  Button, 
  Typography, 
  Row, 
  Col, 
  message,
  Divider 
} from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { UserSettings } from '@/types';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

export default function EnvironmentPreferences() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState<UserSettings>({
    default_cpu: 2.0,
    default_memory: 4,
    default_storage_class: 'standard',
    auto_cleanup_hours: 4,
    auto_save: true,
    enable_monitoring: true,
    email_notifications: false,
    auto_backup: false,
  });

  // Load preferences from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('env_preferences');
    if (saved) {
      try {
        const parsedPrefs = JSON.parse(saved);
        setPreferences(parsedPrefs);
        form.setFieldsValue(parsedPrefs);
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    }
  }, [form]);

  const handleSave = async (values: UserSettings) => {
    setLoading(true);
    try {
      const updatedPrefs = {
        ...values,
        last_updated: new Date().toISOString(),
      };
      
      // Save to localStorage for persistence
      localStorage.setItem('env_preferences', JSON.stringify(updatedPrefs));
      setPreferences(updatedPrefs);
      
      message.success('Environment preferences saved successfully!');
    } catch (error) {
      message.error('Failed to save preferences');
      console.error('Save error:', error);
    } finally {
      setLoading(false);
    }
  };

  const sectionStyle: React.CSSProperties = {
    background: 'rgba(26, 31, 46, 0.5)',
    borderRadius: '12px',
    padding: '24px',
    margin: '16px 0',
    borderLeft: '4px solid #4A9EFF',
  };

  const previewStyle: React.CSSProperties = {
    backgroundColor: '#1A1F2E',
    border: '1px solid #2D3748',
    borderRadius: '8px',
    padding: '16px',
    fontFamily: 'monospace',
    fontSize: '14px',
    color: '#E2E8F0',
    whiteSpace: 'pre-line',
  };

  return (
    <div className="space-y-6">
      <div style={sectionStyle}>
        <Title level={3} className="text-white mb-4">
          Default Environment Configuration
        </Title>
        <Paragraph className="text-text-secondary mb-6">
          Set your preferred default settings for new research environments. These can be overridden when creating individual environments.
        </Paragraph>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={preferences}
          className="space-y-6"
        >
          {/* Resource Defaults */}
          <Card 
            title="Default Resource Allocation"
            className="bg-background-tertiary border-border-primary"
            headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="default_cpu"
                  label={<span className="text-white">CPU Cores</span>}
                  help="Default number of CPU cores for new environments"
                >
                  <Slider
                    min={0.5}
                    max={8}
                    step={0.5}
                    marks={{
                      0.5: '0.5',
                      2: '2',
                      4: '4',
                      6: '6',
                      8: '8'
                    }}
                    tooltip={{ formatter: (value) => `${value} cores` }}
                  />
                </Form.Item>

                <Form.Item
                  name="default_memory"
                  label={<span className="text-white">Memory (GB)</span>}
                  help="Default memory allocation in gigabytes"
                >
                  <Slider
                    min={1}
                    max={32}
                    step={1}
                    marks={{
                      1: '1GB',
                      8: '8GB',
                      16: '16GB',
                      24: '24GB',
                      32: '32GB'
                    }}
                    tooltip={{ formatter: (value) => `${value} GB` }}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="default_storage_class"
                  label={<span className="text-white">Default Storage Class</span>}
                  help="Default storage class for new workspaces"
                >
                  <Select className="w-full">
                    <Option value="standard">Standard - High performance, higher cost</Option>
                    <Option value="nearline">Nearline - Moderate performance, lower cost</Option>
                    <Option value="coldline">Coldline - Long-term storage, lowest cost</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="auto_cleanup_hours"
                  label={<span className="text-white">Auto-cleanup (hours)</span>}
                  help="Automatically stop idle environments after this many hours"
                >
                  <Slider
                    min={1}
                    max={168}
                    step={1}
                    marks={{
                      1: '1h',
                      24: '1d',
                      72: '3d',
                      168: '1w'
                    }}
                    tooltip={{ formatter: (value) => `${value} hours` }}
                  />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Divider className="border-border-primary" />

          {/* Advanced Preferences */}
          <Card 
            title="Advanced Preferences"
            className="bg-background-tertiary border-border-primary"
            headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="auto_save"
                  valuePropName="checked"
                  className="mb-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <Text className="text-white font-medium">Auto-save workspace changes</Text>
                      <div className="text-text-secondary text-sm">
                        Automatically save workspace changes periodically
                      </div>
                    </div>
                    <Switch />
                  </div>
                </Form.Item>

                <Form.Item
                  name="enable_monitoring"
                  valuePropName="checked"
                  className="mb-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <Text className="text-white font-medium">Enable environment monitoring</Text>
                      <div className="text-text-secondary text-sm">
                        Monitor resource usage and performance
                      </div>
                    </div>
                    <Switch />
                  </div>
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="email_notifications"
                  valuePropName="checked"
                  className="mb-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <Text className="text-white font-medium">Email notifications</Text>
                      <div className="text-text-secondary text-sm">
                        Receive email notifications for environment events
                      </div>
                    </div>
                    <Switch />
                  </div>
                </Form.Item>

                <Form.Item
                  name="auto_backup"
                  valuePropName="checked"
                  className="mb-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <Text className="text-white font-medium">Auto-backup workspaces</Text>
                      <div className="text-text-secondary text-sm">
                        Automatically backup workspace data
                      </div>
                    </div>
                    <Switch />
                  </div>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Divider className="border-border-primary" />

          {/* Configuration Preview */}
          <Card 
            title="Configuration Preview"
            className="bg-background-tertiary border-border-primary"
            headStyle={{ color: '#FFFFFF', borderBottom: '1px solid #2D3748' }}
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} md={12}>
                <Text className="text-white font-medium block mb-2">Resource Defaults:</Text>
                <div style={previewStyle}>
                  {`├── CPU: ${form.getFieldValue('default_cpu') || preferences.default_cpu} cores
├── Memory: ${form.getFieldValue('default_memory') || preferences.default_memory} GB
└── Storage: ${form.getFieldValue('default_storage_class') || preferences.default_storage_class}`}
                </div>
              </Col>

              <Col xs={24} md={12}>
                <Text className="text-white font-medium block mb-2">Automation Settings:</Text>
                <div style={previewStyle}>
                  {`├── Auto-cleanup: ${form.getFieldValue('auto_cleanup_hours') || preferences.auto_cleanup_hours}h
├── Auto-save: ${form.getFieldValue('auto_save') !== undefined ? (form.getFieldValue('auto_save') ? '✓' : '✗') : (preferences.auto_save ? '✓' : '✗')}
├── Monitoring: ${form.getFieldValue('enable_monitoring') !== undefined ? (form.getFieldValue('enable_monitoring') ? '✓' : '✗') : (preferences.enable_monitoring ? '✓' : '✗')}
├── Notifications: ${form.getFieldValue('email_notifications') !== undefined ? (form.getFieldValue('email_notifications') ? '✓' : '✗') : (preferences.email_notifications ? '✓' : '✗')}
└── Auto-backup: ${form.getFieldValue('auto_backup') !== undefined ? (form.getFieldValue('auto_backup') ? '✓' : '✗') : (preferences.auto_backup ? '✓' : '✗')}`}
                </div>
              </Col>
            </Row>
          </Card>

          {/* Save Button */}
          <div className="flex justify-center">
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
              size="large"
              className="px-12 h-12"
            >
              Save Environment Preferences
            </Button>
          </div>
        </Form>
      </div>

      {preferences.last_updated && (
        <div className="text-center text-text-secondary text-sm">
          Last updated: {new Date(preferences.last_updated).toLocaleString()}
        </div>
      )}
    </div>
  );
}
