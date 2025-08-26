// Environment variable validation and configuration
export interface EnvironmentConfig {
  // API Configuration
  apiUrl: string;
  
  // NextAuth Configuration  
  nextAuthUrl: string;
  nextAuthSecret: string;
  
  // Google OAuth
  googleClientId: string;
  googleClientSecret: string;
  
  // App Configuration
  appTitle: string;
  appTagline: string;
  
  // Theme Configuration
  primaryColor: string;
  backgroundColor: string;
  secondaryColor: string;
  tertiaryColor: string;
  textPrimary: string;
  textSecondary: string;
  
  // Environment
  isDevelopment: boolean;
  isProduction: boolean;
  debug: boolean;
  
  // Domain configuration
  domain: string;
  apiDomain: string;
}

// Required server-side environment variables (removed NEXT_PUBLIC_API_URL)
const REQUIRED_ENV_VARS = [
  'NEXTAUTH_URL', 
  'NEXTAUTH_SECRET',
  'GOOGLE_CLIENT_ID',
  'GOOGLE_CLIENT_SECRET'
] as const;

// Optional environment variables with defaults
const OPTIONAL_ENV_VARS = {
  NEXT_PUBLIC_APP_TITLE: 'CMBAgent Cloud',
  NEXT_PUBLIC_APP_TAGLINE: 'Your gateway to autonomous research',
  NEXT_PUBLIC_PRIMARY_COLOR: '#4A9EFF',
  NEXT_PUBLIC_BACKGROUND_COLOR: '#0E1117',
  NEXT_PUBLIC_SECONDARY_COLOR: '#1A1F2E',
  NEXT_PUBLIC_TERTIARY_COLOR: '#252B3A',
  NEXT_PUBLIC_TEXT_PRIMARY: '#FFFFFF',
  NEXT_PUBLIC_TEXT_SECONDARY: '#E2E8F0',
  NEXT_PUBLIC_DOMAIN: '35.188.79.156.nip.io',
  NEXT_PUBLIC_API_DOMAIN: 'api.35.188.79.156.nip.io',
  DEBUG: 'false',
  DEV_MODE: 'false'
} as const;

class EnvironmentValidator {
  private static instance: EnvironmentValidator;
  private config: EnvironmentConfig | null = null;
  private runtimeConfig: any = null;
  
  private constructor() {}
  
  public static getInstance(): EnvironmentValidator {
    if (!EnvironmentValidator.instance) {
      EnvironmentValidator.instance = new EnvironmentValidator();
    }
    return EnvironmentValidator.instance;
  }
  
  private async fetchRuntimeConfig(): Promise<any> {
    if (this.runtimeConfig) {
      return this.runtimeConfig;
    }
    
    try {
      // Only fetch on client side
      if (typeof window !== 'undefined') {
        console.log('Fetching runtime config from /api/config...');
        const response = await fetch('/api/config');
        if (response.ok) {
          this.runtimeConfig = await response.json();
          console.log('Runtime config loaded:', this.runtimeConfig);
          return this.runtimeConfig;
        } else {
          console.warn('Failed to fetch runtime config, response not ok:', response.status, response.statusText);
        }
      } else {
        // Server side - use environment variables directly
        this.runtimeConfig = {
          apiUrl: process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
          domain: process.env.NEXT_PUBLIC_DOMAIN || 'localhost',
          apiDomain: process.env.NEXT_PUBLIC_API_DOMAIN || 'api.localhost',
          nextAuthUrl: process.env.NEXTAUTH_URL || 'http://localhost:3001'
        };
        console.log('Server-side config loaded:', this.runtimeConfig);
        return this.runtimeConfig;
      }
    } catch (error) {
      console.warn('Failed to fetch runtime config, using defaults:', error);
    }
    
    // Fallback to defaults
    this.runtimeConfig = {
      apiUrl: 'http://localhost:8000',
      domain: 'localhost',
      apiDomain: 'api.localhost',
      nextAuthUrl: 'http://localhost:3001'
    };
    
    console.warn('Using fallback config:', this.runtimeConfig);
    return this.runtimeConfig;
  }
  
