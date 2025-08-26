import { ReactNode } from 'react';

// Core application types
export interface User {
  sub: string;
  email: string;
  name: string;
  picture?: string;
}

export interface Environment {
  id: string;
  env_id: string;
  status: 'running' | 'pending' | 'failed' | 'stopped' | 'unknown';
  created_at: string;
  updated_at?: string;
  last_activity?: string;
  url?: string;
  pod_name?: string;
  namespace?: string;
  image?: string;
  port?: number;
  resource_config?: {
    cpu_limit: number;
    memory_limit: string;
    storage_size: string;
  };
}

export interface StorageItem {
  id: string;
  display_name: string;
  bucket_name: string;
  storage_class: 'standard' | 'nearline' | 'coldline';
  status: 'active' | 'inactive';
  created_at: string;
  updated_at?: string;
  size_bytes: number;
  region?: string;
  object_count?: number;
}

export interface UserFile {
  id: string;
  file_name: string;
  file_type: 'json' | 'gcp' | 'config';
  environment_variable_name?: string;
  container_path?: string;
  created_at: string;
  updated_at?: string;
  file_size: number;
}

export interface UserEnvVar {
  key: string;
  value: string;
}

export interface UserSettings {
  default_cpu: number;
  default_memory: number;
  default_storage_class: 'standard' | 'nearline' | 'coldline';
  auto_cleanup_hours: number;
  auto_save: boolean;
  enable_monitoring: boolean;
  email_notifications: boolean;
  auto_backup: boolean;
  last_updated?: string;
}

// API Response types
export interface ApiResponse<T = any> {
  status: 'success' | 'error' | 'created' | 'existing' | 'deleted';
  message?: string;
  data?: T;
  environments?: Environment[];
  storages?: StorageItem[];
  environment?: Environment;
  env_vars?: Record<string, string>;
}

// Environment creation config
export interface EnvironmentConfig {
  cpu_limit: number;
  memory_limit: string;
  storage_size: string;
  storage_id?: string;
  create_new_storage?: boolean;
  storage_class?: 'standard' | 'nearline' | 'coldline';
}

// Storage selection types
export interface StorageSelection {
  selection_type: 'existing' | 'create_new' | 'pending';
  storage_id?: string;
  storage_name?: string;
  storage_class?: 'standard' | 'nearline' | 'coldline';
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface EnvironmentFormData {
  preset: string;
  cpu_limit?: number;
  memory_limit?: string;
  storage_size?: string;
  storage_selection?: StorageSelection;
}

export interface EnvVarFormData {
  key: string;
  value: string;
}

export interface FileUploadFormData {
  file: File;
  file_type: 'json' | 'gcp' | 'config';
  environment_variable_name?: string;
  container_path?: string;
}

// Component prop types
export interface TabItem {
  key: string;
  label: string;
  children: ReactNode;
}

export interface StatusBadgeProps {
  status: Environment['status'];
  text?: string;
}

export interface EnvironmentCardProps {
  environment: Environment;
  onRestart?: (id: string) => void;
  onStop?: (id: string) => void;
  onRefresh?: (id: string) => void;
}

export interface StorageCardProps {
  storage: StorageItem;
  onRefresh?: (id: string) => void;
  onDelete?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Theme types
export interface ThemeColors {
  primary: string;
  background: {
    primary: string;
    secondary: string;
    tertiary: string;
  };
  text: {
    primary: string;
    secondary: string;
    muted: string;
  };
  success: string;
  warning: string;
  error: string;
  info: string;
}
