'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { notification, Button } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  InfoCircleOutlined, 
  WarningOutlined,
  CloseOutlined
} from '@ant-design/icons';

export interface NotificationItem {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

interface NotificationContextType {
  notifications: NotificationItem[];
  unreadCount: number;
  addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

const STORAGE_KEY = 'cmbcluster_notifications';

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Load notifications from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        const restored = parsed.map((n: any) => ({
          ...n,
          timestamp: new Date(n.timestamp)
        }));
        setNotifications(restored);
      }
    } catch (error) {
      console.warn('Failed to load saved notifications:', error);
    }
  }, []);

  // Save notifications to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } catch (error) {
      console.warn('Failed to save notifications:', error);
    }
  }, [notifications]);

  const unreadCount = notifications.filter(n => !n.read).length;

  const addNotification = (newNotification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => {
    const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const notificationItem: NotificationItem = {
      ...newNotification,
      id,
      timestamp: new Date(),
      read: false
    };

    setNotifications(prev => [notificationItem, ...prev]);

    // Show system notification
    const getIcon = () => {
      switch (newNotification.type) {
        case 'success':
          return <CheckCircleOutlined />;
        case 'error':
          return <ExclamationCircleOutlined />;
        case 'warning':
          return <WarningOutlined />;
        default:
          return <InfoCircleOutlined />;
      }
    };

    const actions = [
      ...(notificationItem.actions || []),
      {
        text: 'Mark as Read',
        onClick: () => markAsRead(id)
      }
    ];

    // Show Ant Design notification
    notification[newNotification.type]({
      message: newNotification.title,
      description: newNotification.message,
      placement: 'topRight',
      duration: newNotification.persistent ? 0 : 4.5, // Persistent notifications don't auto-dismiss
      icon: getIcon(),
      btn: newNotification.persistent ? (
        <Button size="small" onClick={() => markAsRead(id)}>
          <CloseOutlined /> Dismiss
        </Button>
      ) : undefined,
      onClose: () => {
        if (!newNotification.persistent) {
          markAsRead(id);
        }
      }
    });
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
    
    // Close the system notification
    notification.destroy();
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(n => ({ ...n, read: true }))
    );
    notification.destroy();
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
    notification.destroy();
  };

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

// Helper hook for common notification patterns
export function useCommonNotifications() {
  const { addNotification } = useNotifications();

  return {
    notifySuccess: (title: string, message: string, persistent = false) => 
      addNotification({ type: 'success', title, message, persistent }),
    
    notifyError: (title: string, message: string, persistent = true) => 
      addNotification({ type: 'error', title, message, persistent }),
    
    notifyWarning: (title: string, message: string, persistent = false) => 
      addNotification({ type: 'warning', title, message, persistent }),
    
    notifyInfo: (title: string, message: string, persistent = false) => 
      addNotification({ type: 'info', title, message, persistent }),

    notifyEnvironmentAction: (action: string, envId: string, success: boolean, message?: string) => {
      const title = `Environment ${action} ${success ? 'Successful' : 'Failed'}`;
      const description = message || `Environment ${envId.substring(0, 8)} ${action} ${success ? 'completed successfully' : 'encountered an error'}`;
      addNotification({
        type: success ? 'success' : 'error',
        title,
        message: description,
        persistent: !success // Errors stay until dismissed
      });
    }
  };
}