  public validateEnvironment(): EnvironmentConfig {
    if (this.config) {
      return this.config;
    }
    
    // Skip validation during build if SKIP_ENV_VALIDATION is set
    const skipValidation = process.env.SKIP_ENV_VALIDATION === 'true' || process.env.NODE_ENV === 'production';
    
    // Check for missing required environment variables
    const missingVars: string[] = [];
    
    if (!skipValidation) {
      REQUIRED_ENV_VARS.forEach(varName => {
        if (!process.env[varName]) {
          missingVars.push(varName);
        }
      });
      
      if (missingVars.length > 0) {
        const errorMessage = `Missing required environment variables: ${missingVars.join(', ')}`;
        
        if (typeof window === 'undefined') {
          // Server-side: log error and throw
          console.error('❌ Environment Configuration Error:', errorMessage);
          throw new Error(errorMessage);
        } else {
          // Client-side: log error but don't throw to avoid breaking the app
          console.error('❌ Environment Configuration Error:', errorMessage);
        }
      }
    }
    
    // Build configuration object
    this.config = {
      // API Configuration - fallback for server-side, will be updated client-side
      apiUrl: process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      
      // NextAuth Configuration
      nextAuthUrl: process.env.NEXTAUTH_URL || 'https://35.188.79.156.nip.io',
      nextAuthSecret: process.env.NEXTAUTH_SECRET || 'fallback-secret-not-secure',
      
      // Google OAuth
      googleClientId: process.env.GOOGLE_CLIENT_ID || '',
      googleClientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
      
      // App Configuration  
      appTitle: process.env.NEXT_PUBLIC_APP_TITLE || OPTIONAL_ENV_VARS.NEXT_PUBLIC_APP_TITLE,
      appTagline: process.env.NEXT_PUBLIC_APP_TAGLINE || OPTIONAL_ENV_VARS.NEXT_PUBLIC_APP_TAGLINE,
      
      // Theme Configuration
      primaryColor: process.env.NEXT_PUBLIC_PRIMARY_COLOR || OPTIONAL_ENV_VARS.NEXT_PUBLIC_PRIMARY_COLOR,
      backgroundColor: process.env.NEXT_PUBLIC_BACKGROUND_COLOR || OPTIONAL_ENV_VARS.NEXT_PUBLIC_BACKGROUND_COLOR,
      secondaryColor: process.env.NEXT_PUBLIC_SECONDARY_COLOR || OPTIONAL_ENV_VARS.NEXT_PUBLIC_SECONDARY_COLOR,
      tertiaryColor: process.env.NEXT_PUBLIC_TERTIARY_COLOR || OPTIONAL_ENV_VARS.NEXT_PUBLIC_TERTIARY_COLOR,
      textPrimary: process.env.NEXT_PUBLIC_TEXT_PRIMARY || OPTIONAL_ENV_VARS.NEXT_PUBLIC_TEXT_PRIMARY,
      textSecondary: process.env.NEXT_PUBLIC_TEXT_SECONDARY || OPTIONAL_ENV_VARS.NEXT_PUBLIC_TEXT_SECONDARY,
      
      // Environment Detection
      isDevelopment: process.env.NODE_ENV === 'development',
      isProduction: process.env.NODE_ENV === 'production',
      debug: process.env.DEBUG === 'true' || process.env.DEV_MODE === 'true',
      
      // Domain Configuration
      domain: process.env.NEXT_PUBLIC_DOMAIN || OPTIONAL_ENV_VARS.NEXT_PUBLIC_DOMAIN,
      apiDomain: process.env.NEXT_PUBLIC_API_DOMAIN || OPTIONAL_ENV_VARS.NEXT_PUBLIC_API_DOMAIN
    };
    
    // Log configuration in development
    if (this.config.isDevelopment && this.config.debug) {
      console.log('🔧 Environment Configuration:', {
        apiUrl: this.config.apiUrl,
        nextAuthUrl: this.config.nextAuthUrl,
        domain: this.config.domain,
        apiDomain: this.config.apiDomain,
        isDevelopment: this.config.isDevelopment,
        debug: this.config.debug
      });
    }
    
    return this.config;
  }
  
  public getApiUrl(endpoint: string = ''): string {
    const config = this.validateEnvironment();
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${config.apiUrl.replace(/\/$/, '')}${cleanEndpoint}`;
  }
  
  public async getApiUrlAsync(endpoint: string = ''): Promise<string> {
    const runtimeConfig = await this.fetchRuntimeConfig();
    
    // Ensure we have a valid API URL
    const baseUrl = runtimeConfig.apiUrl || 'http://localhost:8000';
    const cleanBaseUrl = baseUrl.replace(/\/$/, '');
    
    if (!endpoint) {
      return cleanBaseUrl;
    }
    
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${cleanBaseUrl}${cleanEndpoint}`;
  }
  
  public getFrontendUrl(path: string = ''): string {
    const config = this.validateEnvironment();
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${config.nextAuthUrl.replace(/\/$/, '')}${cleanPath}`;
  }
  
  public isConfigured(): boolean {
    try {
      this.validateEnvironment();
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const envValidator = EnvironmentValidator.getInstance();

// Export convenience functions
export const getConfig = () => envValidator.validateEnvironment();
export const getApiUrl = (endpoint?: string) => envValidator.getApiUrl(endpoint);
export const getApiUrlAsync = (endpoint?: string) => envValidator.getApiUrlAsync(endpoint);
export const getFrontendUrl = (path?: string) => envValidator.getFrontendUrl(path);
export const isConfigured = () => envValidator.isConfigured();

export default envValidator;