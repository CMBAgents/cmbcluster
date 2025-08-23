'use client';

import { ConfigProvider, theme } from 'antd';
import { Inter } from 'next/font/google';
import { SessionProvider } from 'next-auth/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

// Ant Design dark theme configuration
const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#4A9EFF',
    colorBgBase: '#0E1117',
    colorBgContainer: '#1A1F2E',
    colorBgLayout: '#0E1117',
    colorBorder: '#2D3748',
    colorText: '#FFFFFF',
    colorTextSecondary: '#E2E8F0',
    borderRadius: 8,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  components: {
    Layout: {
      bodyBg: 'transparent',
      headerBg: '#1A1F2E',
      siderBg: '#1A1F2E',
    },
    Card: {
      colorBgContainer: '#1A1F2E',
      colorBorderSecondary: '#2D3748',
    },
    Button: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Input: {
      colorBgContainer: '#252B3A',
      colorBorder: '#2D3748',
      borderRadius: 8,
      controlHeight: 40,
    },
    Select: {
      colorBgContainer: '#252B3A',
      colorBorder: '#2D3748',
      borderRadius: 8,
      controlHeight: 40,
    },
    Tabs: {
      cardBg: '#1A1F2E',
      borderRadius: 8,
    },
    Modal: {
      contentBg: '#1A1F2E',
      headerBg: '#1A1F2E',
    },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <html lang="en" data-theme="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="CMBAgent Cloud - Your gateway to autonomous research" />
        <title>CMBAgent Cloud</title>
      </head>
      <body className={inter.className}>
        <SessionProvider>
          <QueryClientProvider client={queryClient}>
            <ConfigProvider theme={darkTheme}>
              <div className="min-h-screen bg-gradient-to-br from-background-primary to-[#151A26]">
                {children}
              </div>
            </ConfigProvider>
          </QueryClientProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
