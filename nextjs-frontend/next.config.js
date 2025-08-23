/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    appDir: true,
  },
  transpilePackages: [
    'antd',
    '@ant-design/icons',
    '@ant-design/charts'
  ],
  env: {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL || 'http://localhost:8501',
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET || 'development-secret-key',
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
