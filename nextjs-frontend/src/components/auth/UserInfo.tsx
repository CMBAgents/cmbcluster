'use client';

import { useSession, signOut } from 'next-auth/react';
import { Card, Button, Avatar, Typography, Space, Divider } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Text, Title } = Typography;

export default function UserInfo() {
  const { data: session } = useSession();
  const router = useRouter();

  if (!session?.user) {
    return null;
  }

  const handleSignOut = () => {
    signOut({ callbackUrl: '/auth/signin' });
  };

  const handleSettings = () => {
    router.push('/settings');
  };

  return (
    <Card className="w-full">
      <div className="text-center mb-4">
        <Avatar 
          size={64} 
          src={session.user.image} 
          icon={<UserOutlined />}
          className="mb-3"
        />
        <Title level={5} className="mb-1 text-text-primary">
          {session.user.name}
        </Title>
        <Text type="secondary" className="text-text-muted">
          {session.user.email}
        </Text>
      </div>

      <Divider />

      <Space direction="vertical" className="w-full" size="small">
        <Button
          icon={<SettingOutlined />}
          block
          type="text"
          onClick={handleSettings}
          className="text-left justify-start"
        >
          Settings
        </Button>
        
        <Button
          icon={<LogoutOutlined />}
          block
          type="text"
          danger
          onClick={handleSignOut}
          className="text-left justify-start"
        >
          Sign Out
        </Button>
      </Space>
    </Card>
  );
}
