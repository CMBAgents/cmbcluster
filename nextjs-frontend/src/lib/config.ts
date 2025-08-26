import { getConfig, getApiUrl, getFrontendUrl } from './env-validator';

// Environment-specific configuration using validated environment
const envConfig = getConfig();

export const config = {
  ...envConfig,
  
  // Port configuration
  port: process.env.NEXT_PUBLIC_PORT || process.env.PORT || '8501',
  
  // Helper functions
  getApiUrl,
  getFrontendUrl,
  
  // CSS custom properties for theming
  cssVars: {
    '--color-primary': envConfig.primaryColor,
    '--color-background': envConfig.backgroundColor,
    '--color-secondary': envConfig.secondaryColor,
    '--color-tertiary': envConfig.tertiaryColor,
    '--color-text-primary': envConfig.textPrimary,
    '--color-text-secondary': envConfig.textSecondary,
  }
};

export default config;