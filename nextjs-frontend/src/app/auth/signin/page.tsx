'use client';

import { useEffect, Suspense, useState } from 'react';
import { signIn, getSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button, Typography, Image, Spin, Alert } from 'antd';
import { GoogleOutlined, LoadingOutlined, SunOutlined, MoonOutlined, SafetyOutlined, BarChartOutlined, TeamOutlined } from '@ant-design/icons';
import { useTheme } from '@/contexts/ThemeContext';

const { Title, Text } = Typography;

function SignInContent() {
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

  const { theme, toggleTheme } = useTheme();

  return (
    <div className="signin-background">
      {/* Theme Toggle */}
      <div className="theme-toggle" onClick={toggleTheme}>
        {theme === 'dark' ? (
          <SunOutlined style={{ fontSize: '20px', color: 'var(--text-primary)' }} />
        ) : (
          <MoonOutlined style={{ fontSize: '20px', color: 'var(--text-primary)' }} />
        )}
      </div>

      <div className="signin-container">
        {/* Logo Section */}
        <div className="logo-container">
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

        {/* Main Card */}
        <div className="glass-card p-8">
          <div className="text-center mb-8">
            <Title level={1} className="mb-4" style={{ 
              color: 'var(--text-primary)', 
              fontSize: '32px',
              fontWeight: '700',
              background: 'linear-gradient(135deg, var(--text-primary) 0%, var(--border-accent) 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              CMBAgent Cloud
            </Title>
            <Text className="text-lg" style={{ color: 'var(--text-secondary)' }}>
              Enterprise research platform for autonomous discovery
            </Text>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert
              message="Authentication Failed"
              description={error}
              type="error"
              showIcon
              className="mb-6"
              onClose={() => setError(null)}
              closable
              style={{
                background: 'rgba(245, 101, 101, 0.1)',
                border: '1px solid rgba(245, 101, 101, 0.3)',
                borderRadius: '12px'
              }}
            />
          )}

          {/* Login Button */}
          <div className="mb-8">
            <Button
              size="large"
              icon={isLoading ? <LoadingOutlined /> : <GoogleOutlined />}
              block
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="glass-button h-14 text-base font-semibold"
              style={{
                background: 'rgba(74, 158, 255, 0.1)',
                border: '1px solid rgba(74, 158, 255, 0.3)',
                color: 'var(--text-primary)',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              {isLoading ? 'Authenticating...' : 'Continue with Google'}
            </Button>
            <div className="text-center mt-4">
              <Text style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                Secure OAuth 2.0 authentication
              </Text>
            </div>
          </div>

          {/* Features Section */}
          <div className="feature-grid">
            <div className="feature-item">
              <div className="icon-shield">
                <SafetyOutlined style={{ fontSize: '24px', color: 'var(--border-accent)' }} />
              </div>
              <Text style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>
                Secure Access
              </Text>
            </div>
            <div className="feature-item">
              <div className="icon-analytics">
                <BarChartOutlined style={{ fontSize: '24px', color: '#48BB78' }} />
              </div>
              <Text style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>
                Analytics
              </Text>
            </div>
            <div className="feature-item">
              <div className="icon-team">
                <TeamOutlined style={{ fontSize: '24px', color: '#ED8936' }} />
              </div>
              <Text style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>
                Collaboration
              </Text>
            </div>
          </div>

          {/* Development Mode */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-6 pt-4 text-center" style={{ borderTop: '1px solid var(--border-primary)' }}>
              <Text style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                Development Environment
              </Text>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SignIn() {
  return (
    <Suspense fallback={
      <div className="signin-background">
        <div className="signin-container">
          <div className="glass-card p-8">
            <div className="text-center py-12">
              <Spin size="large" style={{ color: 'var(--border-accent)' }} />
              <div className="mt-6">
                <Text style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>Initializing...</Text>
              </div>
            </div>
          </div>
        </div>
      </div>
    }>
      <SignInContent />
    </Suspense>
  );
}
