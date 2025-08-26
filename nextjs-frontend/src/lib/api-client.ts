import axios, { AxiosInstance, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getSession, signOut } from 'next-auth/react';
import type { 
  Environment, 
  StorageItem, 
  UserFile, 
  ApiResponse, 
  EnvironmentConfig,
  UserEnvVar 
} from '@/types';

// Production configuration with enhanced security
const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
};

class CMBClusterAPIClient {
  private api: AxiosInstance;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest', // CSRF protection
      },
      validateStatus: (status) => status < 500, // Don't throw on 4xx errors
      withCredentials: true, // Include cookies for CSRF protection
    });

    // Request interceptor to add auth token and security headers
    this.api.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        try {
          // Get backend token (either from session or throw error)
          const backendToken = await this.getBackendToken();
          
          if (backendToken) {
            if (!config.headers) {
              config.headers = {} as any;
            }
            config.headers.Authorization = `Bearer ${backendToken}`;
          }
        } catch (error) {
          // If token retrieval fails, reject the request with helpful error
          return Promise.reject({
            isAuthError: true,
            message: error instanceof Error ? error.message : 'Authentication failed',
            config,
          });
        }
        
        // Add security headers
        config.headers = config.headers || {};
        config.headers['X-Client-Version'] = '1.0.0';
        config.headers['X-Client-Type'] = 'nextjs-frontend';
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for enhanced error handling and token refresh
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        // Check for security warnings in response headers
        const securityWarning = response.headers['x-security-warning'];
        if (securityWarning) {
          console.warn('Security warning from API:', securityWarning);
        }
        
        return response;
      },
      async (error: AxiosError | any) => {
        // Handle authentication errors from request interceptor
        if (error.isAuthError) {
          console.error('Authentication error:', error.message);
          return Promise.reject(new Error(error.message));
        }

        const originalRequest = error.config;
        
        if (error.response?.status === 401) {
          // Authentication failed - sign out and redirect to login
          console.log('Authentication failed (401), signing out');
          signOut({ callbackUrl: '/auth/signin' });
          
        } else if (error.response?.status === 403) {
          console.error('Access denied. Insufficient permissions.');
          
        } else if (error.response?.status === 429) {
          console.error('Rate limit exceeded. Please try again later.');
          
        } else if (error.response && error.response.status >= 500) {
          console.error('Server error:', error.response.data);
          
        } else if (error.code === 'ECONNABORTED') {
          console.error('Request timeout');
          
        } else if (error.code === 'ERR_NETWORK') {
          console.error('Network error - please check your connection');
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get backend JWT token from NextAuth session
   */
  private async getBackendToken(): Promise<string | null> {
    try {
      console.log('=== API CLIENT TOKEN DEBUG ===');
      const session = await getSession();
      
      // If no session, can't get token
      if (!session) {
        console.log('❌ No session found - user not logged in');
        return null;
      }
      
      console.log('✅ Session found for user:', session.user?.email);
      console.log('Session has accessToken:', !!session.accessToken);
      
      // If session has backend token, use it
      if (session.accessToken) {
        console.log('✅ Using backend token from session');
        console.log('==============================');
        return session.accessToken;
      }
      
      // If session exists but no backend token, the initial token exchange probably failed
      console.error('❌ Authentication incomplete: User is logged in but backend token exchange failed');
      console.error('This usually means there was an issue connecting to the backend during login');
      console.error('Session data:', { 
        hasUser: !!session.user, 
        userEmail: session.user?.email,
        hasAccessToken: !!session.accessToken 
      });
      console.error('==============================');
      throw new Error('Authentication incomplete - please try logging out and logging in again');
    } catch (error) {
      console.error('Error getting backend token:', error);
      throw error;
    }
  }

  /**
   * Get headers for API requests
   */
  private async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Client-Version': '1.0.0',
      'X-Client-Type': 'nextjs-frontend',
    };

    const backendToken = await this.getBackendToken();
    if (backendToken) {
      headers.Authorization = `Bearer ${backendToken}`;
    }

    return headers;
  }

  private async refreshToken(): Promise<string | null> {
    if (this.isRefreshing) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();

    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string | null> {
    try {
      // In NextAuth, token refresh happens automatically
      // We just need to get a fresh session
      const session = await getSession();
      return session?.accessToken || null;
    } catch (error) {
      console.error('Token refresh request failed:', error);
      return null;
    }
  }

  private async handleResponse<T>(response: AxiosResponse<T>): Promise<T> {
    return response.data;
  }

  private handleError(error: any): ApiResponse {
    if (error.response?.data) {
      return {
        status: 'error',
        message: error.response.data.detail || error.response.data.message || 'An error occurred',
      };
    }
    if (error.code === 'ECONNABORTED') {
      return {
        status: 'error',
        message: 'Request timeout - please try again',
      };
    }
    if (error.code === 'ERR_NETWORK') {
      return {
        status: 'error',
        message: 'Network error - please check your connection',
      };
    }
    if (error.message) {
      return {
        status: 'error',
        message: error.message,
      };
    }
    return {
      status: 'error',
      message: 'An unexpected error occurred',
    };
  }

  // Health check with enhanced error handling
  async healthCheck(): Promise<ApiResponse> {
    try {
      const response = await this.api.get('/health');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Environment management
  async createEnvironment(config?: EnvironmentConfig): Promise<ApiResponse<Environment>> {
    try {
      const data = {
        cpu_limit: 2.0,
        memory_limit: "4Gi",
        storage_size: "20Gi",
        ...config
      };

      const response = await this.api.post('/environments', data);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async listEnvironments(): Promise<ApiResponse<Environment[]>> {
    try {
      const response = await this.api.get('/environments/list');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getEnvironmentStatus(): Promise<ApiResponse<Environment[]>> {
    try {
      const response = await this.api.get('/environments');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getEnvironmentById(envId: string): Promise<ApiResponse<Environment>> {
    try {
      // First try to get from list
      const listResponse = await this.listEnvironments();
      if (listResponse.environments) {
        const env = listResponse.environments.find(
          e => e.id === envId || e.env_id === envId
        );
        if (env) {
          return {
            status: 'success',
            data: env,
            environment: env
          };
        }
      }
      return {
        status: 'error',
        message: 'Environment not found'
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async restartEnvironment(envId?: string, config?: EnvironmentConfig): Promise<ApiResponse> {
    try {
      // Stop environment first
      const deleteResponse = await this.deleteEnvironment(envId);
      if (deleteResponse.status !== 'deleted' && deleteResponse.status !== 'success') {
        return {
          status: 'error',
          message: `Failed to stop environment: ${deleteResponse.message}`
        };
      }

      // Wait a moment for cleanup
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Create new environment
      const createResponse = await this.createEnvironment(config);
      if (createResponse.status === 'created' || createResponse.status === 'existing') {
        return {
          status: 'success',
          message: 'Environment restarted successfully',
          environment: createResponse.environment
        };
      }

      return {
        status: 'error',
        message: `Failed to create new environment: ${createResponse.message}`
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async stopEnvironment(envId?: string): Promise<ApiResponse> {
    try {
      const result = await this.deleteEnvironment(envId);
      if (result.status === 'deleted') {
        return {
          status: 'success',
          message: 'Environment stopped successfully'
        };
      }
      return {
        status: 'error',
        message: result.message || 'Failed to stop environment'
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  async deleteEnvironment(envId?: string): Promise<ApiResponse> {
    try {
      const params = envId ? { env_id: envId } : {};
      const response = await this.api.delete('/environments', { params });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async sendHeartbeat(): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/environments/heartbeat');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Storage management
  async listUserStorages(): Promise<ApiResponse<StorageItem[]>> {
    try {
      const response = await this.api.get('/storage');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getStorageDetails(storageId: string): Promise<ApiResponse<StorageItem>> {
    try {
      const response = await this.api.get(`/storage/${storageId}`);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async createStorageBucket(storageClass: string = 'STANDARD', customName?: string): Promise<ApiResponse<StorageItem>> {
    try {
      const data: any = { storage_class: storageClass };
      if (customName) {
        data.custom_name = customName;
      }

      const response = await this.api.post('/storage', data);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async deleteStorage(storageId: string, force: boolean = false): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(`/storage/${storageId}`, {
        data: { operation: 'delete', force }
      });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // User environment variables
  async getUserEnvVars(): Promise<ApiResponse<Record<string, string>>> {
    try {
      const response = await this.api.get('/user-env-vars');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async setUserEnvVar(key: string, value: string): Promise<ApiResponse> {
    try {
      const response = await this.api.post('/user-env-vars', { key, value });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async deleteUserEnvVar(key: string): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(`/user-env-vars/${key}`);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // User file management
  async listUserFiles(): Promise<ApiResponse<UserFile[]>> {
    try {
      const response = await this.api.get('/files');
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async uploadUserFile(
    file: File, 
    fileType: string, 
    envVarName?: string, 
    containerPath?: string
  ): Promise<ApiResponse<UserFile>> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('file_type', fileType);
      
      if (envVarName) {
        formData.append('environment_variable_name', envVarName);
      }
      if (containerPath) {
        formData.append('container_path', containerPath);
      }

      const response = await this.api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async getUserFile(fileId: string): Promise<ApiResponse<UserFile>> {
    try {
      const response = await this.api.get(`/files/${fileId}`);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async updateUserFile(fileId: string, updates: Partial<UserFile>): Promise<ApiResponse<UserFile>> {
    try {
      const response = await this.api.put(`/files/${fileId}`, updates);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async deleteUserFile(fileId: string): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(`/files/${fileId}`);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async downloadUserFile(fileId: string): Promise<ApiResponse> {
    try {
      const response = await this.api.get(`/files/${fileId}/download`);
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Storage file operations
  async listStorageFiles(storageId: string, prefix?: string): Promise<any> {
    try {
      const params: any = {};
      if (prefix) params.prefix = prefix;
      const response = await this.api.get(`/storage/${storageId}/files`, { params });
      return response.data;
    } catch (error) {
      return this.handleError(error);
    }
  }

  async uploadFileToStorage(storageId: string, file: File, path?: string): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (path) {
        formData.append('path', path);
      }

      const response = await this.api.post(`/storage/${storageId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async downloadFileFromStorage(storageId: string, fileName: string): Promise<any> {
    try {
      const response = await this.api.get(`/storage/${storageId}/download/${fileName}`, {
        responseType: 'blob',
      });
      return response;
    } catch (error) {
      throw error;
    }
  }

  async deleteFileFromStorage(storageId: string, fileName: string): Promise<ApiResponse> {
    try {
      const response = await this.api.delete(`/storage/${storageId}/files`, {
        data: { file_path: fileName }
      });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Activity log
  async getActivityLog(limit: number = 50): Promise<ApiResponse> {
    try {
      const response = await this.api.get('/activity', { params: { limit } });
      return await this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }
}

// Global API client instance
export const apiClient = new CMBClusterAPIClient();
export default apiClient;
