'use client';

import { Card, Typography } from 'antd';
import MainLayout from '@/components/layout/MainLayout';

// Force dynamic rendering
export const dynamic = 'force-dynamic';

const { Title, Text } = Typography;

export default function DesignSystemPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Title level={2} className="text-text-primary mb-2">
            Design System
          </Title>
          <Text className="text-text-secondary">
            This page is under development. Design system components will be added here.
          </Text>
        </div>
        
        <Card className="bg-background-secondary border-border-primary">
          <div className="text-center py-8">
            <Text className="text-text-secondary">
              Design system documentation coming soon...
            </Text>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
}