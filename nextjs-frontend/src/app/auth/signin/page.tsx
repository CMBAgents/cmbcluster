'use client';

import { useEffect } from 'react';
import { signIn, getSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, Button, Typography, Space, Image, Spin, Alert } from 'antd';
import { GoogleOutlined, LoadingOutlined } from '@ant-design/icons';
import { useState } from 'react';

const { Title, Text } = Typography;

export default function SignIn() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkSession = async () => {
      const session = await getSession();
      if (session) {
        const callbackUrl = searchParams.get('callbackUrl') || '/';
        router.push(callbackUrl);
      }
    };
    
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError('Authentication failed. Please try again.');
    }
    
    checkSession();
  }, [router, searchParams]);

  const handleGoogleSignIn = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const callbackUrl = searchParams.get('callbackUrl') || '/';
      
      await signIn('google', { 
        callbackUrl,
        redirect: true 
      });
    } catch (err) {
      setError('Authentication failed. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background-primary to-[#151A26] p-6">
      <Card className="w-full max-w-md shadow-large border-border-primary">
        <div className="text-center mb-8">
          {/* Logo Section */}
          <div className="flex justify-center items-center space-x-6 mb-8">
            <div className="cambridge-logo-container">
              <Image
                src="/logos/cambridge-logo.png"
                alt="Cambridge Logo"
                width={100}
                height={50}
                className="filter invert brightness-150 contrast-200 saturate-0 hue-rotate-180"
                preview={false}
              />
            </div>
            <Image
              src="/logos/infosys-logo.png"
              alt="Infosys Logo"
              width={100}
              height={50}
              preview={false}
            />
          </div>

          <div className="mb-6">
            <Title level={2} className="mb-2 text-text-primary">
              Welcome to CMBAgent Cloud
            </Title>
            <Text className="text-lg text-text-secondary">
              Your gateway to autonomous research
            </Text>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert
            message="Authentication Error"
            description={error}
            type="error"
            showIcon
            className="mb-4"
            onClose={() => setError(null)}
            closable
          />
        )}

        {/* Login Form */}
        <div className="space-y-6">
          <Button
            type="primary"
            size="large"
            icon={isLoading ? <LoadingOutlined /> : <GoogleOutlined />}
            block
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="h-14 text-base font-medium"
          >
            {isLoading ? 'Signing in...' : 'Sign in with Google'}
          </Button>

          <div className="text-center">
            <Text type="secondary" className="text-sm">
              Secure authentication powered by Google OAuth
            </Text>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-8 pt-6 border-t border-border-primary">
          <div className="text-center space-y-3">
            <Text type="secondary" className="text-sm block">
              🚀 Access your research environments securely
            </Text>
            <Text type="secondary" className="text-sm block">
              📊 Manage storage and monitor performance
            </Text>
            <Text type="secondary" className="text-sm block">
              👥 Collaborate with your research team
            </Text>
          </div>
        </div>

        {/* Development Mode */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 pt-4 border-t border-border-primary">
            <Text type="secondary" className="text-xs block text-center">
              Development Mode Active
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
}
