/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // Skip TypeScript checks during build for faster deployment
    ignoreBuildErrors: true,
  },
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Transpile packages for better compatibility
  transpilePackages: [
    'antd',
    '@ant-design/icons',
    '@ant-design/charts'
  ],
  
  // Environment variables - remove hardcoded fallbacks for production
  env: {
    // NextAuth will automatically read NEXTAUTH_URL and NEXTAUTH_SECRET from env
    // Don't set fallbacks that would override Kubernetes environment variables
  },
  
  // API rewrites for backend communication
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: `${process.env.API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
  
  // Production optimizations
  compress: true,
  poweredByHeader: false,
  generateEtags: true,
  
  // Image optimization for production
  images: {
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
  },
  
  // Other configurations
  
  // Experimental features for performance
  experimental: {
    optimizePackageImports: ['antd', '@ant-design/icons'],
    optimizeCss: true,
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  
  // Performance optimizations
  swcMinify: true,
  modularizeImports: {
    '@ant-design/icons': {
      transform: '@ant-design/icons/lib/icons/{{member}}',
    },
    'antd': {
      transform: 'antd/lib/{{member}}',
      style: false,
    },
  },
  
  // Bundle analyzer (only in development)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
      if (!isServer) {
        const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
        config.plugins.push(
          new BundleAnalyzerPlugin({
            analyzerMode: 'static',
            openAnalyzer: false,
          })
        );
      }
      return config;
    },
  }),
};

module.exports = nextConfig;
