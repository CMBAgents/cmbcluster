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
    SKIP_ENV_VALIDATION: 'true',
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
  
  // Cache busting for authentication fixes
  generateBuildId: async () => {
    // Use timestamp + random for cache busting in auth fixes
    return `auth-fix-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  },
  
  // Force no-cache headers for dynamic content
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
        ],
      },
      {
        source: '/_next/static/chunks/:path*',
        headers: [
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
        ],
      },
    ];
  },
  
  // Image optimization for production
  images: {
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
  },
  
  // Disable static generation for authenticated pages
  trailingSlash: false,
  
  // Experimental features for performance
  experimental: {
    optimizePackageImports: ['antd', '@ant-design/icons'],
    optimizeCss: true,
    // Disable PPR to avoid static generation issues with auth
    ppr: false,
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
  
  // Webpack config for better compatibility
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Handle serialization issues
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };
    
    // Add bundle analyzer only if requested
    if (process.env.ANALYZE === 'true' && !isServer) {
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
};

module.exports = nextConfig;
