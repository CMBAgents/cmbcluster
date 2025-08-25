'use client';

import { useSearchParams } from 'next/navigation';
import { Button, Typography, Alert, Card } from 'antd';
import { ExclamationCircleOutlined, HomeOutlined, ReloadOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { Suspense } from 'react';

const { Title, Text } = Typography;

function AuthErrorContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const error = searchParams.get('error');

  const getErrorDetails = (errorCode: string | null) => {
    switch (errorCode) {
      case 'Configuration':
        return {
          title: 'Configuration Error',
          description: 'There is a problem with the authentication configuration. Please contact the administrator.',
          suggestion: 'This usually indicates a server-side configuration issue.',
        };
      case 'AccessDenied':
        return {
          title: 'Access Denied',
          description: 'You do not have permission to access this application.',
          suggestion: 'Please ensure you are using an authorized email address or contact your administrator.',
        };
      case 'Verification':
        return {
          title: 'Email Verification Required',
          description: 'Your email address has not been verified with Google.',
          suggestion: 'Please verify your email address in your Google account settings and try again.',
        };
      case 'TokenExchange':
        return {
          title: 'Authentication Failed',
          description: 'There was a problem exchanging your authentication token.',
          suggestion: 'This is usually a temporary issue. Please try signing in again.',
        };
      case 'RateLimit':
        return {
          title: 'Too Many Attempts',
          description: 'You have made too many authentication attempts.',
          suggestion: 'Please wait a while before trying to sign in again.',
        };
      case 'Callback':
        return {
          title: 'Authentication Callback Error',
          description: 'There was an error processing your authentication response.',
          suggestion: 'Please try signing in again. If the problem persists, clear your browser cookies.',
        };
      default:
        return {
          title: 'Authentication Error',
          description: 'An unexpected error occurred during authentication.',
          suggestion: 'Please try signing in again. If the problem persists, contact support.',
        };
    }
  };

  const errorDetails = getErrorDetails(error);

  const handleRetry = () => {
    router.push('/auth/signin');
  };

  const handleHome = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background-primary p-4">
      <Card className="w-full max-w-md">
        <div className="text-center">
          <ExclamationCircleOutlined 
            style={{ 
              fontSize: '64px', 
              color: '#ff4d4f',
              marginBottom: '24px' 
            }} 
          />
          
          <Title level={2} className="mb-4" style={{ color: 'var(--text-primary)' }}>
            {errorDetails.title}
          </Title>
          
          <Alert
            message={errorDetails.description}
            type="error"
            showIcon={false}
            className="mb-4"
            style={{
              background: 'rgba(245, 101, 101, 0.1)',
              border: '1px solid rgba(245, 101, 101, 0.3)',
            }}
          />
          
          <Text 
            className="block mb-6" 
            style={{ color: 'var(--text-secondary)', fontSize: '14px' }}
          >
            {errorDetails.suggestion}
          </Text>
          
          <div className="space-y-3">
            <Button
              type="primary"
              size="large"
              icon={<ReloadOutlined />}
              onClick={handleRetry}
              className="w-full"
              style={{
                background: 'var(--border-accent)',
                borderColor: 'var(--border-accent)',
                height: '48px',
                fontSize: '16px'
              }}
            >
              Try Again
            </Button>
            
            <Button
              size="large"
              icon={<HomeOutlined />}
              onClick={handleHome}
              className="w-full"
              style={{
                height: '48px',
                fontSize: '16px',
                color: 'var(--text-primary)',
                borderColor: 'var(--border-primary)'
              }}
            >
              Go to Home
            </Button>
          </div>
          
          {/* Additional help information */}
          <div className="mt-8 pt-6 border-t border-border-primary">
            <Text style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              Error Code: {error || 'UNKNOWN'}
            </Text>
            <br />
            <Text style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              If this problem persists, please contact support with the error code above.
            </Text>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default function AuthErrorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background-primary">
        <Card className="w-full max-w-md p-8">
          <div className="text-center">
            <Title level={2} style={{ color: 'var(--text-primary)' }}>Loading...</Title>
          </div>
        </Card>
      </div>
    }>
      <AuthErrorContent />
    </Suspense>
  );
}
