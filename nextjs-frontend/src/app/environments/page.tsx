'use client';

import MainLayout from '@/components/layout/MainLayout';
import EnvironmentManagement from '@/components/environments/EnvironmentManagement';
import ProtectedRoute from '@/components/auth/ProtectedRoute';


function EnvironmentsContent() {
  return (
    <MainLayout>
      <EnvironmentManagement />
    </MainLayout>
  );
}

export default function EnvironmentsPage() {
  return (
    <ProtectedRoute>
      <EnvironmentsContent />
    </ProtectedRoute>
  );
}
