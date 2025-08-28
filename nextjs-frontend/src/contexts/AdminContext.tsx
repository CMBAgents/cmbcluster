'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface AdminContextType {
  isAdmin: boolean;
  canSwitchToAdmin: boolean;
  currentRole: 'user' | 'admin';
  switchToAdmin: () => void;
  switchToUser: () => void;
  checkAdminStatus: () => Promise<boolean>;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export function AdminProvider({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const [currentRole, setCurrentRole] = useState<'user' | 'admin'>('user');
  const [isAdmin, setIsAdmin] = useState(false);

  // Check if user has admin role in their session
  const canSwitchToAdmin = session?.user?.role === 'admin';

  useEffect(() => {
    if (session?.user?.role === 'admin') {
      setIsAdmin(true);
    } else {
      setIsAdmin(false);
      setCurrentRole('user');
    }
  }, [session]);

  const switchToAdmin = () => {
    if (canSwitchToAdmin) {
      setCurrentRole('admin');
      // You could also make an API call here to validate admin access
    }
  };

  const switchToUser = () => {
    setCurrentRole('user');
  };

  const checkAdminStatus = async (): Promise<boolean> => {
    try {
      // For now, just check if user has admin role in session
      // This can be expanded to make an actual API verification call
      return canSwitchToAdmin;
    } catch (error) {
      return false;
    }
  };

  return (
    <AdminContext.Provider value={{
      isAdmin,
      canSwitchToAdmin,
      currentRole,
      switchToAdmin,
      switchToUser,
      checkAdminStatus,
    }}>
      {children}
    </AdminContext.Provider>
  );
}

export function useAdmin() {
  const context = useContext(AdminContext);
  if (context === undefined) {
    throw new Error('useAdmin must be used within an AdminProvider');
  }
  return context;
}
