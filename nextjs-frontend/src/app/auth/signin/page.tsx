'use client';

import { useEffect, Suspense, useState } from 'react';
import { signIn, getSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation'; // Removed Button
import { Typography, Image, Alert, Card } from 'antd';
import { GoogleOutlined, LoadingOutlined, SunOutlined, MoonOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useTheme } from '@/contexts/ThemeContext';

const { Text } = Typography;

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
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%)' }}>
      {/* Professional Background Pattern */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-20 w-64 h-64 rounded-full" style={{ 
          background: `radial-gradient(circle, ${theme === 'dark' ? 'rgba(14, 125, 184, 0.1)' : 'rgba(14, 125, 184, 0.05)'} 0%, transparent 70%)` 
        }}></div>
        <div className="absolute bottom-20 right-20 w-80 h-80 rounded-full" style={{ 
          background: `radial-gradient(circle, ${theme === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)'} 0%, transparent 70%)` 
        }}></div>
        <div className="absolute top-1/2 left-1/3 w-48 h-48 rounded-full" style={{ 
          background: `radial-gradient(circle, ${theme === 'dark' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(245, 158, 11, 0.05)'} 0%, transparent 70%)` 
        }}></div>
      </div>
      
      {/* Professional Theme Toggle */}
      <button 
        onClick={toggleTheme}
        className="fixed top-6 right-6 z-50 icon-container primary"
        style={{
          width: '48px',
          height: '48px',
          borderRadius: 'var(--radius-xl)',
          background: 'var(--glass-bg-primary)',
          backdropFilter: 'blur(var(--glass-blur-light))',
          border: '1px solid var(--glass-border)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        {theme === 'dark' ? (
          <SunOutlined style={{ fontSize: '18px', color: 'var(--interactive-primary)' }} />
        ) : (
          <MoonOutlined style={{ fontSize: '18px', color: 'var(--interactive-primary)' }} />
        )}
      </button>

      {/* Main Content Container */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center p-6">
        {/* Elegant Header */}
        <div className="w-full max-w-6xl text-center mb-8 fade-in">
          {/* Clean Logo Partnership */}
          <div className="flex items-center justify-center gap-20 mb-6">
            <div className="cambridge-logo-container">
              <Image
                src="/logos/cambridge-logo.png"
                alt="University of Cambridge"
                width={170}
                height={90}
                preview={false}
                style={{
                  transition: 'all 0.4s ease',
                  objectFit: 'contain'
                }}
              />
            </div>
            <div className="flex flex-col items-center">
              <div 
                className="w-20 h-px opacity-30 mb-3"
                style={{ background: `linear-gradient(90deg, transparent, var(--text-muted), transparent)` }}
              ></div>
              <div className="w-3 h-3 rounded-full opacity-40" style={{ background: 'var(--interactive-primary)' }}></div>
              <div 
                className="w-20 h-px opacity-30 mt-3"
                style={{ background: `linear-gradient(90deg, transparent, var(--text-muted), transparent)` }}
              ></div>
            </div>
            <div>
              <Image
                src="/logos/infosys-logo.png"
                alt="Infosys Limited"
                width={160}
                height={80}
                preview={false}
                style={{
                  transition: 'all 0.4s ease',
                  objectFit: 'contain'
                }}
              />
            </div>
          </div>
          
          {/* Sophisticated Branding */}
          <div>
            <div className="flex items-center justify-center gap-4 mb-4">
              <Image
                src="/logos/cmbagent-logo.png"
                alt="CMBAgent"
                width={48}
                height={48}
                preview={false}
                style={{
                  transition: 'all 0.4s ease',
                  objectFit: 'contain',
                  filter: theme === 'dark' ? 'brightness(1.1)' : 'brightness(0.9)'
                }}
              />
              <h1 className="text-5xl font-light" style={{ 
                color: 'var(--text-primary)',
                fontWeight: '300',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
                margin: 0
              }}>
                CMBAgent 
                <span style={{ 
                  fontWeight: '600',
                  background: `linear-gradient(135deg, var(--interactive-primary), var(--primary-300))`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  Cloud
                </span>
              </h1>
            </div>
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="h-px w-12 opacity-30" style={{ background: 'var(--text-muted)' }}></div>
              <Text style={{ 
                color: 'var(--text-muted)', 
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--font-medium)',
                textTransform: 'uppercase',
                letterSpacing: '0.15em'
              }}>
                Autonomous Agentic Research Environment
              </Text>
              <div className="h-px w-12 opacity-30" style={{ background: 'var(--text-muted)' }}></div>
            </div>
          </div>
        </div>

        {/* Clean Authentication Container */}
        <div className="w-full max-w-md slide-up" style={{ animationDelay: '0.3s' }}>

          {/* Clean Authentication Card */}
          <Card 
            className="glass-card"
            style={{
              background: 'var(--glass-bg-primary)',
              backdropFilter: 'blur(var(--glass-blur))',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--radius-2xl)',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden'
            }}
            styles={{ body: { padding: '48px 40px' } }}
          >
            {/* Minimal Header */}
            <div className="text-center mb-10">
              <Text style={{ 
                color: 'var(--text-primary)', 
                fontSize: 'var(--text-lg)',
                lineHeight: 1.5,
                fontWeight: 'var(--font-medium)'
              }}>
                Access your research environment
              </Text>
            </div>

            {/* Clean Error Alert */}
            {error && (
              <Alert
                message={error}
                type="error"
                showIcon
                className="mb-8 fade-in"
                onClose={() => setError(null)}
                closable
                style={{
                  background: theme === 'dark' ? 'rgba(239, 68, 68, 0.05)' : 'var(--error-50)',
                  border: `1px solid ${theme === 'dark' ? 'rgba(239, 68, 68, 0.15)' : 'var(--error-200)'}`,
                  borderRadius: 'var(--radius-lg)',
                  color: theme === 'dark' ? 'var(--error-300)' : 'var(--error-700)'
                }}
              />
            )}

            {/* Elegant Sign-In Button */}
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="btn-signin-google"
            >
              <span className="flex items-center justify-center w-full h-full gap-3">
                {isLoading ? <LoadingOutlined /> : <GoogleOutlined />}
                <span>
                  {isLoading ? 'Authenticating...' : 'Continue with Google'}
                </span>
              </span>
            </button>

            {/* Minimal Security Note */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-4">
                <SafetyCertificateOutlined style={{ 
                  fontSize: '14px', 
                  color: 'var(--success-400)' 
                }} />
                <Text style={{ 
                  color: 'var(--text-muted)', 
                  fontSize: 'var(--text-sm)'
                }}>
                  Enterprise-grade security
                </Text>
              </div>
              
            </div>
          </Card>
        </div>

        {/* Clean Footer */}
        <div className="text-center mt-6 fade-in" style={{ animationDelay: '0.8s' }}>
          <Text style={{ 
            color: 'var(--text-muted)', 
            fontSize: 'var(--text-xs)',
            lineHeight: 1.6
          }}>
            By continuing, you agree to our{' '}
            <span style={{ 
              color: 'var(--interactive-primary)', 
              cursor: 'pointer',
              textDecoration: 'underline',
              textUnderlineOffset: '2px'
            }}>
              Terms of Service
            </span>
            {' '}and{' '}
            <span style={{ 
              color: 'var(--interactive-primary)', 
              cursor: 'pointer',
              textDecoration: 'underline',
              textUnderlineOffset: '2px'
            }}>
              Privacy Policy
            </span>
          </Text>
        </div>
      </div>
    </div>
  );
}

export default function SignIn() {
  return (
    <Suspense fallback={
      <div 
        className="min-h-screen flex items-center justify-center loading-page" 
        style={{ 
          background: 'var(--background-primary)',
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 9999
        }}
      >
        <div className="text-center loading-container">
          <div className="loading-logo mb-4">
            <img
              src="/logos/cambridge-logo.png"
              alt="Cambridge Logo"
              className="w-16 h-16"
              style={{
                filter: 'var(--logo-filter)',
                transition: 'all 0.3s ease'
              }}
            />
          </div>
          <div className="spinner mx-auto mb-4" style={{ width: '32px', height: '32px' }}></div>
          <h3 className="text-lg font-semibold mb-2 loading-text">
            Initializing Platform
          </h3>
          <p className="text-sm loading-text" style={{ opacity: 0.7 }}>
            Setting up your secure environment...
          </p>
        </div>
      </div>
    }>
      <SignInContent />
    </Suspense>
  );
}
