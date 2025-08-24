'use client';

import MainLayout from '@/components/layout/MainLayout';
import EnvironmentManagement from '@/components/environments/EnvironmentManagement';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

// Force dynamic rendering
export const dynamic = 'force-dynamic';

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
